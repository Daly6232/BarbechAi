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
    {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    },
    {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
    },
    {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
    },
]

FOURSQUARE_API_KEY = settings.FOURSQUARE_API_KEY


def get_headers():
    return random.choice(HEADERS_LIST)


# ───────────────────────────────────────────────────────────────
# SOURCE 1 : OpenStreetMap Nominatim
# ───────────────────────────────────────────────────────────────

def enrich_from_osm(lat, lng):
    try:
        url = (
            "https://nominatim.openstreetmap.org/reverse"
            f"?lat={lat}&lon={lng}&format=json"
        )

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
        logger.exception(exc)
        return {"source": "osm", "error": "blocked_or_timeout"}


# ───────────────────────────────────────────────────────────────
# SOURCE 2 : Foursquare
# ───────────────────────────────────────────────────────────────

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
            params={
                "query": name,
                "near": city,
                "limit": 1,
            },
            timeout=settings.REQUEST_TIMEOUT,
        )

        results = response.json().get("results", [])

        if not results:
            return {"source": "foursquare", "error": "no_results"}

        place = results[0]

        return {
            "source": "foursquare",
            "phone": place.get("tel", ""),
            "address": ", ".join(
                place.get("location", {}).get("formatted_address", [])
            ),
            "website": place.get("website", ""),
            "facebook": "",
            "instagram": "",
        }

    except Exception as exc:
        logger.exception(exc)
        return {"source": "foursquare", "error": "blocked_or_timeout"}


# ───────────────────────────────────────────────────────────────
# SOURCE 3 : DuckDuckGo
# ───────────────────────────────────────────────────────────────

def enrich_from_duckduckgo(name, city):
    try:
        results = {}

        with DDGS() as ddgs:

            web = list(
                ddgs.text(
                    f"{name} {city} site officiel",
                    max_results=3,
                )
            )

            for item in web:
                url = item.get("href", "")
                if (
                    "facebook.com" not in url
                    and "instagram.com" not in url
                ):
                    results["website"] = url
                    break

            facebook = list(
                ddgs.text(
                    f"{name} {city} facebook",
                    max_results=3,
                )
            )

            for item in facebook:
                url = item.get("href", "")
                if "facebook.com" in url:
                    results["facebook"] = url
                    break

            instagram = list(
                ddgs.text(
                    f"{name} {city} instagram",
                    max_results=3,
                )
            )

            for item in instagram:
                url = item.get("href", "")
                if "instagram.com" in url:
                    results["instagram"] = url
                    break

        results["source"] = "duckduckgo"

        return results

    except Exception as exc:
        logger.exception(exc)
        return {"source": "duckduckgo", "error": "blocked_or_timeout"}


# ───────────────────────────────────────────────────────────────
# SOURCE 4 : Pages Jaunes Tunisia
# ───────────────────────────────────────────────────────────────

def enrich_from_pagesjaunes(name, city):
    try:
        query = f"{name} {city}".replace(" ", "+")

        response = requests.get(
            f"https://www.pagesjaunes.tn/search?q={query}",
            headers=get_headers(),
            timeout=settings.REQUEST_TIMEOUT,
        )

        phones = re.findall(
            r"[\+216\s]?[2459]\d{7}",
            response.text,
        )

        return {
            "source": "pagesjaunes",
            "phone": phones[0] if phones else "",
        }

    except Exception as exc:
        logger.exception(exc)
        return {"source": "pagesjaunes", "error": "blocked_or_timeout"}


# ───────────────────────────────────────────────────────────────
# Parallel enrichment
# ───────────────────────────────────────────────────────────────

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
        "status": "ENRICHING",
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

            for field in (
                "website",
                "facebook",
                "instagram",
                "phone",
                "email",
                "address",
                "opening_hours",
            ):
                if result.get(field) and not merged[field]:
                    merged[field] = result[field]

    # Mark as fully enriched
    merged["status"] = "ENRICHED"

    # ── WebSocket push to frontend ──
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
        except Exception as ws_exc:
            logger.warning("WebSocket push failed for %s: %s", business_id, str(ws_exc))

    # ── Callback to update database ──
    if on_complete:
        on_complete(business_id, merged)

    return merged


# ───────────────────────────────────────────────────────────────
# Background enrichment
# ───────────────────────────────────────────────────────────────

def enrich_in_background(
    business_id,
    name,
    city,
    lat,
    lng,
    on_complete,
    session_id=None,
):
    thread = threading.Thread(
        target=enrich_business,
        args=(
            business_id,
            name,
            city,
            lat,
            lng,
            session_id,
            on_complete,
        ),
        daemon=True,
    )

    thread.start()
