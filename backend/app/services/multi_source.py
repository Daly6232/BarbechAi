"""
Multi-Source Discovery Engine
Phase 2: Parallel search across Foursquare, HERE, TomTom, Geoapify.
Finds businesses that OSM may have missed and enriches existing ones.
"""

from concurrent.futures import ThreadPoolExecutor, as_completed
import requests

from app.core.config import settings
from app.core.logging import get_logger
from app.data.location_bbox import LOCATION_BBOX

logger = get_logger(__name__)

# ───────────────────────────────────────────────────────────────
# API KEY CHECKS
# ───────────────────────────────────────────────────────────────

FOURSQUARE_KEY = settings.FOURSQUARE_API_KEY
HERE_KEY = settings.HERE_API_KEY
TOMTOM_KEY = settings.TOMTOM_API_KEY
GEOAPIFY_KEY = settings.GEOAPIFY_API_KEY


# ───────────────────────────────────────────────────────────────
# FOURSQUARE
# ───────────────────────────────────────────────────────────────

def _foursquare_tag(business_type: str) -> str:
    """Map French business type to Foursquare category ID or search query."""
    mapping = {
        "restaurant": "restaurant",
        "café": "cafe",
        "fast food": "fast food",
        "pâtisserie": "bakery",
        "boulangerie": "bakery",
        "boucherie": "butcher",
        "épicerie": "convenience store",
        "supermarché": "supermarket",
        "hotel": "hotel",
        "pharmacie": "pharmacy",
        "parapharmacie": "pharmacy",
        "clinique": "clinic",
        "cabinet médical": "doctor",
        "dentiste": "dentist",
        "opticien": "optician",
        "laboratoire": "laboratory",
        "vétérinaire": "veterinarian",
        "gym": "gym",
        "salle de sport": "gym",
        "salon de coiffure": "hair salon",
        "centre esthétique": "beauty salon",
        "hammam": "spa",
        "spa": "spa",
        "banque": "bank",
        "école": "school",
        "lycée": "school",
        "université": "university",
        "librairie": "bookstore",
        "garage": "auto repair",
        "station service": "gas station",
        "cinéma": "movie theater",
        "musée": "museum",
        "centre commercial": "shopping mall",
        "marché": "market",
    }
    return mapping.get(business_type, business_type)


def search_foursquare(city: str, business_type: str, bbox: tuple) -> list:
    """Search Foursquare Places API for businesses."""
    if not FOURSQUARE_KEY:
        logger.warning("Foursquare API key not configured")
        return []

    try:
        south, west, north, east = bbox
        category = _foursquare_tag(business_type)

        response = requests.get(
            "https://api.foursquare.com/v3/places/search",
            headers={
                "Authorization": FOURSQUARE_KEY,
                "Accept": "application/json",
            },
            params={
                "query": category,
                "near": f"{city}, Tunisia",
                "limit": 50,
            },
            timeout=settings.REQUEST_TIMEOUT,
        )

        if response.status_code != 200:
            logger.warning("Foursquare returned %s", response.status_code)
            return []

        results = response.json().get("results", [])
        businesses = []

        for place in results:
            name = place.get("name", "")
            if not name:
                continue

            location = place.get("location", {})
            geocodes = place.get("geocodes", {}).get("main", {})

            businesses.append({
                "name": name,
                "category": category,
                "lat": geocodes.get("latitude") or location.get("lat"),
                "lng": geocodes.get("longitude") or location.get("lng"),
                "address": ", ".join(location.get("formatted_address", [])) if isinstance(location.get("formatted_address"), list) else location.get("address", ""),
                "phone": place.get("tel", ""),
                "website": place.get("website", ""),
                "source": "foursquare",
            })

        logger.info("Foursquare found %d businesses for '%s' in %s", len(businesses), business_type, city)
        return businesses

    except Exception as exc:
        logger.exception("Foursquare search failed: %s", str(exc))
        return []


# ───────────────────────────────────────────────────────────────
# HERE MAPS
# ───────────────────────────────────────────────────────────────

def _here_category(business_type: str) -> str:
    """Map French business type to HERE category."""
    mapping = {
        "restaurant": "restaurant",
        "café": "cafe",
        "fast food": "fast-food",
        "boulangerie": "bakery",
        "supermarché": "supermarket",
        "hotel": "hotel",
        "pharmacie": "pharmacy",
        "clinique": "hospital",
        "dentiste": "dentist",
        "gym": "sports-facility",
        "salon de coiffure": "hairdresser",
        "centre esthétique": "beauty-salon",
        "banque": "bank",
        "école": "school",
        "station service": "petrol-station",
        "cinéma": "cinema",
        "musée": "museum",
        "centre commercial": "shopping-center",
    }
    return mapping.get(business_type, business_type)


def search_here(city: str, business_type: str, bbox: tuple) -> list:
    """Search HERE Maps API for businesses."""
    if not HERE_KEY:
        logger.warning("HERE API key not configured")
        return []

    try:
        south, west, north, east = bbox
        category = _here_category(business_type)

        response = requests.get(
            "https://discover.search.hereapi.com/v1/discover",
            headers={
                "Authorization": f"Bearer {HERE_KEY}",
            },
            params={
                "q": category,
                "in": f"circle:{ (north + south) / 2 },{ (east + west) / 2 };r=20000",
                "limit": 50,
            },
            timeout=settings.REQUEST_TIMEOUT,
        )

        if response.status_code != 200:
            logger.warning("HERE returned %s", response.status_code)
            return []

        items = response.json().get("items", [])
        businesses = []

        for item in items:
            name = item.get("title", "")
            if not name:
                continue

            position = item.get("position", {})
            address = item.get("address", {})
            contacts = item.get("contacts", [{}])[0] if item.get("contacts") else {}

            businesses.append({
                "name": name,
                "category": category,
                "lat": position.get("lat"),
                "lng": position.get("lng"),
                "address": address.get("label", ""),
                "phone": " ".join(contacts.get("phone", [])) if isinstance(contacts.get("phone"), list) else contacts.get("phone", ""),
                "website": " ".join(contacts.get("www", [])) if isinstance(contacts.get("www"), list) else contacts.get("www", ""),
                "opening_hours": ", ".join(item.get("openingHours", {}).get("text", [])) if isinstance(item.get("openingHours", {}).get("text"), list) else "",
                "source": "here",
            })

        logger.info("HERE found %d businesses for '%s' in %s", len(businesses), business_type, city)
        return businesses

    except Exception as exc:
        logger.exception("HERE search failed: %s", str(exc))
        return []


# ───────────────────────────────────────────────────────────────
# TOMTOM
# ───────────────────────────────────────────────────────────────

def _tomtom_category(business_type: str) -> str:
    """Map French business type to TomTom category."""
    mapping = {
        "restaurant": "RESTAURANT",
        "café": "CAFE",
        "fast food": "FAST FOOD",
        "boulangerie": "BAKERY",
        "supermarché": "SUPERMARKET",
        "hotel": "HOTEL",
        "pharmacie": "PHARMACY",
        "clinique": "HOSPITAL",
        "dentiste": "DENTIST",
        "gym": "HEALTH CLUB",
        "salon de coiffure": "HAIR DRESSER",
        "banque": "BANK",
        "école": "SCHOOL",
        "station service": "PETROL STATION",
        "cinéma": "CINEMA",
        "musée": "MUSEUM",
        "centre commercial": "SHOPPING CENTER",
    }
    return mapping.get(business_type, business_type)


def search_tomtom(city: str, business_type: str, bbox: tuple) -> list:
    """Search TomTom API for businesses."""
    if not TOMTOM_KEY:
        logger.warning("TomTom API key not configured")
        return []

    try:
        south, west, north, east = bbox
        category = _tomtom_category(business_type)

        response = requests.get(
            "https://api.tomtom.com/search/2/poiSearch/.json",
            params={
                "key": TOMTOM_KEY,
                "query": category,
                "countrySet": "TN",
                "lat": (north + south) / 2,
                "lon": (east + west) / 2,
                "radius": 20000,
                "limit": 50,
            },
            timeout=settings.REQUEST_TIMEOUT,
        )

        if response.status_code != 200:
            logger.warning("TomTom returned %s", response.status_code)
            return []

        results = response.json().get("results", [])
        businesses = []

        for item in results:
            poi = item.get("poi", {})
            name = poi.get("name", "")
            if not name:
                continue

            position = item.get("position", {})
            address = item.get("address", {})

            businesses.append({
                "name": name,
                "category": category,
                "lat": position.get("lat"),
                "lng": position.get("lon"),
                "address": address.get("freeformAddress", ""),
                "phone": poi.get("phone", ""),
                "website": poi.get("url", ""),
                "source": "tomtom",
            })

        logger.info("TomTom found %d businesses for '%s' in %s", len(businesses), business_type, city)
        return businesses

    except Exception as exc:
        logger.exception("TomTom search failed: %s", str(exc))
        return []


# ───────────────────────────────────────────────────────────────
# GEOAPIFY
# ───────────────────────────────────────────────────────────────

def _geoapify_category(business_type: str) -> str:
    """Map French business type to Geoapify category."""
    mapping = {
        "restaurant": "catering.restaurant",
        "café": "catering.cafe",
        "fast food": "catering.fast_food",
        "boulangerie": "catering.bakery",
        "supermarché": "commercial.supermarket",
        "hotel": "accommodation.hotel",
        "pharmacie": "healthcare.pharmacy",
        "clinique": "healthcare.hospital",
        "dentiste": "healthcare.dentist",
        "opticien": "healthcare.optician",
        "gym": "sport.fitness",
        "salon de coiffure": "beauty.hairdresser",
        "centre esthétique": "beauty.salon",
        "spa": "beauty.spa",
        "banque": "service.financial.bank",
        "école": "education.school",
        "station service": "service.vehicle.fuel",
        "cinéma": "entertainment.cinema",
        "musée": "entertainment.museum",
        "centre commercial": "commercial.shopping_mall",
        "garage": "service.vehicle.repair",
        "librairie": "commercial.books",
        "marché": "commercial.marketplace",
    }
    return mapping.get(business_type, business_type)


def search_geoapify(city: str, business_type: str, bbox: tuple) -> list:
    """Search Geoapify Places API for businesses."""
    if not GEOAPIFY_KEY:
        logger.warning("Geoapify API key not configured")
        return []

    try:
        south, west, north, east = bbox
        category = _geoapify_category(business_type)

        response = requests.get(
            "https://api.geoapify.com/v2/places",
            params={
                "apiKey": GEOAPIFY_KEY,
                "categories": category,
                "filter": f"rect:{west},{south},{east},{north}",
                "limit": 50,
            },
            timeout=settings.REQUEST_TIMEOUT,
        )

        if response.status_code != 200:
            logger.warning("Geoapify returned %s", response.status_code)
            return []

        features = response.json().get("features", [])
        businesses = []

        for feature in features:
            props = feature.get("properties", {})
            name = props.get("name", "")
            if not name:
                continue

            geometry = feature.get("geometry", {})
            coords = geometry.get("coordinates", [None, None])

            businesses.append({
                "name": name,
                "category": category,
                "lat": coords[1] if len(coords) > 1 else None,
                "lng": coords[0] if len(coords) > 0 else None,
                "address": props.get("formatted", "") or props.get("address_line1", ""),
                "phone": props.get("phone", ""),
                "website": props.get("website", ""),
                "email": props.get("email", ""),
                "facebook": props.get("facebook", ""),
                "instagram": props.get("instagram", ""),
                "opening_hours": props.get("opening_hours", ""),
                "source": "geoapify",
            })

        logger.info("Geoapify found %d businesses for '%s' in %s", len(businesses), business_type, city)
        return businesses

    except Exception as exc:
        logger.exception("Geoapify search failed: %s", str(exc))
        return []


# ───────────────────────────────────────────────────────────────
# ORCHESTRATOR
# ───────────────────────────────────────────────────────────────

def discover_multi_source(city: str, business_type: str, osm_results: list) -> dict:
    """
    Run all 4 external APIs in parallel.
    Returns:
        - all_results: list of all businesses found by external sources
        - new_discoveries: businesses NOT in OSM results
        - source_summary: counts per source
    """
    if city not in LOCATION_BBOX:
        return {
            "all_results": [],
            "new_discoveries": [],
            "source_summary": {},
            "error": "Location not in bbox",
        }

    bbox = LOCATION_BBOX[city]

    all_external = []
    source_summary = {}

    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {
            executor.submit(search_foursquare, city, business_type, bbox): "foursquare",
            executor.submit(search_here, city, business_type, bbox): "here",
            executor.submit(search_tomtom, city, business_type, bbox): "tomtom",
            executor.submit(search_geoapify, city, business_type, bbox): "geoapify",
        }

        for future in as_completed(futures):
            source_name = futures[future]
            try:
                results = future.result()
                all_external.extend(results)
                source_summary[source_name] = len(results)
            except Exception as exc:
                logger.exception("%s failed: %s", source_name, str(exc))
                source_summary[source_name] = 0

    logger.info(
        "Multi-source: %d total from external APIs (%s)",
        len(all_external),
        ", ".join(f"{k}={v}" for k, v in source_summary.items()),
    )

    return {
        "all_results": all_external,
        "source_summary": source_summary,
    }
