"""
Multi-Source Discovery Engine
Primary discovery: Foursquare, TomTom, Geoapify, LocationIQ
OSM is secondary (instant preview only)
Results cross-checked and deduplicated via reconciliation engine
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
LOCATIONIQ_KEY = settings.LOCATIONIQ_API_KEY
TIMEOUT = settings.REQUEST_TIMEOUT

QUERY_MAP = {
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
    "pharmacie": "pharmacie pharmacy",
    "parapharmacie": "parapharmacie cosmetics beauty",
    "clinique": "clinique clinic",
    "cabinet médical": "cabinet medical doctor",
    "dentiste": "dentiste dentist",
    "opticien": "opticien optician",
    "laboratoire d'analyses": "laboratoire analyses",
    "vétérinaire": "veterinaire veterinary",
    "cabinet de kinésithérapie": "kinesitherapie physiotherapy",
    "radiologie": "radiologie radiology",
    "salle de sport": "salle sport gym fitness",
    "piscine": "piscine swimming pool",
    "club sportif": "club sportif sports",
    "centre de fitness": "fitness center",
    "salon de coiffure": "coiffure hair salon",
    "institut de beauté": "institut beaute beauty",
    "hammam": "hammam",
    "spa": "spa",
    "centre d'esthétique": "esthetique beauty center",
    "onglerie": "onglerie nail salon",
    "centre de formation": "centre formation training",
    "école de langue": "ecole langue language school",
    "auto-école": "auto ecole driving school",
    "académie de musique": "academie musique music",
    "académie de danse": "academie danse dance",
    "crèche": "creche daycare",
    "banque": "banque bank",
    "assurance": "assurance insurance",
    "agence immobilière": "agence immobiliere real estate",
    "cabinet juridique": "cabinet juridique lawyer avocat",
    "cabinet comptable": "cabinet comptable accounting",
    "bureau de change": "bureau de change currency",
    "notaire": "notaire notary",
    "agence de communication": "agence communication marketing",
    "agence digitale": "agence digitale digital",
    "société informatique": "societe informatique IT",
    "espace coworking": "coworking space",
    "garage": "garage car repair",
    "lavage auto": "lavage auto car wash",
    "station-service": "station service fuel",
    "vente de pièces auto": "pieces auto car parts",
    "concessionnaire": "concessionnaire car dealer",
    "salle des fêtes": "salle fetes event hall",
    "studio photo": "studio photo",
    "imprimerie": "imprimerie printing",
    "librairie": "librairie bookstore",
    "papeterie": "papeterie stationery",
    "bijouterie": "bijouterie jewelry",
    "vêtements": "vetements clothing",
    "chaussures": "chaussures shoes",
    "maroquinerie": "maroquinerie leather",
    "lingerie": "lingerie",
    "articles de sport": "articles sport",
    "électroménager": "electromenager appliances",
    "informatique": "informatique computer",
    "téléphonie": "telephonie mobile phone",
    "meubles": "meubles furniture",
    "décoration": "decoration home",
    "matériaux de construction": "materiaux construction building",
    "quincaillerie": "quincaillerie hardware",
    "droguerie": "droguerie hardware",
    "fleuriste": "fleuriste florist",
    "transport": "transport logistics",
    "logistique": "logistique warehouse",
    "grossiste": "grossiste wholesale",
    "bureau d'études": "bureau etudes consulting",
    "cabinet d'architecture": "architecture architect",
    "menuiserie": "menuiserie carpenter",
    "plomberie": "plomberie plumber",
    "électricité": "electricite electrician",
    "climatisation": "climatisation air conditioning",
    "peinture": "peinture painter",
    "carrelage": "carrelage tiling",
    "ferronnerie": "ferronnerie ironwork",
}

GEOAPIFY_MAP = {
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
    "hammam": "leisure.spa",
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
    "supermarché": "commercial.supermarket",
}


def _get_center(city: str):
    bbox = LOCATION_BBOX.get(city)
    if bbox:
        return (bbox[0] + bbox[2]) / 2, (bbox[1] + bbox[3]) / 2
    return 36.8, 10.18


def _normalize(business: dict) -> dict:
    return {
        "name": business.get("name", "").strip(),
        "category": business.get("category", ""),
        "lat": business.get("lat"),
        "lng": business.get("lng"),
        "address": business.get("address", ""),
        "phone": business.get("phone", ""),
        "website": business.get("website", ""),
        "email": business.get("email", ""),
        "facebook": business.get("facebook", ""),
        "instagram": business.get("instagram", ""),
        "opening_hours": business.get("opening_hours", ""),
        "source": business.get("source", []),
    }


# ── Foursquare ────────────────────────────────────────────────────────────────

def _search_foursquare(business_type: str, city: str, lat: float, lng: float) -> list:
    if not FOURSQUARE_KEY:
        return []
    query = QUERY_MAP.get(business_type, business_type)
    try:
        res = requests.get(
            "https://api.foursquare.com/v3/places/search",
            headers={"Authorization": FOURSQUARE_KEY, "Accept": "application/json"},
            params={
                "query": query,
                "near": f"{city}, Tunisia",
                "limit": 50,
                "fields": "name,location,tel,website,social_media,hours",
            },
            timeout=TIMEOUT,
        )
        data = res.json()
        results = []
        for p in data.get("results", []):
            if not p.get("name"):
                continue
            loc = p.get("location", {})
            social = p.get("social_media", {})
            address = ", ".join(filter(None, [
                loc.get("address", ""),
                loc.get("locality", ""),
                loc.get("postcode", ""),
            ]))
            fb_id = social.get("facebook_id", "")
            ig = social.get("instagram", "")
            results.append(_normalize({
                "name": p["name"],
                "category": business_type,
                "lat": loc.get("latitude"),
                "lng": loc.get("longitude"),
                "address": address,
                "phone": p.get("tel", ""),
                "website": p.get("website", ""),
                "facebook": f"https://www.facebook.com/{fb_id}" if fb_id else "",
                "instagram": f"https://www.instagram.com/{ig}" if ig and not ig.startswith("http") else ig,
                "source": ["foursquare"],
            }))
        logger.info("Foursquare: %d for '%s' in %s", len(results), business_type, city)
        return results
    except Exception as e:
        logger.warning("Foursquare failed: %s", e)
        return []


# ── TomTom ────────────────────────────────────────────────────────────────────

def _search_tomtom(business_type: str, city: str, lat: float, lng: float) -> list:
    if not TOMTOM_KEY:
        return []
    query = QUERY_MAP.get(business_type, business_type)
    try:
        res = requests.get(
            f"https://api.tomtom.com/search/2/search/{requests.utils.quote(f'{query} {city} Tunisia')}.json",
            params={
                "key": TOMTOM_KEY,
                "countrySet": "TN",
                "limit": 50,
                "lat": lat,
                "lon": lng,
                "radius": 15000,
            },
            timeout=TIMEOUT,
        )
        data = res.json()
        results = []
        for r in data.get("results", []):
            poi = r.get("poi", {})
            addr = r.get("address", {})
            pos = r.get("position", {})
            name = poi.get("name", "")
            if not name:
                continue
            results.append(_normalize({
                "name": name,
                "category": business_type,
                "lat": pos.get("lat"),
                "lng": pos.get("lon"),
                "address": addr.get("freeformAddress", ""),
                "phone": poi.get("phone", ""),
                "website": poi.get("url", ""),
                "source": ["tomtom"],
            }))
        logger.info("TomTom: %d for '%s' in %s", len(results), business_type, city)
        return results
    except Exception as e:
        logger.warning("TomTom failed: %s", e)
        return []


# ── Geoapify ──────────────────────────────────────────────────────────────────

def _search_geoapify(business_type: str, city: str, lat: float, lng: float) -> list:
    if not GEOAPIFY_KEY:
        return []
    category = GEOAPIFY_MAP.get(business_type)
    if not category:
        return []
    try:
        res = requests.get(
            "https://api.geoapify.com/v2/places",
            params={
                "categories": category,
                "filter": f"circle:{lng},{lat},15000",
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
            name = props.get("name", "")
            if not name:
                continue
            results.append(_normalize({
                "name": name,
                "category": business_type,
                "lat": coords[1],
                "lng": coords[0],
                "address": props.get("formatted", ""),
                "phone": props.get("datasource", {}).get("raw", {}).get("phone", ""),
                "website": props.get("datasource", {}).get("raw", {}).get("website", ""),
                "source": ["geoapify"],
            }))
        logger.info("Geoapify: %d for '%s' in %s", len(results), business_type, city)
        return results
    except Exception as e:
        logger.warning("Geoapify failed: %s", e)
        return []


# ── LocationIQ ────────────────────────────────────────────────────────────────

def _search_locationiq(business_type: str, city: str, lat: float, lng: float) -> list:
    if not LOCATIONIQ_KEY:
        return []
    query = QUERY_MAP.get(business_type, business_type)
    try:
        res = requests.get(
            "https://us1.locationiq.com/v1/search",
            params={
                "key": LOCATIONIQ_KEY,
                "q": f"{query} {city} Tunisia",
                "format": "json",
                "limit": 50,
                "countrycodes": "tn",
                "addressdetails": 1,
            },
            timeout=TIMEOUT,
        )
        data = res.json()
        if not isinstance(data, list):
            return []
        results = []
        for r in data:
            name = r.get("display_name", "").split(",")[0].strip()
            if not name:
                continue
            addr = r.get("address", {})
            address = ", ".join(filter(None, [
                addr.get("road", ""),
                addr.get("suburb", ""),
                addr.get("city", addr.get("town", "")),
            ]))
            results.append(_normalize({
                "name": name,
                "category": business_type,
                "lat": float(r.get("lat", 0)),
                "lng": float(r.get("lon", 0)),
                "address": address,
                "source": ["locationiq"],
            }))
        logger.info("LocationIQ: %d for '%s' in %s", len(results), business_type, city)
        return results
    except Exception as e:
        logger.warning("LocationIQ failed: %s", e)
        return []


# ── Orchestrator ──────────────────────────────────────────────────────────────

def discover_multi_source(city: str, business_type: str, osm_results: list) -> dict:
    lat, lng = _get_center(city)
    bt = business_type.lower().strip()

    with ThreadPoolExecutor(max_workers=4) as executor:
        f_fsq = executor.submit(_search_foursquare, bt, city, lat, lng)
        f_tom = executor.submit(_search_tomtom, bt, city, lat, lng)
        f_geo = executor.submit(_search_geoapify, bt, city, lat, lng)
        f_liq = executor.submit(_search_locationiq, bt, city, lat, lng)

        fsq = f_fsq.result()
        tom = f_tom.result()
        geo = f_geo.result()
        liq = f_liq.result()

    all_results = fsq + tom + geo + liq

    return {
        "all_results": all_results,
        "source_summary": {
            "foursquare": len(fsq),
            "tomtom": len(tom),
            "geoapify": len(geo),
            "locationiq": len(liq),
            "total": len(all_results),
        },
    }
