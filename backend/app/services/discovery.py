import requests
from app.data.location_bbox import LOCATION_BBOX

OVERPASS_URL = "https://overpass-api.de/api/interpreter"
HEADERS = {
    "Content-Type": "application/x-www-form-urlencoded",
    "User-Agent": "BarbechAI/1.0"
}

def discover_businesses(city: str, business_type: str = "restaurant"):
    if city not in LOCATION_BBOX:
        return {
            "error": "Location not supported",
            "supported_locations": sorted(list(LOCATION_BBOX.keys()))
        }

    south, west, north, east = LOCATION_BBOX[city]

    query = f"""
    [out:json][timeout:25];
    node["amenity"="{business_type}"]({south},{west},{north},{east});
    out tags;
    """

    try:
        response = requests.post(
            OVERPASS_URL,
            data={"data": query},
            headers=HEADERS,
            timeout=60
        )

        if response.status_code != 200:
            return {"error": "OSM request failed", "status": response.status_code}

        data = response.json()
        results = []

        for el in data.get("elements", []):
            tags = el.get("tags", {})
            name = tags.get("name") or tags.get("name:ar") or tags.get("name:fr")
            if not name:
                continue

            results.append({
                "name": name,
                "category": tags.get("amenity", business_type),
                "lat": el.get("lat"),
                "lng": el.get("lon"),
                "source": ["osm"],
                # Address
                "address": " ".join(filter(None, [
                    tags.get("addr:housenumber", ""),
                    tags.get("addr:street", ""),
                    tags.get("addr:city", ""),
                ])),
                "postcode": tags.get("addr:postcode", ""),
                # Contact
                "phone": tags.get("phone") or tags.get("contact:phone") or tags.get("contact:mobile", ""),
                "email": tags.get("email") or tags.get("contact:email", ""),
                "website": tags.get("website") or tags.get("contact:website", ""),
                "facebook": tags.get("contact:facebook") or tags.get("facebook", ""),
                "instagram": tags.get("contact:instagram") or tags.get("instagram", ""),
                # Details
                "opening_hours": tags.get("opening_hours", ""),
                "cuisine": tags.get("cuisine", ""),
                "brand": tags.get("brand", ""),
            })

        return results

    except Exception as e:
        return {"error": str(e)}
