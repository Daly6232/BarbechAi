def normalize_businesses(businesses):
    seen = set()
    cleaned = []

    for b in businesses:
        if not b.get("name"):
            continue

        key = b["name"].strip().lower()

        if key in seen:
            continue

        seen.add(key)

        cleaned.append({
            "name": b["name"].strip(),
            "category": b.get("category", "unknown"),
            "city": b.get("city"),
            "address": b.get("address", ""),
            "lat": b.get("lat"),
            "lng": b.get("lng"),
            "source": b.get("source", []),
            "phone": b.get("phone", ""),
            "email": b.get("email", ""),
            "website": b.get("website", ""),
            "facebook": b.get("facebook", ""),
            "instagram": b.get("instagram", ""),
            "opening_hours": b.get("opening_hours", ""),
            "cuisine": b.get("cuisine", ""),
            "brand": b.get("brand", ""),
        })

    return cleaned
