import re
from urllib.parse import quote_plus

import requests

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


HEADERS = {
    "User-Agent": settings.USER_AGENT,
}


def search_web(query: str):
    url = (
        "https://html.duckduckgo.com/html/"
        f"?q={quote_plus(query)}"
    )

    try:
        response = requests.get(
            url,
            headers=HEADERS,
            timeout=settings.REQUEST_TIMEOUT,
        )

        urls = re.findall(
            r'href="(https?://[^"&]+)"',
            response.text,
        )

        results = []

        for url in urls:

            if (
                "duckduckgo" in url
                or "bing.com" in url
            ):
                continue

            results.append(url)

            if len(results) >= 5:
                break

        return results

    except Exception as exc:
        logger.exception(exc)
        return []


def enrich_business_real(
    name: str,
    city: str,
):
    base = f"{name} {city}"

    logger.info(
        f"Running real enrichment for '{base}'"
    )

    website_urls = search_web(
        f"{base} site officiel"
    )

    facebook_urls = search_web(
        f"{base} facebook"
    )

    instagram_urls = search_web(
        f"{base} instagram"
    )

    website = next(
        (
            url
            for url in website_urls
            if "facebook.com" not in url
            and "instagram.com" not in url
        ),
        None,
    )

    facebook = next(
        (
            url
            for url in facebook_urls
            if "facebook.com" in url
        ),
        None,
    )

    instagram = next(
        (
            url
            for url in instagram_urls
            if "instagram.com" in url
        ),
        None,
    )

    return {
        "website": website,
        "facebook": facebook,
        "instagram": instagram,
        "website_candidates": (
            website_urls
            + facebook_urls
            + instagram_urls
        ),
    }
