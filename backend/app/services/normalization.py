from typing import Dict, List


DEFAULT_CATEGORY = "unknown"


def normalize_businesses(businesses: List[Dict]) -> List[Dict]:
    seen = set()
    cleaned = []

    for business in businesses:
        name = (business.get("name") or "").strip()

        if not name:
            continue

        key = name.casefold()

        if key in seen:
            continue

        seen.add(key)

        cleaned.append(
            {
                "name": name,
                "category": business.get("category", DEFAULT_CATEGORY),
                "city": business.get("city"),
                "address": business.get("address", "").strip(),
                "lat": business.get("lat"),
                "lng": business.get("lng"),
                "source": business.get("source", []),
                "phone": business.get("phone", "").strip(),
                "email": business.get("email", "").strip(),
                "website": business.get("website", "").strip(),
                "facebook": business.get("facebook", "").strip(),
                "instagram": business.get("instagram", "").strip(),
                "opening_hours": business.get("opening_hours", "").strip(),
                "cuisine": business.get("cuisine", "").strip(),
                "brand": business.get("brand", "").strip(),
            }
        )

    return cleaned
