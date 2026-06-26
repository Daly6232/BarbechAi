from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


def enrich_business(name: str, city: str):
    """
    Lightweight enrichment placeholder.

    This service builds standardized search queries that
    future enrichment providers (DuckDuckGo, Google,
    HERE, Foursquare, etc.) can consume.
    """

    query_base = f"{name} {city}".strip()

    logger.info(
        f"Preparing enrichment queries for '{query_base}'"
    )

    return {
        "business": name,
        "city": city,
        "queries": {
            "website": f"{query_base} official website",
            "facebook": f"{query_base} facebook",
            "instagram": f"{query_base} instagram",
            "phone": f"{query_base} phone",
            "email": f"{query_base} email",
        },
        "timeout": settings.REQUEST_TIMEOUT,
        "user_agent": settings.USER_AGENT,
    }
