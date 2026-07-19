import random
import uuid
import asyncio

from fastapi import APIRouter, BackgroundTasks

from app.services.discovery import discover_businesses
from app.services.normalization import normalize_businesses
from app.services.scoring import score_business
from app.services.enrichment_engine import enrich_in_background
from app.services.multi_source import discover_multi_source
from app.services.reconciliation import reconcile
from app.services.websocket_manager import manager
from app.database import SessionLocal, Business, Enrichment, Lead
from app.core.logging import get_logger
from app.data.location_bbox import LOCATION_BBOX

logger = get_logger(__name__)
router = APIRouter()
MAX_RESULTS = 100

# How far outside a searched city's bounding box (in degrees, ~0.5 ≈ 50km) a
# result's real coordinates may fall before we treat it as an unrelated
# false match rather than a legitimate result near a delegation boundary.
AREA_BUFFER_DEG = 0.5


def _resolve_real_city(lat, lng, fallback_city: str) -> str:
    """Determine the actual locality a business sits in from its real
    coordinates, instead of trusting the search-seed city blindly.
    Multi-source APIs (Foursquare/TomTom/Geoapify/etc.) don't always
    respect their location bias, so a result can land far from the city
    that was searched — this makes the stored `city` field reflect
    reality instead of the search parameter."""
    if lat is None or lng is None:
        return fallback_city
    try:
        lat_f, lng_f = float(lat), float(lng)
    except (TypeError, ValueError):
        return fallback_city
    for name, (south, west, north, east) in LOCATION_BBOX.items():
        if south <= lat_f <= north and west <= lng_f <= east:
            return name
    return fallback_city


def _within_search_area(lat, lng, city: str, buffer_deg: float = AREA_BUFFER_DEG) -> bool:
    """Reject discoveries whose coordinates fall nowhere near the city that
    was actually searched. A generous buffer tolerates legitimate results
    near a delegation boundary while still catching results that are
    wildly out of area — a different governorate, or an unrelated match
    from another country entirely."""
    if lat is None or lng is None:
        return True  # can't disprove it without coordinates — don't block
    bbox = LOCATION_BBOX.get(city)
    if not bbox:
        return True  # unknown city key, nothing to validate against
    try:
        lat_f, lng_f = float(lat), float(lng)
    except (TypeError, ValueError):
        return True
    south, west, north, east = bbox
    return (
        (south - buffer_deg) <= lat_f <= (north + buffer_deg)
        and (west - buffer_deg) <= lng_f <= (east + buffer_deg)
    )


def on_enrichment_complete(business_id, enrichment_data):
    db = SessionLocal()
    try:
        existing = db.query(Enrichment).filter(Enrichment.business_id == business_id).first()
        if existing:
            existing.website = enrichment_data.get("website") or existing.website
            existing.facebook = enrichment_data.get("facebook") or existing.facebook
            existing.instagram = enrichment_data.get("instagram") or existing.instagram
            existing.phone = enrichment_data.get("phone") or existing.phone
            existing.email = enrichment_data.get("email") or existing.email
            existing.address = enrichment_data.get("address") or existing.address
            existing.opening_hours = enrichment_data.get("opening_hours") or existing.opening_hours
        else:
            db_enrich = Enrichment(
                id=str(uuid.uuid4()),
                business_id=business_id,
                website=enrichment_data.get("website"),
                facebook=enrichment_data.get("facebook"),
                instagram=enrichment_data.get("instagram"),
                phone=enrichment_data.get("phone"),
                email=enrichment_data.get("email"),
                address=enrichment_data.get("address"),
                opening_hours=enrichment_data.get("opening_hours"),
            )
            db.add(db_enrich)
        lead = db.query(Lead).filter(Lead.business_id == business_id).first()
        if lead:
            lead.status = enrichment_data.get("status", "ENRICHED_PARTIAL")
        db.commit()
    except Exception as e:
        db.rollback()
    finally:
        db.close()


def _get_saved_business_names(db, city: str, category: str) -> set:
    try:
        existing = db.query(Business.name).filter(
            Business.city == city,
            Business.category == category,
        ).all()
        return {name[0].strip().casefold() for name in existing if name[0]}
    except Exception:
        return set()


def _write_business_to_db(db, biz: dict, city: str, business_type: str, status: str = "NEW") -> dict:
    biz_id = str(uuid.uuid4())
    category = business_type
    real_city = _resolve_real_city(biz.get("lat"), biz.get("lng"), city)

    db_biz = Business(
        id=biz_id,
        name=biz["name"],
        category=category,
        city=real_city,
        address=biz.get("address", ""),
        lat=biz.get("lat"),
        lng=biz.get("lng"),
        source=str(biz.get("sources_used", biz.get("source", []))),
    )
    db.add(db_biz)

    db_enrich = Enrichment(
        id=str(uuid.uuid4()),
        business_id=biz_id,
        website=biz.get("website"),
        facebook=biz.get("facebook"),
        instagram=biz.get("instagram"),
        phone=biz.get("phone"),
        email=biz.get("email"),
        address=biz.get("address"),
        opening_hours=biz.get("opening_hours"),
    )
    db.add(db_enrich)

    score_data = score_business(biz)
    db_lead = Lead(
        id=str(uuid.uuid4()),
        business_id=biz_id,
        score=score_data["score"],
        opportunity_level=score_data["opportunity_level"],
        status=status,
        service_opportunities=",".join(score_data.get("service_opportunities", [])),
    )
    db.add(db_lead)

    return {
        "id": biz_id,
        "name": biz["name"],
        "category": category,
        "city": real_city,
        "address": biz.get("address", ""),
        "phone": biz.get("phone", ""),
        "email": biz.get("email", ""),
        "website": biz.get("website", ""),
        "facebook": biz.get("facebook", ""),
        "instagram": biz.get("instagram", ""),
        "opening_hours": biz.get("opening_hours", ""),
        "lat": biz.get("lat"),
        "lng": biz.get("lng"),
        "score": score_data["score"],
        "opportunity": score_data["opportunity_level"],
        "has_website": score_data["has_website"],
        "has_facebook": score_data["has_facebook"],
        "has_instagram": score_data["has_instagram"],
        "has_phone": score_data["has_phone"],
        "has_email": score_data["has_email"],
        "has_address": score_data["has_address"],
        "service_opportunities": score_data.get("service_opportunities", []),
        "status": status,
        "source": biz.get("source", []),
        "sources_used": biz.get("sources_used", ["osm"]),
        "confidence": biz.get("confidence", 100),
        "has_conflicts": biz.get("has_conflicts", False),
        "conflict_fields": biz.get("conflict_fields", []),
        "is_new_discovery": biz.get("is_new_discovery", False),
    }


async def _run_phase_two(city: str, business_type: str, osm_results: list, session_id: str):
    db = SessionLocal()
    try:
        # Offload heavy synchronous queries to the background thread pool
        ms_result = await asyncio.to_thread(discover_multi_source, city, business_type, osm_results)
        all_external = ms_result.get("all_results", [])

        if not all_external:
            return

        recon = await asyncio.to_thread(reconcile, osm_results, all_external)
        merged = recon.get("merged", [])
        new_discoveries = recon.get("new_discoveries", [])

        for biz in merged:
            if biz.get("has_conflicts"):
                # Smooth, native websocket push directly on FastAPI's active loop
                await manager.send_update(session_id, {
                    "type": "conflict_detected",
                    "business_id": biz.get("id", ""),
                    "business_name": biz.get("name", ""),
                    "conflict_fields": biz.get("conflict_fields", []),
                })

            await manager.send_update(session_id, {
                "type": "confidence_update",
                "business_id": biz.get("id", ""),
                "business_name": biz.get("name", ""),
                "confidence": biz.get("confidence", 100),
                "sources_used": biz.get("sources_used", []),
            })

        for biz in new_discoveries:
            if not _within_search_area(biz.get("lat"), biz.get("lng"), city):
                logger.warning(
                    "Discarding out-of-area discovery '%s' (lat=%s, lng=%s) while "
                    "searching '%s' — likely an unrelated match from another location.",
                    biz.get("name"), biz.get("lat"), biz.get("lng"), city,
                )
                continue

            # Safely perform database insertion off-thread
            biz_result = await asyncio.to_thread(_write_business_to_db, db, biz, city, business_type, "NEW")
            db.commit()

            await manager.send_update(session_id, {
                "type": "new_discovery",
                "business": biz_result,
            })

            enrich_in_background(
                biz_result["id"],
                biz["name"],
                city,
                biz.get("lat"),
                biz.get("lng"),
                on_enrichment_complete,
                session_id=session_id,
            )

    except Exception as e:
        db.rollback()
        logger.exception("Phase 2 failed: %s", str(e))
    finally:
        db.close()


@router.get("/discover")
async def discover(city: str, business_type: str = "restaurant", session_id: str = "default", background_tasks: BackgroundTasks = None):
    # Properly awaiting the updated async discovery engine
    raw = await discover_businesses(city, business_type)

    if isinstance(raw, dict) and "error" in raw:
        return raw

    cleaned = normalize_businesses(raw)
    results = []
    db = SessionLocal()

    try:
        saved_names = _get_saved_business_names(db, city, business_type)

        scored_businesses = []
        for b in cleaned:
            name_key = b["name"].strip().casefold()
            if name_key in saved_names:
                continue
            scored_businesses.append(b)

        random.shuffle(scored_businesses)
        selected = scored_businesses[:MAX_RESULTS]

        for b in selected:
            b["sources_used"] = ["osm"]
            b["confidence"] = 100
            b["has_conflicts"] = False
            b["conflict_fields"] = []
            b["is_new_discovery"] = False
            result = _write_business_to_db(db, b, city, business_type, status="NEW")
            results.append(result)

        db.commit()

        # Phase 2: Multi-source (background)
        osm_for_recon = [
            {
                "name": b["name"],
                "category": business_type,
                "lat": b.get("lat"),
                "lng": b.get("lng"),
                "address": b.get("address", ""),
                "phone": b.get("phone", ""),
                "website": b.get("website", ""),
                "email": b.get("email", ""),
                "facebook": b.get("facebook", ""),
                "instagram": b.get("instagram", ""),
                "opening_hours": b.get("opening_hours", ""),
            }
            for b in selected
        ]

        # Use FastAPI's managed task execution pool instead of standard unmanaged threads
        if background_tasks:
            background_tasks.add_task(
                _run_phase_two, city, business_type, osm_for_recon, session_id
            )
        else:
            # Fallback wrapper if endpoint context fails to receive background tasks
            asyncio.create_task(_run_phase_two(city, business_type, osm_for_recon, session_id))

        # Phase 3: Enrichment (background)
        for i, b in enumerate(selected):
            enrich_in_background(
                results[i]["id"],
                b["name"],
                city,
                b.get("lat"),
                b.get("lng"),
                on_enrichment_complete,
                session_id=session_id,
            )

    except Exception as e:
        db.rollback()
        return {"error": str(e)}
    finally:
        db.close()

    return {
        "count": len(results),
        "results": results,
        "total_found": len(scored_businesses),
        "excluded_saved": len(cleaned) - len(scored_businesses),
        "returned": len(results),
    }


PENDING_STATUSES = ["NEW", "ENRICHMENT_FAILED"]


@router.get("/leads/pending-count")
def pending_count():
    db = SessionLocal()
    try:
        count = db.query(Lead).filter(Lead.status.in_(PENDING_STATUSES)).count()
        return {"pending": count}
    finally:
        db.close()


@router.post("/leads/enrich-pending")
def enrich_pending(batch_size: int = 10, session_id: str = "default"):
    db = SessionLocal()
    try:
        pending = (
            db.query(Lead, Business)
            .join(Business, Lead.business_id == Business.id)
            .filter(Lead.status.in_(PENDING_STATUSES))
            .limit(batch_size)
            .all()
        )
        queued_ids = []
        for lead, biz in pending:
            lead.status = "ENRICHING"
            queued_ids.append(biz.id)
        db.commit()

        for lead, biz in pending:
            enrich_in_background(
                biz.id, biz.name, biz.city, biz.lat, biz.lng,
                on_enrichment_complete,
                session_id=session_id,
            )

        remaining = db.query(Lead).filter(Lead.status.in_(PENDING_STATUSES)).count()
        return {"queued": len(queued_ids), "remaining": remaining}
    except Exception as e:
        db.rollback()
        return {"error": str(e)}
    finally:
        db.close()
