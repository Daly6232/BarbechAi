"""
Multi-Source Discovery Engine
Primary discovery: Foursquare, TomTom, Geoapify, LocationIQ
OSM is secondary (instant preview only)
Results cross-checked and deduplicated via reconciliation engine
"""

from concurrent.futures import ThreadPoolExecutor
import re
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
}

# tunisie-medicale.com — medical vertical only. Confirmed accessible (meta-robots:
# index,follow, no bot blocking) as of this integration. Category slugs verified
# by direct fetch; the site's own regional filter param wasn't verified against
# live requests, so we pull unfiltered listing pages and match city client-side
# instead — more robust than guessing an unverified query string.
TUNISIE_MEDICALE_MAP = {
    "dentiste": "dentiste",
    "cabinet médical": "docteur",
    "pharmacie": "pharmacie",
    "vétérinaire": "veterinaire",
    "cabinet de kinésithérapie": "kinesitherapie",
    "laboratoire d'analyses": "laboratoire-analyse-medicale",
    "clinique": "hopital-clinique",
}

# goafricaonline.com/tn — confirmed accessible, huge multi-category directory.
# Only mapping the categories actually confirmed live via fetch (food/alimentation
# vertical); add more slugs here once verified rather than guessing them.
GOAFRICA_MAP = {
    "restaurant": "restaurants",
    "fast-food": "fast-food",
    "pizzeria": "pizzeria",
    "boulangerie": "boulangeries-patisseries",
    "pâtisserie": "boulangeries-patisseries",
    "boucherie": "boucheries",
    "épicerie": "epicerie",
    "traiteur": "traiteurs",
    "lounge": "bars",
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

def _search_foursquare(session: requests.Session, business_type: str, city: str, lat: float, lng: float) -> list:
    if not FOURSQUARE_KEY:
        return []
    query = QUERY_MAP.get(business_type, business_type)
    try:
        res = session.get(
            "https://api.foursquare.com/v3/places/search",
            headers={"Authorization": FOURSQUARE_KEY, "Accept": "application/json"},
            params={
                "query": query,
                "ll": f"{lat},{lng}",  # Changed to precise coordinates bias instead of text guessing
                "radius": 15000,
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

def _search_tomtom(session: requests.Session, business_type: str, city: str, lat: float, lng: float) -> list:
    if not TOMTOM_KEY:
        return []
    query = QUERY_MAP.get(business_type, business_type)
    try:
        # Re-centered query formatting by removing redundant terms TomTom already narrows with lat/lon bias
        res = session.get(
            f"https://api.tomtom.com/search/2/search/{requests.utils.quote(query)}.json",
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

def _search_geoapify(session: requests.Session, business_type: str, city: str, lat: float, lng: float) -> list:
    if not GEOAPIFY_KEY:
        return []
    category = GEOAPIFY_MAP.get(business_type)
    if not category:
        return []
    try:
        res = session.get(
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

def _search_locationiq(session: requests.Session, business_type: str, city: str, lat: float, lng: float) -> list:
    if not LOCATIONIQ_KEY:
        return []
    query = QUERY_MAP.get(business_type, business_type)
    try:
        res = session.get(
            "https://us1.locationiq.com/v1/search",
            params={
                "key": LOCATIONIQ_KEY,
                "q": f"{query} {city}",
                "format": "json",
                "limit": 50,
                "countrycodes": "tn",
                "lat": lat,  # Added local coordinate biasing for precise proximity ranking
                "lon": lng,
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


# ── tunisie-medicale.com ─────────────────────────────────────────────────────
# NOTE: built from a markdown-rendered preview of the page, not raw HTML — this
# environment has no way to inspect real DOM/class names ahead of time. Parsing
# is anchored on the URL pattern of profile links (/index.php/{cat}/{id}-{slug})
# rather than CSS classes, which is more resilient to markup changes but should
# still be test-run against a live page before relying on it in production.

def _search_tunisie_medicale(session: requests.Session, business_type: str, city: str, lat: float, lng: float) -> list:
    slug = TUNISIE_MEDICALE_MAP.get(business_type)
    if not slug:
        return []
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        logger.warning("tunisie-medicale: beautifulsoup4 not installed, skipping")
        return []

    results = []
    city_norm = city.lower().strip()
    try:
        # Pull first 3 pages (~60 listings); filter by city client-side since the
        # site's own region-filter query param wasn't verified live.
        for offset in (0, 20, 40):
            path = f"/index.php/{slug}" if offset == 0 else f"/index.php/{slug}/index/{offset}"
            res = session.get(f"https://tunisie-medicale.com{path}", timeout=TIMEOUT)
            if res.status_code != 200:
                break
            soup = BeautifulSoup(res.text, "html.parser")
            profile_links = soup.find_all("a", href=re.compile(rf"/index\.php/{slug}/\d+-"))
            if not profile_links:
                break
            for link in profile_links:
                name = link.get_text(strip=True)
                if not name:
                    continue
                container = link.find_parent(["li", "div", "article"]) or link.parent
                block_text = container.get_text(" ", strip=True) if container else ""
                if city_norm not in block_text.lower():
                    continue
                results.append(_normalize({
                    "name": name,
                    "category": business_type,
                    "address": block_text[:200],
                    "source": ["tunisie_medicale"],
                }))
        logger.info("tunisie-medicale: %d for '%s' in %s", len(results), business_type, city)
        return results
    except Exception as e:
        logger.warning("tunisie-medicale failed: %s", e)
        return []


# ── goafricaonline.com/tn ────────────────────────────────────────────────────
# Same caveat as above: anchored on the /tn/{id}-{slug} profile-link pattern and
# on <a href="tel:..."> for phone numbers, since those are stable regardless of
# surrounding CSS/markup. Needs a live test run before production use.

def _search_goafricaonline(session: requests.Session, business_type: str, city: str, lat: float, lng: float) -> list:
    slug = GOAFRICA_MAP.get(business_type)
    if not slug:
        return []
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        logger.warning("goafricaonline: beautifulsoup4 not installed, skipping")
        return []

    results = []
    city_norm = city.lower().strip()
    try:
        for page in (1, 2, 3):
            res = session.get(
                f"https://www.goafricaonline.com/tn/annuaire/{slug}",
                params={"p": page} if page > 1 else {},
                timeout=TIMEOUT,
            )
            if res.status_code != 200:
                break
            soup = BeautifulSoup(res.text, "html.parser")
            listing_links = soup.find_all("a", href=re.compile(r"/tn/\d+-"))
            if not listing_links:
                break
            for link in listing_links:
                name = link.get_text(strip=True)
                if not name:
                    continue
                container = link.find_parent(["li", "div", "article"]) or link.parent
                block_text = container.get_text(" ", strip=True) if container else ""
                if city_norm not in block_text.lower():
                    continue
                tel_link = container.find("a", href=re.compile(r"^tel:")) if container else None
                phone = tel_link["href"].replace("tel:", "").strip() if tel_link else ""
                results.append(_normalize({
                    "name": name,
                    "category": business_type,
                    "address": block_text[:200],
                    "phone": phone,
                    "source": ["goafricaonline"],
                }))
        logger.info("goafricaonline: %d for '%s' in %s", len(results), business_type, city)
        return results
    except Exception as e:
        logger.warning("goafricaonline failed: %s", e)
        return []


# ── Orchestrator ──────────────────────────────────────────────────────────────

def discover_multi_source(city: str, business_type: str, osm_results: list) -> dict:
    lat, lng = _get_center(city)
    bt = business_type.lower().strip()

    # Unified Connection session pool to speed up parallel requests by skipping redundant handshakes
    session = requests.Session()

    try:
        with ThreadPoolExecutor(max_workers=6) as executor:
            f_fsq = executor.submit(_search_foursquare, session, bt, city, lat, lng)
            f_tom = executor.submit(_search_tomtom, session, bt, city, lat, lng)
            f_geo = executor.submit(_search_geoapify, session, bt, city, lat, lng)
            f_liq = executor.submit(_search_locationiq, session, bt, city, lat, lng)
            f_tnm = executor.submit(_search_tunisie_medicale, session, bt, city, lat, lng)
            f_gao = executor.submit(_search_goafricaonline, session, bt, city, lat, lng)

            fsq = f_fsq.result()
            tom = f_tom.result()
            geo = f_geo.result()
            liq = f_liq.result()
            tnm = f_tnm.result()
            gao = f_gao.result()
    finally:
        session.close()

    all_results = fsq + tom + geo + liq + tnm + gao
    return {
        "all_results": all_results,
        "source_summary": {
            "foursquare": len(fsq),
            "tomtom": len(tom),
            "geoapify": len(geo),
            "locationiq": len(liq),
            "tunisie_medicale": len(tnm),
            "goafricaonline": len(gao),
            "total": len(all_results),
        },
    }
