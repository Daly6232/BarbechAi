from fastapi import APIRouter

from app.services.discovery import discover_businesses
from app.services.normalization import normalize_businesses
from app.services.real_enrichment import enrich_business_real
from app.services.scoring import score_business

router = APIRouter()

@router.get("/discover")
def discover(city: str, business_type: str = "restaurant"):
    raw = discover_businesses(city, business_type)

    if isinstance(raw, dict) and "error" in raw:
        return raw

    cleaned = normalize_businesses(raw)
    results = []

    for b in cleaned:
        b["enrichment"] = enrich_business_real(b["name"], city)
        b["score"] = score_business(b)

        results.append({
            "name": b["name"],
            "category": b["category"],
            "city": city,
            "score": b["score"]["score"],
            "opportunity": b["score"]["opportunity_level"]
        })

    return {
        "count": len(results),
        "results": results
    }
