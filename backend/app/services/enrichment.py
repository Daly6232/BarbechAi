import requests

def enrich_business(name: str, city: str):
    """
    Lightweight enrichment placeholder (Phase 1).
    We simulate Google discovery structure first.
    """

    query_base = f"{name} {city}"

    return {
        "website_query": f"{query_base} official website",
        "facebook_query": f"{query_base} facebook",
        "instagram_query": f"{query_base} instagram"
    }
