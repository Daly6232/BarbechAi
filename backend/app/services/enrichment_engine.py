import os
import random
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from ddgs import DDGS
import requests

HEADERS_LIST = [
    {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"},
    {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"},
    {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"},
]

FOURSQUARE_API_KEY = os.environ.get("FOURSQUARE_API_KEY", "")

def get_headers():
    return random.choice(HEADERS_LIST)

# ─── SOURCE 1: OSM TAGS ───────────────────────────────────────────────────────
def enrich_from_osm(lat, lng):
    try:
        url = f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lng}&format=json"
        res = requests.get(url, headers={"User-Agent": "BarbechAI/1.0"}, timeout=5)
        data = res.json()
        address = data.get("display_name", "")
        return {"source": "osm", "address": address}
    except:
        return {"source": "osm", "error": "blocked_or_timeout"}

# ─── SOURCE 2: FOURSQUARE ─────────────────────────────────────────────────────
def enrich_from_foursquare(name, city):
    try:
        if not FOURSQUARE_API_KEY:
            return {"source": "foursquare", "error": "no_key"}
        url = "https://api.foursquare.com/v3/places/search"
        headers = {
            "Authorization": FOURSQUARE_API_KEY,
            "Accept": "application/json"
        }
        params = {"query": name, "near": city, "limit": 1}
        res = requests.get(url, headers=headers, params=params, timeout=5)
        data = res.json()
        results = data.get("results", [])
        if not results:
            return {"source": "foursquare", "error": "no_results"}
        place = results[0]
        return {
            "source": "foursquare",
            "phone": place.get("tel", ""),
            "address": ", ".join(place.get("location", {}).get("formatted_address", [])),
            "website": place.get("website", ""),
            "facebook": "",
            "instagram": "",
        }
    except:
        return {"source": "foursquare", "error": "blocked_or_timeout"}

# ─── SOURCE 3: DUCKDUCKGO ─────────────────────────────────────────────────────
def enrich_from_duckduckgo(name, city):
    try:
        results = {}
        with DDGS() as ddgs:
            # Website
            web = list(ddgs.text(f"{name} {city} site officiel", max_results=3))
            for r in web:
                url = r.get("href", "")
                if "facebook.com" not in url and "instagram.com" not in url:
                    results["website"] = url
                    break
            # Facebook
            fb = list(ddgs.text(f"{name} {city} facebook", max_results=3))
            for r in fb:
                url = r.get("href", "")
                if "facebook.com" in url:
                    results["facebook"] = url
                    break
            # Instagram
            ig = list(ddgs.text(f"{name} {city} instagram", max_results=3))
            for r in ig:
                url = r.get("href", "")
                if "instagram.com" in url:
                    results["instagram"] = url
                    break
        results["source"] = "duckduckgo"
        return results
    except:
        return {"source": "duckduckgo", "error": "blocked_or_timeout"}

# ─── SOURCE 4: PAGES JAUNES TN ───────────────────────────────────────────────
def enrich_from_pagesjaunes(name, city):
    try:
        query = f"{name} {city}".replace(" ", "+")
        url = f"https://www.pagesjaunes.tn/search?q={query}"
        res = requests.get(url, headers=get_headers(), timeout=5)
        import re
        phones = re.findall(r'[\+216\s]?[2459]\d{7}', res.text)
        return {
            "source": "pagesjaunes",
            "phone": phones[0] if phones else ""
        }
    except:
        return {"source": "pagesjaunes", "error": "blocked_or_timeout"}

# ─── PARALLEL ENRICHMENT ──────────────────────────────────────────────────────
def enrich_business(business_id, name, city, lat, lng, on_complete=None):
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
        "address": None,
        "sources_used": [],
        "sources_failed": [],
    }

    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {executor.submit(fn): fn for fn in sources}
        for future in as_completed(futures):
            result = future.result()
            source = result.get("source", "unknown")
            if "error" in result:
                merged["sources_failed"].append(source)
            else:
                merged["sources_used"].append(source)
                if result.get("website") and not merged["website"]:
                    merged["website"] = result["website"]
                if result.get("facebook") and not merged["facebook"]:
                    merged["facebook"] = result["facebook"]
                if result.get("instagram") and not merged["instagram"]:
                    merged["instagram"] = result["instagram"]
                if result.get("phone") and not merged["phone"]:
                    merged["phone"] = result["phone"]
                if result.get("address") and not merged["address"]:
                    merged["address"] = result["address"]

    if on_complete:
        on_complete(business_id, merged)

    return merged

# ─── BACKGROUND ENRICHMENT ────────────────────────────────────────────────────
def enrich_in_background(business_id, name, city, lat, lng, on_complete):
    thread = threading.Thread(
        target=enrich_business,
        args=(business_id, name, city, lat, lng, on_complete),
        daemon=True
    )
    thread.start()
