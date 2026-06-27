"""
Multi-Source Discovery Engine
Phase 2: Parallel search across Foursquare, TomTom, Geoapify.
Primary source when OSM returns 0 results.
"""

from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
from app.core.config import settings
from app.core.logging import get_logger
from app.data.location_bbox import LOCATION_BBOX

logger = get_logger(__name__)

FOURSQUARE_KEY = settings.FOURSQUARE_API_KEY
TOMTOM_KEY = settings.TOMTOM_API_KEY
GEOAPIFY_KEY = settings.GEOAPIFY_API_KEY

TIMEOUT = settings.REQUEST_TIMEOUT

# ── French label → search query per API ──────────────────────────────────────

FOURSQUARE_QUERY_MAP = {
    "restaurant": "restaurant",
    "café": "cafe coffee",
    "lounge": "lounge bar",
    "fast-food": "fast food",
    "pizzeria": "pizza",
    "sandwicherie": "sandwich",
    "snack": "snack",
    "pâtisserie": "patisserie pastry",
    "boulangerie": "boulangerie bakery",
    "boucherie": "boucherie butcher",
    "épicerie": "epicerie grocery",
    "supermarché": "supermarket",
    "traiteur": "traiteur catering",
    "hôtel": "hotel",
    "maison d'hôtes": "guest house",
    "auberge": "hostel auberge",
    "résidence touristique": "residence hotel",
    "agence de voyage": "travel agency",
    "pharmacie": "pharmacy pharmacie",
    "parapharmacie": "parapharmacie cosmetics",
    "clinique": "clinic clinique",
    "cabinet médical": "doctor medical",
    "dentiste": "dentist dentiste",
    "opticien": "optician opticien",
    "laboratoire d'analyses": "laboratory analyses",
    "vétérinaire": "veterinarian",
    "cabinet de kinésithérapie": "physiotherapy kinesitherapie",
    "radiologie": "radiology radiologie",
    "salle de sport": "gym fitness",
    "piscine": "swimming pool piscine",
    "club sportif": "sports club",
    "centre de fitness": "fitness center",
    "salon de coiffure": "hair salon coiffure",
    "institut de beauté": "beauty salon institut",
    "hammam": "hammam spa",
    "spa": "spa",
    "centre d'esthétique": "esthetique beauty",
    "onglerie": "nail salon onglerie",
    "centre de formation": "training center formation",
    "école de langue": "language school",
    "auto-école": "driving school auto ecole",
    "académie de musique": "music school",
    "académie de danse": "dance school",
    "crèche": "daycare creche",
    "banque": "bank banque",
    "assurance": "insurance assurance",
    "agence immobilière": "real estate immobilier",
    "cabinet juridique": "law firm avocat",
    "cabinet comptable": "accounting comptable",
    "bureau de change": "currency exchange",
    "notaire": "notaire notary",
    "agence de communication": "communication agency",
    "agence digitale": "digital agency",
    "société informatique": "IT company informatique",
    "espace coworking": "coworking space",
    "garage": "garage car repair",
    "lavage auto": "car wash",
    "station-service": "gas station fuel",
    "vente de pièces auto": "auto parts",
    "concessionnaire": "car dealer",
    "salle des fêtes": "event hall salle fetes",
    "studio photo": "photo studio",
    "imprimerie": "printing imprimerie",
    "librairie": "bookstore librairie",
    "papeterie": "stationery papeterie",
    "bijouterie": "jewelry bijouterie",
    "vêtements": "clothing clothes",
    "chaussures": "shoes chaussures",
    "maroquinerie": "leather goods",
    "lingerie": "lingerie",
    "articles de sport": "sports store",
    "électroménager": "appliances electromenager",
    "informatique": "computer store",
    "téléphonie": "mobile phone",
    "meubles": "furniture meubles",
    "décoration": "decoration home",
    "matériaux de construction": "building materials construction",
    "quincaillerie": "hardware store",
    "droguerie": "hardware chemist",
    "fleuriste": "florist fleurs",
    "transport": "transport logistics",
    "logistique": "logistics warehouse",
    "grossiste": "wholesale grossiste",
    "bureau d'études": "consulting engineering",
    "cabinet d'architecture": "architecture architect",
    "menuiserie": "carpenter menuiserie",
    "plomberie": "plumber plomberie",
    "électricité": "electrician",
    "climatisation": "air conditioning",
    "peinture": "painter peinture",
    "carrelage": "tiling carrelage",
    "ferronnerie": "ironwork ferronnerie",
}

GEOAPIFY_CATEGORY_MAP = {
    "restaurant": "catering.restaurant",
    "café": "catering.cafe",
    "fast-food": "catering.fast_food",
    "pâtisserie": "catering.cafe",
    "boulangerie": "commercial.food_and_drink.bakery",
    "boucherie": "commercial.food_and_drink.butcher",
    "épicerie": "commercial.supermarket",
    "supermarché": "commercial.supermarket",
    "hôtel": "accommodation.hotel",
    "maison d'hôtes": "accommodation.guest_house",
    "auberge": "accommodation.hostel",
    "pharmacie": "healthcare.pharmacy",
    "clinique": "healthcare.clinic_or_praxis",
    "cabinet médical": "healthcare.clinic_or_praxis",
    "dentiste": "healthcare.dentist",
    "opticien": "commercial.health_and_beauty.optician",
    "vétérinaire": "healthcare.veterinary",
    "salle de sport": "sport.fitness",
    "piscine": "leisure.swimming_pool",
    "club sportif": "sport",
    "salon de coiffure": "commercial.health_and_beauty.hairdresser",
    "institut de beauté": "commercial.health_and_beauty.beauty",
    "spa": "leisure.spa",
    "banque": "commercial.shopping.bank",
    "agence immobilière": "commercial.real_estate",
    "garage": "commercial.vehicle.car_repair",
    "lavage auto": "commercial.vehicle.car_wash",
    "station-service": "commercial.vehicle.fuel",
    "concessionnaire": "commercial.vehicle.car_dealer",
    "librairie": "commercial.books",
    "bijouterie": "commercial.clothing.jewelry",
    "vêtements": "commercial.clothing",
    "chaussures": "commercial.clothing.shoes",
    "meubles": "commercial.furniture_and_garden",
    "informatique": "commercial.electronics",
    "téléphonie": "commercial.electronics",
    "fleuriste": "commercial.florist",
}


# ── Foursquare ────────────────────────────────────────────────────────────────

def _search_foursquare(business_type: str, city: str, lat: float, lng: float) -> list:
    if not FOURSQUARE_KEY:
        return []
    query = FOURSQUARE_QUERY_MAP.get(business_type, business_type)
    try:
        res = requests.get(
            "https://api.foursquare.com/v3/places/search",
            headers={"Authorization": FOURSQUARE_KEY, "Accept": "application/json"},
            params={
                "query": query,
                "near": f"{city}, Tunisia",
                "limit": 50,
                "fields": "name,location,tel,website,social_media,hours,categories",
            },
            timeout=TIMEOUT,
        )
        data = res.json()
        results = []
        for place in data.get("results", []):
            loc = place.get("location", {})
            address = ", ".join(filter(None, [
                loc.get("address", ""),
                loc.get("locality", ""),
                loc.get("postcode", ""),
            ]))
            social = place.get("social_media", {})
            results.append({
                "name": place.get("name", ""),
                "category": business_type,
                "lat": loc.get("latitude"),
                "lng": loc.get("longitude"),
                "address": address,
                "phone": place.get("tel", ""),
                "website": place.get("website", ""),
                "facebook": social.get("facebook_id", ""),
                "instagram": social.get("instagram", ""),
                "source": ["foursquare"],
            })
        logger.info("Foursquare: %d results for '%s' in %s", len(results), business_type, city)
        return results
    except Exception as e:
        logger.warning("Foursquare failed: %s", e)
        return []


# ── TomTom ────────────────────────────────────────────────────────────────────

def _search_tomtom(business_type: str, city: str, lat: float, lng: float) -> list:
    if not TOMTOM_KEY:
        return []
    query = FOURSQUARE_QUERY_MAP.get(business_type, business_type)
    try:
        res = requests.get(
            "https://api.tomtom.com/search/2/search/{}.json".format(
                requests.utils.quote(f"{query} {city} Tunisia")
            ),
            params={
                "key": TOMTOM_KEY,
                "countrySet": "TN",
                "limit": 50,
                "lat": lat,
                "lon": lng,
                "radius": 10000,
            },
            timeout=TIMEOUT,
        )
        data = res.json()
        results = []
        for r in data.get("results", []):
            poi = r.get("poi", {})
            addr = r.get("address", {})
            pos = r.get("position", {})
            phone = ""
            if poi.get("phone"):
                phone = poi["phone"]
            results.append({
                "name": poi.get("name", ""),
                "category": business_type,
                "lat": pos.get("lat"),
                "lng": pos.get("lon"),
                "address": addr.get("freeformAddress", ""),
                "phone": phone,
                "website": poi.get("url", ""),
                "source": ["tomtom"],
            })
        logger.info("TomTom: %d results for '%s' in %s", len(results), business_type, city)
        return results
    except Exception as e:
        logger.warning("TomTom failed: %s", e)
        return []


# ── Geoapify ──────────────────────────────────────────────────────────────────

def _search_geoapify(business_type: str, city: str, lat: float, lng: float) -> list:
    if not GEOAPIFY_KEY:
        return []
    category = GEOAPIFY_CATEGORY_MAP.get(business_type, "")
    if not category:
        return []
    try:
        res = requests.get(
            "https://api.geoapify.com/v2/places",
            params={
                "categories": category,
                "filter": f"circle:{lng},{lat},10000",
                "bias": f"proximity:{lng},{lat}",
                "limit": 50,
                "apiKey": GEOAPIFY_KEY,
            },
            timeout=TIMEOUT,
        )
        data = res.json()
        results = []
        for feat in data.get("features", []):
            props = feat.get("properties", {})
            coords = feat.get("geometry", {}).get("coordinates", [None, None])
            results.append({
                "name": props.get("name", ""),
                "category": business_type,
                "lat": coords[1],
                "lng": coords[0],
                "address": props.get("formatted", ""),
                "phone": props.get("contact", {}).get("phone", ""),
                "website": props.get("website", ""),
                "source": ["geoapify"],
            })
        results = [r for r in results if r["name"]]
        logger.info("Geoapify: %d results for '%s' in %s", len(results), business_type, city)
        return results
    except Exception as e:
        logger.warning("Geoapify failed: %s", e)
        return []


# ── Orchestrator ──────────────────────────────────────────────────────────────

def discover_multi_source(city: str, business_type: str, osm_results: list) -> dict:
    bbox = LOCATION_BBOX.get(city)
    if bbox:
        lat = (bbox[0] + bbox[2]) / 2
        lng = (bbox[1] + bbox[3]) / 2
    else:
        lat, lng = 36.8, 10.18

    bt = business_type.lower().strip()

    with ThreadPoolExecutor(max_workers=3) as executor:
        f_fsq = executor.submit(_search_foursquare, bt, city, lat, lng)
        f_tom = executor.submit(_search_tomtom, bt, city, lat, lng)
        f_geo = executor.submit(_search_geoapify, bt, city, lat, lng)

        fsq = f_fsq.result()
        tom = f_tom.result()
        geo = f_geo.result()

    all_results = fsq + tom + geo

    return {
        "all_results": all_results,
        "source_summary": {
            "foursquare": len(fsq),
            "tomtom": len(tom),
            "geoapify": len(geo),
            "total": len(all_results),
        },
    }
