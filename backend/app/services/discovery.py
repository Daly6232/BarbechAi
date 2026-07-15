import httpx
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

BUSINESS_TYPE_OSM_MAP = {
    # ── Restauration & Alimentation ──
    "restaurant": [("amenity", "restaurant")],
    "café": [("amenity", "cafe")],
    "lounge": [("amenity", "bar"), ("amenity", "cafe")],
    "fast-food": [("amenity", "fast_food")],
    "pizzeria": [("amenity", "fast_food"), ("amenity", "restaurant")],
    "sandwicherie": [("amenity", "fast_food")],
    "snack": [("amenity", "fast_food"), ("amenity", "snack_bar")],
    "pâtisserie": [("shop", "pastry"), ("shop", "confectionery")],
    "boulangerie": [("shop", "bakery")],
    "boucherie": [("shop", "butcher")],
    "épicerie": [("shop", "convenience"), ("shop", "greengrocer")],
    "supermarché": [("shop", "supermarket")],
    "traiteur": [("shop", "deli"), ("amenity", "restaurant")],

    # ── Hôtellerie & Tourisme ──
    "hôtel": [("tourism", "hotel")],
    "maison d'hôtes": [("tourism", "guest_house")],
    "auberge": [("tourism", "hostel"), ("tourism", "guest_house")],
    "résidence touristique": [("tourism", "apartment"), ("tourism", "hotel")],
    "agence de voyage": [("shop", "travel_agency"), ("office", "travel_agent")],

    # ── Santé & Médical ──
    "pharmacie": [("amenity", "pharmacy")],
    "parapharmacie": [("shop", "chemist"), ("shop", "cosmetics")],
    "clinique": [("amenity", "clinic"), ("amenity", "hospital")],
    "cabinet médical": [("amenity", "doctors")],
    "dentiste": [("amenity", "dentist")],
    "opticien": [("shop", "optician")],
    "laboratoire d'analyses": [("amenity", "clinic"), ("healthcare", "laboratory")],
    "vétérinaire": [("amenity", "veterinary")],
    "cabinet de kinésithérapie": [("healthcare", "physiotherapist"), ("amenity", "doctors")],
    "radiologie": [("healthcare", "radiologist"), ("amenity", "clinic")],

    # ── Sport & Bien-être ──
    "salle de sport": [("leisure", "fitness_centre"), ("leisure", "sports_centre")],
    "piscine": [("leisure", "swimming_pool")],
    "club sportif": [("leisure", "sports_centre"), ("club", "sport")],
    "centre de fitness": [("leisure", "fitness_centre")],

    # ── Beauté & Soins ──
    "salon de coiffure": [("shop", "hairdresser")],
    "institut de beauté": [("shop", "beauty")],
    "hammam": [("amenity", "hammam"), ("amenity", "public_bath")],
    "spa": [("leisure", "spa")],
    "centre d'esthétique": [("shop", "beauty"), ("amenity", "beauty_salon")],
    "onglerie": [("shop", "beauty")],

    # ── Formation & Éducation ──
    "centre de formation": [("amenity", "college"), ("amenity", "training")],
    "école de langue": [("amenity", "language_school")],
    "auto-école": [("amenity", "driving_school")],
    "académie de musique": [("amenity", "music_school")],
    "académie de danse": [("leisure", "dance"), ("amenity", "dance_school")],
    "crèche": [("amenity", "kindergarten"), ("amenity", "childcare")],

    # ── Finance & Juridique ──
    "banque": [("amenity", "bank")],
    "assurance": [("office", "insurance")],
    "agence immobilière": [("office", "estate_agent"), ("shop", "estate_agent")],
    "cabinet juridique": [("office", "lawyer")],
    "cabinet comptable": [("office", "accountant"), ("office", "tax_advisor")],
    "bureau de change": [("amenity", "bureau_de_change")],
    "notaire": [("office", "notary")],

    # ── Marketing & Tech ──
    "agence de communication": [("office", "advertising_agency")],
    "agence digitale": [("office", "it"), ("office", "advertising_agency")],
    "société informatique": [("office", "it"), ("office", "company")],
    "espace coworking": [("amenity", "coworking_space")],

    # ── Automobile ──
    "garage": [("shop", "car_repair")],
    "lavage auto": [("amenity", "car_wash")],
    "station-service": [("amenity", "fuel")],
    "vente de pièces auto": [("shop", "car_parts")],
    "concessionnaire": [("shop", "car")],

    # ── Événementiel & Arts ──
    "salle des fêtes": [("amenity", "events_venue"), ("amenity", "community_centre")],
    "studio photo": [("shop", "photo"), ("craft", "photographer")],
    "imprimerie": [("shop", "printing"), ("shop", "copyshop")],
    "librairie": [("shop", "books")],
    "papeterie": [("shop", "stationery")],

    # ── Mode & Accessoires ──
    "bijouterie": [("shop", "jewelry")],
    "vêtements": [("shop", "clothes")],
    "chaussures": [("shop", "shoes")],
    "maroquinerie": [("shop", "leather")],
    "lingerie": [("shop", "underwear"), ("shop", "clothes")],
    "articles de sport": [("shop", "sports")],

    # ── Électronique & Maison ──
    "électroménager": [("shop", "appliance"), ("shop", "electronics")],
    "informatique": [("shop", "computer")],
    "téléphonie": [("shop", "mobile_phone")],
    "meubles": [("shop", "furniture")],
    "décoration": [("shop", "interior_decoration")],
    "matériaux de construction": [("shop", "building_materials"), ("shop", "hardware")],
    "quincaillerie": [("shop", "hardware"), ("shop", "doityourself")],
    "droguerie": [("shop", "chemist"), ("shop", "hardware")],
    "fleuriste": [("shop", "florist")],

    # ── Services aux entreprises ──
    "transport": [("office", "transport")],
    "logistique": [("office", "logistics")],
    "grossiste": [("shop", "wholesale")],
    "bureau d'études": [("office", "consulting"), ("office", "engineer")],
    "cabinet d'architecture": [("office", "architect")],

    # ── Artisanat & BTP ──
    "menuiserie": [("craft", "carpenter")],
    "plomberie": [("craft", "plumber")],
    "électricité": [("craft", "electrician")],
    "climatisation": [("craft", "hvac")],
    "peinture": [("craft", "painter")],
    "carrelage": [("craft", "tiler")],
    "ferronnerie": [("craft", "blacksmith")],
}


def _build_overpass_query(business_type: str, south: float, west: float, north: float, east: float) -> str:
    tags = BUSINESS_TYPE_OSM_MAP.get(business_type)
    if not tags:
        tags = [("amenity", business_type)]

    nwr_queries = []
    for key, value in tags:
        nwr_queries.append(f'nwr["{key}"="{value}"]({south},{west},{north},{east});')

    union_body = "\n    ".join(nwr_queries)
    query = f"""
[out:json][timeout:25];
(
    {union_body}
);
out center 500;
"""
    return query


async def discover_businesses(city: str, business_type: str = DEFAULT_BUSINESS_TYPE):
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
        logger.info("Searching '%s' in %s (Async-Overpass)", business_type_lower, city)
        async with httpx.AsyncClient() as client:
            response = await client.post(
                OVERPASS_URL,
                data={"data": query},
                headers=HEADERS,
                timeout=30.0,
            )

        if response.status_code != 200:
            logger.error("OSM returned HTTP %s", response.status_code)
            return {"error": "OSM request failed", "status": response.status_code}

        data = response.json()
        results = []

        for el in data.get("elements", []):
            tags = el.get("tags", {})
            name = (
                tags.get("name")
                or tags.get("name:fr")
                or tags.get("name:ar")
                or tags.get("brand")
                or tags.get("operator")
            )
            if not name:
                continue

            detected_category = (
                tags.get("amenity")
                or tags.get("shop")
                or tags.get("tourism")
                or tags.get("leisure")
                or tags.get("office")
                or tags.get("craft")
                or tags.get("healthcare")
                or business_type_lower
            )

            lat = el.get("lat") or el.get("center", {}).get("lat")
            lng = el.get("lon") or el.get("center", {}).get("lon")

            results.append({
                "name": name,
                "category": detected_category,
                "lat": lat,
                "lng": lng,
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

        logger.info("Found %d results for '%s' in %s", len(results), business_type_lower, city)
        return results

    except httpx.RequestError as e:
        logger.error("OSM Network/Timeout Exception: %s", str(e))
        return {"error": "OSM connection timed out or failed"}
    except Exception as e:
        logger.exception("Discovery failed for '%s' in %s", business_type_lower, city)
        return {"error": str(e)}
