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

BLACKLIST = [
    "tiktok.com", "youtube.com", "youtu.be", "wikipedia.org",
    "wikimedia.org", "google.com", "maps.google", "goo.gl",
    "findglocal.com", "yelp.com", "tripadvisor.com", "zomato.com",
    "foursquare.com", "openstreetmap.org", "nominatim",
    "booking.com", "expedia.com", "airbnb.com", "hotels.com",
    "trustpilot.com", "yellowpages.com", "annuaire", "directory",
    "medline.tn", "tunisie-annuaire.com", "bnina.tn",
    "tunisieindustrie.nat.tn", "emploi.com", "linkedin.com",
    "twitter.com", "x.com", "snapchat.com", "pinterest.com",
]

FOURSQUARE_KEY = settings.FOURSQUARE_API_KEY


def get_headers():
    return random.choice(HEADERS_LIST)


def is_valid_website(url: str) -> bool:
    if not url:
        return False
    url_lower = url.lower()
    for blocked in BLACKLIST:
        if blocked in url_lower:
            return False
    if "facebook.com" in url_lower or "instagram.com" in url_lower:
        return False
    if "/posts/" in url_lower or "/videos/" in url_lower or "/watch" in url_lower:
        return False
    return True


def is_valid_facebook(url: str) -> bool:
    if not url or "facebook.com" not in url:
        return False
    if "/posts/" in url or "/videos/" in url or "/photo" in url:
        return False
    if "/pages/" in url.lower():
        return False
    return True


def is_valid_instagram(url: str) -> bool:
    if not url or "instagram.com" not in url:
        return False
    if url.rstrip("/") in ["https://www.instagram.com", "https://instagram.com",
                            "https://www.instagram.com/?hl=en", "https://www.instagram.com/?hl=fr"]:
        return False
    return True


# ─── SOURCE 1: Nominatim ─────────────────────────────────────────────────────

def enrich_from_osm(lat, lng):
    try:
        if not lat or not lng:
            return {"source": "osm", "error": "no_coordinates"}
        res = requests.get(
            f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lng}&format=json",
            headers={"User-Agent": settings.USER_AGENT},
            timeout=settings.REQUEST_TIMEOUT,
        )
        data = res.json()
        addr = data.get("display_name", "")
        return {"source": "osm", "address": addr}
    except Exception as e:
        logger.warning(f"Nominatim failed: {e}")
        return {"source": "osm", "error": "timeout"}


# ─── SOURCE 2: Foursquare ─────────────────────────────────────────────────────

def enrich_from_foursquare(name, city):
    try:
        if not FOURSQUARE_KEY:
            return {"source": "foursquare", "error": "no_key"}
        res = requests.get(
            "https://api.foursquare.com/v3/places/search",
            headers={"Authorization": FOURSQUARE_KEY, "Accept": "application/json"},
            params={
                "query": name,
                "near": f"{city}, Tunisia",
                "limit": 1,
                "fields": "name,location,tel,website,social_media",
            },
            timeout=settings.REQUEST_TIMEOUT,
        )
        data = res.json()
        places = data.get("results", [])
        if not places:
            return {"source": "foursquare", "error": "no_results"}
        p = places[0]
        loc = p.get("location", {})
        social = p.get("social_media", {})
        address = ", ".join(filter(None, [
            loc.get("address", ""),
            loc.get("locality", ""),
            loc.get("postcode", ""),
        ]))
        website = p.get("website", "")
        fb_id = social.get("facebook_id", "")
        facebook = f"https://www.facebook.com/{fb_id}" if fb_id else ""
        instagram = social.get("instagram", "")
        if instagram and not instagram.startswith("http"):
            instagram = f"https://www.instagram.com/{instagram}"
        return {
            "source": "foursquare",
            "phone": p.get("tel", ""),
            "address": address,
            "website": website if is_valid_website(website) else "",
            "facebook": facebook if is_valid_facebook(facebook) else "",
            "instagram": instagram if is_valid_instagram(instagram) else "",
        }
    except Exception as e:
        logger.warning(f"Foursquare enrichment failed: {e}")
        return {"source": "foursquare", "error": "timeout"}


# ─── SOURCE 3: DuckDuckGo ─────────────────────────────────────────────────────

def enrich_from_duckduckgo(name, city):
    try:
        results = {}
        with DDGS() as ddgs:
            # Website
            web = list(ddgs.text(f'"{name}" "{city}" Tunisie site officiel', max_results=5))
            for r in web:
                url = r.get("href", "")
                if is_valid_website(url):
                    results["website"] = url
                    break

            # Facebook
            fb = list(ddgs.text(f'"{name}" "{city}" site:facebook.com', max_results=5))
            for r in fb:
                url = r.get("href", "")
                if is_valid_facebook(url):
                    results["facebook"] = url
                    break

            # Instagram
            ig = list(ddgs.text(f'"{name}" "{city}" site:instagram.com', max_results=5))
            for r in ig:
                url = r.get("href", "")
                if is_valid_instagram(url):
                    results["instagram"] = url
                    break

        results["source"] = "duckduckgo"
        return results
    except Exception as e:
        logger.warning(f"DuckDuckGo failed: {e}")
        return {"source": "duckduckgo", "error": "timeout"}


# ─── SOURCE 4: Pages Jaunes TN ───────────────────────────────────────────────

def enrich_from_pagesjaunes(name, city):
    try:
        query = f"{name} {city}".replace(" ", "+")
        res = requests.get(
            f"https://www.pagesjaunes.tn/search?q={query}",
            headers=get_headers(),
            timeout=settings.REQUEST_TIMEOUT,
        )
        phones = re.findall(r"[\+216\s]?[2459]\d{7}", res.text)
        return {
            "source": "pagesjaunes",
            "phone": phones[0].strip() if phones else "",
        }
    except Exception as e:
        logger.warning(f"PagesJaunes failed: {e}")
        return {"source": "pagesjaunes", "error": "timeout"}


# ─── PARALLEL ENRICHMENT ──────────────────────────────────────────────────────

def enrich_business(business_id, name, city, lat, lng, session_id=None, on_complete=None):
    sources = [
        lambda: enrich_from_osm(lat, lng),
        lambda: enrich_from_foursquare(name, city),
        lambda: enrich_from_duckduckgo(name, city),
        lambda: enrich_from_pagesjaunes(name, city),
    ]

    merged = {
        "website": None, "facebook": None, "instagram": None,
        "phone": None, "email": None, "address": None,
        "opening_hours": None, "sources_used": [], "sources_failed": [],
        "status": "ENRICHED",
    }

    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {executor.submit(fn): fn for fn in sources}
        for future in as_completed(futures):
            result = future.result()
            source = result.get("source", "unknown")
            if "error" in result:
                merged["sources_failed"].append(source)
                continue
            merged["sources_used"].append(source)
            for field in ("website", "facebook", "instagram", "phone", "email", "address", "opening_hours"):
                val = result.get(field)
                if val and not merged[field]:
                    merged[field] = val

    if on_complete:
        on_complete(business_id, merged)

    if session_id:
        try:
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(manager.send_update(session_id, {
                "type": "enrichment_update",
                "business_id": business_id,
                "enrichment": merged,
            }))
            loop.close()
        except Exception as e:
            logger.warning(f"WebSocket push failed: {e}")

    return merged


# ─── BACKGROUND ───────────────────────────────────────────────────────────────

def enrich_in_background(business_id, name, city, lat, lng, on_complete, session_id=None):
    thread = threading.Thread(
        target=enrich_business,
        args=(business_id, name, city, lat, lng, session_id, on_complete),
        daemon=True,
    )
    thread.start()
