from fastapi import APIRouter
from app.services.discovery import discover_businesses
from app.services.normalization import normalize_businesses
from app.services.scoring import score_business
from app.services.enrichment_engine import enrich_in_background
from app.database import SessionLocal, Business, Enrichment, Lead
import uuid

router = APIRouter()

def on_enrichment_complete(business_id, enrichment_data):
    db = SessionLocal()
    try:
        existing = db.query(Enrichment).filter(Enrichment.business_id == business_id).first()
        if existing:
            existing.website = enrichment_data.get("website") or existing.website
            existing.facebook = enrichment_data.get("facebook") or existing.facebook
            existing.instagram = enrichment_data.get("instagram") or existing.instagram
            existing.phone = enrichment_data.get("phone") or existing.phone
            existing.address = enrichment_data.get("address") or existing.address
        else:
            db_enrich = Enrichment(
                id=str(uuid.uuid4()),
                business_id=business_id,
                website=enrichment_data.get("website"),
                facebook=enrichment_data.get("facebook"),
                instagram=enrichment_data.get("instagram"),
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

@router.get("/discover")
def discover(city: str, business_type: str = "restaurant", session_id: str = "default"):
    raw = discover_businesses(city, business_type)

    if isinstance(raw, dict) and "error" in raw:
        return raw

    cleaned = normalize_businesses(raw)
    results = []
    db = SessionLocal()

    try:
        for b in cleaned:
            score = score_business(b)
            biz_id = str(uuid.uuid4())

            db_biz = Business(
                id=biz_id,
                name=b["name"],
                category=b["category"],
                city=city,
                address=b.get("address", ""),
                lat=b.get("lat"),
                lng=b.get("lng"),
                source=str(b.get("source", [])),
            )
            db.merge(db_biz)

            db_enrich = Enrichment(
                id=str(uuid.uuid4()),
                business_id=biz_id,
                website=b.get("website"),
                facebook=b.get("facebook"),
                instagram=b.get("instagram"),
            )
            db.add(db_enrich)

            db_lead = Lead(
                id=str(uuid.uuid4()),
                business_id=biz_id,
                score=score["score"],
                opportunity_level=score["opportunity_level"],
                status="ENRICHING",
            )
            db.add(db_lead)

            results.append({
                "id": biz_id,
                "name": b["name"],
                "category": b["category"],
                "city": city,
                "address": b.get("address", ""),
                "phone": b.get("phone", ""),
                "email": b.get("email", ""),
                "website": b.get("website", ""),
                "facebook": b.get("facebook", ""),
                "instagram": b.get("instagram", ""),
                "opening_hours": b.get("opening_hours", ""),
                "lat": b.get("lat"),
                "lng": b.get("lng"),
                "score": score["score"],
                "opportunity": score["opportunity_level"],
                "has_website": score["has_website"],
                "has_facebook": score["has_facebook"],
                "has_instagram": score["has_instagram"],
                "has_phone": score["has_phone"],
                "status": "ENRICHING",
            })

            enrich_in_background(
                biz_id,
                b["name"],
                city,
                b.get("lat"),
                b.get("lng"),
                on_enrichment_complete
            )

        db.commit()
    except Exception as e:
        db.rollback()
        return {"error": str(e)}
    finally:
        db.close()

    return {"count": len(results), "results": results}
