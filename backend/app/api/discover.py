from fastapi import APIRouter
from app.services.discovery import discover_businesses
from app.services.normalization import normalize_businesses
from app.services.scoring import score_business
from app.database import SessionLocal, Business, Lead
import uuid

router = APIRouter()

@router.get("/discover")
def discover(city: str, business_type: str = "restaurant"):
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
                status="NEW",
            )
            db.add(db_lead)

            results.append({
                "name": b["name"],
                "category": b["category"],
                "city": city,
                "score": score["score"],
                "opportunity": score["opportunity_level"],
            })

        db.commit()
    except Exception as e:
        db.rollback()
        return {"error": str(e)}
    finally:
        db.close()

    return {"count": len(results), "results": results}
