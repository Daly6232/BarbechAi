import math

def normalize_businesses(businesses):
    seen = set()
    cleaned = []

    for b in businesses:
        if not b.get("name"):
            continue

        key = b["name"].strip().lower()

        # basic deduplication by name
        if key in seen:
            continue

        seen.add(key)

        cleaned.append({
            "name": b["name"].strip(),
            "category": b.get("category", "unknown"),
            "city": b.get("city"),
            "address": b.get("address"),
            "lat": b.get("lat"),
            "lng": b.get("lng"),
            "source": b.get("source", [])
        })

    return cleaned
