from fastapi import APIRouter
from app.services.discovery import discover_businesses
from app.services.normalization import normalize_businesses
from app.services.scoring import score_business
from app.services.enrichment_engine import enrich_in_background
from app.services.websocket_manager import manager
from app.database import SessionLocal, Business, Enrichment, Lead
import uuid
import asyncio

router = APIRouter()

def on_enrichment_complete(business_id, enrichment_data):
    db = SessionLocal()
    try:
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
                "lat": b.get("lat"),
                "lng": b.get("lng"),
                "score": score["score"],
                "opportunity": score["opportunity_level"],
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
