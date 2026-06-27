import random
import re
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
from ddgs import DDGS

from app.core.config import settings
from app.core.logging import get_logger
from app.services.websocket_manager import manager

logger = get_logger(__name__)

HEADERS_LIST = [
    {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"},
    {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"},
    {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"},
]

DIRECTORY_BLACKLIST = [
    "findglocal", "yelp", "tripadvisor", "foursquare", "zomato",
    "yellowpages", "pagesjaunes", "annuaire", "directory", "listing",
    "maps.google", "google.com/maps", "facebook.com/pages",
    "wikipedia", "wikimedia", "openstreetmap", "trustpilot",
    "booking.com", "expedia", "hotels.com", "airbnb",
]

FOURSQUARE_API_KEY = settings.FOURSQUARE_API_KEY


def get_headers():
    return random.choice(HEADERS_LIST)


def is_official_website(url: str, name: str, city: str) -> bool:
    if not url:
        return False
    url_lower = url.lower()
    for blocked in DIRECTORY_BLACKLIST:
        if blocked in url_lower:
            return False
    if "facebook.com" in url_lower or "instagram.com" in url_lower:
        return False
    return True


# ─── SOURCE 1: OSM Nominatim ─────────────────────────────────────────────────

def enrich_from_osm(lat, lng):
    try:
        if not lat or not lng:
            return {"source": "osm", "error": "no_coordinates"}
        url = f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lng}&format=json"
        response = requests.get(
            url,
            headers={"User-Agent": settings.USER_AGENT},
            timeout=settings.REQUEST_TIMEOUT,
        )
        data = response.json()
        return {
            "source": "osm",
            "address": data.get("display_name", ""),
        }
    except Exception as exc:
        logger.warning(f"OSM enrichment failed: {exc}")
        return {"source": "osm", "error": "blocked_or_timeout"}


# ─── SOURCE 2: Foursquare ─────────────────────────────────────────────────────

def enrich_from_foursquare(name, city):
    try:
        if not FOURSQUARE_API_KEY:
            return {"source": "foursquare", "error": "no_key"}
        response = requests.get(
            "https://api.foursquare.com/v3/places/search",
            headers={
                "Authorization": FOURSQUARE_API_KEY,
                "Accept": "application/json",
            },
            params={"query": name, "near": f"{city}, Tunisia", "limit": 1},
            timeout=settings.REQUEST_TIMEOUT,
        )
        data = response.json()
        results = data.get("results", [])
        if not results:
            return {"source": "foursquare", "error": "no_results"}
        place = results[0]
        location = place.get("location", {})
        address_parts = [
            location.get("address", ""),
            location.get("locality", ""),
            location.get("postcode", ""),
        ]
        return {
            "source": "foursquare",
            "phone": place.get("tel", ""),
            "address": ", ".join(p for p in address_parts if p),
            "website": place.get("website", ""),
        }
    except Exception as exc:
        logger.warning(f"Foursquare enrichment failed: {exc}")
        return {"source": "foursquare", "error": "blocked_or_timeout"}


# ─── SOURCE 3: DuckDuckGo ─────────────────────────────────────────────────────

def enrich_from_duckduckgo(name, city):
    try:
        results = {}
        with DDGS() as ddgs:
            # Website — strict query with city + Tunisia
            web = list(ddgs.text(
                f'"{name}" "{city}" Tunisia site officiel',
                max_results=5,
            ))
            for item in web:
                url = item.get("href", "")
                if is_official_website(url, name, city):
                    results["website"] = url
                    break

            # Facebook
            fb = list(ddgs.text(
                f'"{name}" "{city}" Tunisia site:facebook.com',
                max_results=3,
            ))
            for item in fb:
                url = item.get("href", "")
                if "facebook.com" in url and "/pages/" not in url.lower():
                    results["facebook"] = url
                    break

            # Instagram
            ig = list(ddgs.text(
                f'"{name}" "{city}" Tunisia site:instagram.com',
                max_results=3,
            ))
            for item in ig:
                url = item.get("href", "")
                if "instagram.com" in url:
                    results["instagram"] = url
                    break

        results["source"] = "duckduckgo"
        return results
    except Exception as exc:
        logger.warning(f"DuckDuckGo enrichment failed: {exc}")
        return {"source": "duckduckgo", "error": "blocked_or_timeout"}


# ─── SOURCE 4: Pages Jaunes TN ───────────────────────────────────────────────

def enrich_from_pagesjaunes(name, city):
    try:
        query = f"{name} {city}".replace(" ", "+")
        response = requests.get(
            f"https://www.pagesjaunes.tn/search?q={query}",
            headers=get_headers(),
            timeout=settings.REQUEST_TIMEOUT,
        )
        phones = re.findall(r"[\+216\s]?[2459]\d{7}", response.text)
        return {
            "source": "pagesjaunes",
            "phone": phones[0] if phones else "",
        }
    except Exception as exc:
        logger.warning(f"PagesJaunes enrichment failed: {exc}")
        return {"source": "pagesjaunes", "error": "blocked_or_timeout"}


# ─── PARALLEL ENRICHMENT ──────────────────────────────────────────────────────

def enrich_business(business_id, name, city, lat, lng, session_id=None, on_complete=None):
    sources = [
        lambda: enrich_from_osm(lat, lng),
        lambda: enrich_from_foursquare(name, city),
        lambda: enrich_from_duckduckgo(name, city),
        lambda: enrich_from_pagesjaunes(name, city),
    ]

    merged = {
        "website": None,
        "facebook": None,
        "instagram": None,
        "phone": None,
        "email": None,
        "address": None,
        "opening_hours": None,
        "sources_used": [],
        "sources_failed": [],
        "status": "ENRICHED",
    }

    with ThreadPoolExecutor(max_workers=settings.MAX_WORKERS) as executor:
        futures = {executor.submit(fn): fn for fn in sources}
        for future in as_completed(futures):
            result = future.result()
            source = result.get("source", "unknown")

            if "error" in result:
                merged["sources_failed"].append(source)
                continue

            merged["sources_used"].append(source)

            for field in ("website", "facebook", "instagram", "phone", "email", "address", "opening_hours"):
                if result.get(field) and not merged[field]:
                    merged[field] = result[field]

    if on_complete:
        on_complete(business_id, merged)

    if session_id:
        try:
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(
                manager.send_update(session_id, {
                    "type": "enrichment_update",
                    "business_id": business_id,
                    "enrichment": merged,
                })
            )
            loop.close()
        except Exception as exc:
            logger.warning(f"WebSocket push failed: {exc}")

    return merged


# ─── BACKGROUND ENRICHMENT ────────────────────────────────────────────────────

def enrich_in_background(business_id, name, city, lat, lng, on_complete, session_id=None):
    thread = threading.Thread(
        target=enrich_business,
        args=(business_id, name, city, lat, lng, session_id, on_complete),
        daemon=True,
    )
    thread.start()
