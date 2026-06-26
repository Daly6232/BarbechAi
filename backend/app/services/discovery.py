import requests

from app.core.config import settings
from app.core.constants import DEFAULT_BUSINESS_TYPE
from app.core.logging import get_logger
from app.data.location_bbox import LOCATION_BBOX

logger = get_logger(__name__)

OVERPASS_URL = "https://overpass-api.de/api/interpreter"

HEADERS = {
    "Content-Type": "application/x-www-form-urlencoded",
    "User-Agent": settings.USER_AGENT,
}


def discover_businesses(
    city: str,
    business_type: str = DEFAULT_BUSINESS_TYPE,
):
    if city not in LOCATION_BBOX:
        logger.warning("Unsupported location: %s", city)
        return {
            "error": "Location not supported",
            "supported_locations": sorted(LOCATION_BBOX.keys()),
        }

    south, west, north, east = LOCATION_BBOX[city]

    query = f"""
    [out:json][timeout:25];
    node["amenity"="{business_type}"]({south},{west},{north},{east});
    out tags;
    """

    try:
        logger.info("Searching %s in %s", business_type, city)

        response = requests.post(
            OVERPASS_URL,
            data={"data": query},
            headers=HEADERS,
            timeout=settings.REQUEST_TIMEOUT,
        )

        if response.status_code != 200:
            logger.error("OSM returned %s", response.status_code)
            return {
                "error": "OSM request failed",
                "status": response.status_code,
            }

        data = response.json()
        results = []

        for el in data.get("elements", []):
            tags = el.get("tags", {})

            name = (
                tags.get("name")
                or tags.get("name:ar")
                or tags.get("name:fr")
            )

            if not name:
                continue

            results.append({
                "name": name,
                "category": tags.get("amenity", business_type),
                "lat": el.get("lat"),
                "lng": el.get("lon"),
                "source": ["osm"],
                "address": " ".join(filter(None, [
                    tags.get("addr:housenumber", ""),
                    tags.get("addr:street", ""),
                    tags.get("addr:city", ""),
                ])),
                "postcode": tags.get("addr:postcode", ""),
                "phone": (
                    tags.get("phone")
                    or tags.get("contact:phone")
                    or tags.get("contact:mobile", "")
                ),
                "email": (
                    tags.get("email")
                    or tags.get("contact:email", "")
                ),
                "website": (
                    tags.get("website")
                    or tags.get("contact:website", "")
                ),
                "facebook": (
                    tags.get("facebook")
                    or tags.get("contact:facebook", "")
                ),
                "instagram": (
                    tags.get("instagram")
                    or tags.get("contact:instagram", "")
                ),
                "opening_hours": tags.get("opening_hours", ""),
                "cuisine": tags.get("cuisine", ""),
                "brand": tags.get("brand", ""),
            })

        logger.info("Found %d businesses", len(results))
        return results

    except Exception as e:
        logger.exception("Discovery failed")
        return {"error": str(e)}
