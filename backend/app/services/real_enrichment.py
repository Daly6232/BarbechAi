import requests
import re
from urllib.parse import quote_plus

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; BarbechAI/1.0)"
}

def search_web(query: str):
    url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
    try:
        res = requests.get(url, headers=HEADERS, timeout=8)
        urls = re.findall(r'href="(https?://[^"&]+)"', res.text)
        clean = []
        for u in urls:
            if "duckduckgo" not in u and "bing.com" not in u:
                clean.append(u)
            if len(clean) >= 5:
                break
        return clean
    except Exception:
        return []

def enrich_business_real(name: str, city: str):
    base = f"{name} {city}"

    website_urls = search_web(f"{base} site officiel")
    facebook_urls = search_web(f"{base} facebook")
    instagram_urls = search_web(f"{base} instagram")

    website = next((u for u in website_urls
        if "facebook.com" not in u and "instagram.com" not in u), None)
    facebook = next((u for u in facebook_urls
        if "facebook.com" in u), None)
    instagram = next((u for u in instagram_urls
        if "instagram.com" in u), None)

    return {
        "website": website,
        "facebook": facebook,
        "instagram": instagram,
        "website_candidates": website_urls + facebook_urls + instagram_urls
    }
