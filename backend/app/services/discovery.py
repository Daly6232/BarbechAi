import random
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

# ───────────────────────────────────────────────────────────────
# BUSINESS TYPE → OSM TAG MAPPING
# Frontend French labels → valid OpenStreetMap tag combinations
# ───────────────────────────────────────────────────────────────

BUSINESS_TYPE_OSM_MAP = {
    # ── Food & Drink ──
    "restaurant": [("amenity", "restaurant")],
    "café": [("amenity", "cafe")],
    "fast food": [("amenity", "fast_food")],
    "pâtisserie": [("shop", "pastry"), ("shop", "confectionery")],
    "boulangerie": [("shop", "bakery")],
    "boucherie": [("shop", "butcher")],
    "épicerie": [("shop", "convenience"), ("shop", "greengrocer")],
    "supermarché": [("shop", "supermarket"), ("shop", "mall")],

    # ── Hospitality ──
    "hotel": [("tourism", "hotel")],
    "maison d'hôtes": [("tourism", "guest_house")],
    "auberge": [("tourism", "hostel"), ("tourism", "guest_house")],
    "lounge": [("amenity", "cafe"), ("amenity", "bar"), ("amenity", "nightclub")],

    # ── Health & Medical ──
    "pharmacie": [("amenity", "pharmacy")],
    "parapharmacie": [("shop", "chemist"), ("shop", "medical_supply"), ("amenity", "pharmacy")],
    "clinique": [("amenity", "clinic"), ("amenity", "hospital")],
    "cabinet médical": [("amenity", "doctors"), ("amenity", "clinic")],
    "dentiste": [("amenity", "dentist")],
    "opticien": [("shop", "optician")],
    "laboratoire": [("amenity", "laboratory"), ("amenity", "clinic")],
    "vétérinaire": [("amenity", "veterinary")],

    # ── Sports & Fitness ──
    "gym": [("leisure", "fitness_centre"), ("amenity", "gym")],
    "salle de sport": [("leisure", "fitness_centre"), ("amenity", "gym")],
    "piscine": [("leisure", "swimming_pool"), ("amenity", "swimming_pool")],
    "club sportif": [("club", "sport"), ("leisure", "sports_centre")],

    # ── Beauty & Wellness ──
    "salon de coiffure": [("shop", "hairdresser")],
    "centre esthétique": [("shop", "beauty"), ("amenity", "beauty_salon")],
    "hammam": [("amenity", "hammam"), ("amenity", "public_bath")],
    "spa": [("leisure", "spa"), ("amenity", "spa"), ("shop", "beauty")],

    # ── Education ──
    "école": [("amenity", "school")],
    "lycée": [("amenity", "school")],
    "université": [("amenity", "university")],
    "centre de formation": [("amenity", "training"), ("amenity", "college")],
    "école de langue": [("amenity", "language_school")],
    "académie de musique": [("amenity", "music_school")],
    "académie de danse": [("amenity", "dance_school"), ("leisure", "dance")],
    "académie d'art": [("amenity", "arts_centre"), ("amenity", "art_school")],
    "crèche": [("amenity", "kindergarten"), ("amenity", "childcare")],
    "jardin d'enfants": [("amenity", "kindergarten"), ("amenity", "childcare")],

    # ── Finance & Legal ──
    "banque": [("amenity", "bank")],
    "assurance": [("office", "insurance"), ("amenity", "bank")],
    "agence immobilière": [("office", "estate_agent"), ("shop", "estate_agent")],
    "cabinet juridique": [("office", "lawyer"), ("office", "notary")],
    "cabinet comptable": [("office", "accountant"), ("office", "tax_advisor")],
    "notaire": [("office", "notary")],

    # ── Marketing & Tech ──
    "agence de marketing": [("office", "advertising_agency"), ("office", "marketing")],
    "agence de communication": [("office", "advertising_agency"), ("office", "marketing")],
    "société informatique": [("office", "it"), ("office", "company")],
    "espace coworking": [("amenity", "coworking_space"), ("office", "coworking")],

    # ── Automotive ──
    "auto école": [("amenity", "driving_school")],
    "garage": [("shop", "car_repair"), ("amenity", "garage")],
    "lavage auto": [("amenity", "car_wash")],
    "station service": [("amenity", "fuel")],

    # ── Travel & Events ──
    "agence de voyage": [("shop", "travel_agency"), ("office", "travel_agent")],
    "salle des fêtes": [("amenity", "events_venue"), ("amenity", "community_centre")],
    "studio photo": [("shop", "photo"), ("craft", "photographer")],

    # ── Printing & Books ──
    "imprimerie": [("shop", "printing"), ("shop", "copyshop")],
    "librairie": [("shop", "books")],
    "papeterie": [("shop", "stationery")],

    # ── Retail: Fashion & Accessories ──
    "bijouterie": [("shop", "jewelry")],
    "vêtements": [("shop", "clothes"), ("shop", "fashion")],
    "chaussures": [("shop", "shoes")],
    "maroquinerie": [("shop", "leather"), ("shop", "bag")],

    # ── Retail: Electronics & Home ──
    "électroménager": [("shop", "electronics"), ("shop", "appliance")],
    "informatique": [("shop", "computer"), ("shop", "electronics")],
    "téléphonie": [("shop", "mobile_phone"), ("shop", "electronics")],
    "meubles": [("shop", "furniture")],
    "décoration": [("shop", "interior_decoration"), ("shop", "gift")],
    "matériaux de construction": [("shop", "hardware"), ("shop", "building_materials")],
    "quincaillerie": [("shop", "hardware"), ("shop", "doityourself")],
    "droguerie": [("shop", "hardware"), ("shop", "chemist")],
    "fleuriste": [("shop", "florist"), ("shop", "garden_centre")],

    # ── Retail: Other ──
    "jouets": [("shop", "toys")],
    "articles de sport": [("shop", "sports")],
    "optique": [("shop", "optician")],

    # ── Industrial & Services ──
    "transport": [("office", "transport"), ("amenity", "bus_station")],
    "logistique": [("office", "logistics"), ("amenity", "warehouse")],
    "grossiste": [("shop", "wholesale"), ("office", "company")],
    "usine": [("landuse", "industrial"), ("man_made", "works")],
    "atelier": [("craft", "workshop"), ("shop", "craft")],
    "menuiserie": [("craft", "carpenter"), ("shop", "furniture")],
    "plomberie": [("craft", "plumber"), ("shop", "hardware")],
    "électricité": [("craft", "electrician"), ("shop", "electronics")],
    "climatisation": [("craft", "hvac"), ("shop", "appliance")],
    "peinture": [("craft", "painter"), ("shop", "paint")],

    # ── Religious & Cultural ──
    "mosquée": [("amenity", "place_of_worship"), ("religion", "muslim")],
    "église": [("amenity", "place_of_worship"), ("religion", "christian")],
    "association": [("amenity", "community_centre"), ("office", "association")],
    "cinéma": [("amenity", "cinema")],
    "théâtre": [("amenity", "theatre")],
    "musée": [("tourism", "museum")],
    "bibliothèque": [("amenity", "library")],

    # ── Shopping ──
    "centre commercial": [("shop", "mall"), ("amenity", "marketplace")],
    "marché": [("amenity", "marketplace"), ("amenity", "market")],
}


def _build_overpass_query(business_type: str, south: float, west: float, north: float, east: float) -> str:
    """
    Build an Overpass QL query from mapped OSM tags.
    Supports multiple tag combinations per business type (OR logic).
    """
    tags = BUSINESS_TYPE_OSM_MAP.get(business_type)

    if not tags:
        # Fallback: try as raw amenity value
        tags = [("amenity", business_type)]

    # Build union of all tag combinations
    node_queries = []
    for key, value in tags:
        node_queries.append(f'node["{key}"="{value}"]({south},{west},{north},{east});')

    union_body = "\n    ".join(node_queries)

    query = f"""
[out:json][timeout:25];
(
    {union_body}
);
out tags 500;
"""
    return query


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
    business_type_lower = business_type.lower().strip()

    query = _build_overpass_query(business_type_lower, south, west, north, east)

    try:
        logger.info("Searching '%s' in %s", business_type_lower, city)

        response = requests.post(
            OVERPASS_URL,
            data={"data": query},
            headers=HEADERS,
            timeout=25,
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

            # Detect actual OSM category from tags
            detected_category = (
                tags.get("amenity")
                or tags.get("shop")
                or tags.get("tourism")
                or tags.get("leisure")
                or tags.get("office")
                or tags.get("craft")
                or tags.get("club")
                or business_type_lower
            )

            results.append({
                "name": name,
                "category": detected_category,
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

        logger.info("Found %d businesses for '%s' in %s", len(results), business_type_lower, city)
        return results

    except Exception as e:
        logger.exception("Discovery failed for '%s' in %s", business_type_lower, city)
        return {"error": str(e)}
