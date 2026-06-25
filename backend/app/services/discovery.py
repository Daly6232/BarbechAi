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
    out;
    """

    try:
        response = requests.post(
            OVERPASS_URL,
            data={"data": query},
            headers=HEADERS,
            timeout=60
        )

        if response.status_code != 200:
            return {
                "error": "OSM request failed",
                "status": response.status_code,
                "detail": response.text[:200]
            }

        data = response.json()

        results = []

        for el in data.get("elements", []):
            tags = el.get("tags", {})

            results.append({
                "name": tags.get("name"),
                "category": tags.get("amenity"),
                "lat": el.get("lat"),
                "lng": el.get("lon"),
                "source": "osm"
            })

        return results

    except Exception as e:
        return {"error": str(e)}
