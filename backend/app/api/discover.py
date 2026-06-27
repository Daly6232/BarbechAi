import random
import uuid
import threading

from fastapi import APIRouter

from app.services.discovery import discover_businesses
from app.services.normalization import normalize_businesses
from app.services.scoring import score_business
from app.services.enrichment_engine import enrich_in_background
from app.services.multi_source import discover_multi_source
from app.services.reconciliation import reconcile
from app.services.websocket_manager import manager
from app.database import SessionLocal, Business, Enrichment, Lead

router = APIRouter()

MAX_RESULTS = 100


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
            lead.status = "ENRICHED"
        db.commit()
    except Exception as e:
        db.rollback()
    finally:
        db.close()


def _get_saved_business_names(db, city: str, category: str) -> set:
    """Return case-insensitive set of business names already saved for this city + category."""
    try:
        existing = db.query(Business.name).filter(
            Business.city == city,
            Business.category == category,
        ).all()
        return {name[0].strip().casefold() for name in existing if name[0]}
    except Exception:
        return set()


def _write_business_to_db(db, biz: dict, city: str, status: str = "NEW") -> dict:
    """Write a single business + enrichment + lead to DB. Returns the API-safe dict."""
    biz_id = str(uuid.uuid4())

    db_biz = Business(
        id=biz_id,
        name=biz["name"],
        category=biz.get("category", ""),
        city=city,
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
    )
    db.add(db_lead)

    return {
        "id": biz_id,
        "name": biz["name"],
        "category": biz.get("category", ""),
        "city": city,
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
        "status": status,
        "source": biz.get("source", []),
        "sources_used": biz.get("sources_used", [biz.get("source", "osm")]),
        "confidence": biz.get("confidence", 100),
        "has_conflicts": biz.get("has_conflicts", False),
        "conflict_fields": biz.get("conflict_fields", []),
        "is_new_discovery": biz.get("is_new_discovery", False),
    }


def _run_phase_two(city: str, business_type: str, osm_results: list, session_id: str):
    """
    Background: Run multi-source discovery, reconciliation, DB writes, and WebSocket pushes.
    """
    import asyncio

    db = SessionLocal()
    try:
        # 1. Multi-source search
        ms_result = discover_multi_source(city, business_type, osm_results)
        all_external = ms_result.get("all_results", [])

        if not all_external:
            return

        # 2. Reconcile with OSM results
        recon = reconcile(osm_results, all_external)
        merged = recon.get("merged", [])
        new_discoveries = recon.get("new_discoveries", [])

        # 3. Process merged (existing OSM + enriched data)
        for biz in merged:
            if biz.get("has_conflicts"):
                # Push conflict alert via WebSocket
                try:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    loop.run_until_complete(
                        manager.send_update(session_id, {
                            "type": "conflict_detected",
                            "business_id": biz.get("id", ""),
                            "business_name": biz.get("name", ""),
                            "conflict_fields": biz.get("conflict_fields", []),
                        })
                    )
                    loop.close()
                except Exception:
                    pass

            # Push confidence update
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(
                    manager.send_update(session_id, {
                        "type": "confidence_update",
                        "business_id": biz.get("id", ""),
                        "business_name": biz.get("name", ""),
                        "confidence": biz.get("confidence", 100),
                        "sources_used": biz.get("sources_used", []),
                    })
                )
                loop.close()
            except Exception:
                pass

        # 4. Write new discoveries to DB and push to frontend
        for biz in new_discoveries:
            biz_result = _write_business_to_db(db, biz, city, status="NEW")
            db.commit()

            # Push new discovery via WebSocket
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(
                    manager.send_update(session_id, {
                        "type": "new_discovery",
                        "business": biz_result,
                    })
                )
                loop.close()
            except Exception:
                pass

            # Start enrichment for new business
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


# Need logger for the background thread
from app.core.logging import get_logger
logger = get_logger(__name__)


@router.get("/discover")
def discover(city: str, business_type: str = "restaurant", session_id: str = "default"):
    # ── Phase 1: OSM Overpass (fast, synchronous) ──
    raw = discover_businesses(city, business_type)

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

        # Write to DB and build response
        for b in selected:
            b["sources_used"] = ["osm"]
            b["confidence"] = 100
            b["has_conflicts"] = False
            b["conflict_fields"] = []
            b["is_new_discovery"] = False
            result = _write_business_to_db(db, b, city, status="NEW")
            results.append(result)

        db.commit()

        # ── Phase 2: Multi-source discovery (background) ──
        osm_for_recon = [
            {
                "name": b["name"],
                "category": b.get("category", business_type),
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

        thread = threading.Thread(
            target=_run_phase_two,
            args=(city, business_type, osm_for_recon, session_id),
            daemon=True,
        )
        thread.start()

        # ── Phase 3: Enrichment for OSM results (background) ──
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
