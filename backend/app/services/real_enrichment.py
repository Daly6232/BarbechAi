import requests
import re

def extract_official_links(text):
    """
    Very simple heuristic extractor for now.
    Later we replace with Google/SerpAPI.
    """

    urls = re.findall(r"https?://[^\s]+", text)
    return urls[:5]


def mock_google_search(query: str):
    """
    Placeholder for real search engine integration.
    This simulates future Google/SerpAPI response format.
    """

    return {
        "query": query,
        "results": [
            f"https://example.com/{query.replace(' ', '-')}",
            f"https://facebook.com/{query.replace(' ', '-')}",
            f"https://instagram.com/{query.replace(' ', '-')}"
        ]
    }


def enrich_business_real(name: str, city: str):

    query = f"{name} {city}"

    search_result = mock_google_search(query)

    return {
        "query": query,
        "website_candidates": search_result["results"]
    }
