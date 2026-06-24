def score_business(business):
    score = 0

    enrichment = business.get("enrichment", {})
    websites = enrichment.get("website_candidates", [])

    # Opportunity scoring
    # Missing things = higher score

    has_website = any(
        "example.com" not in url
        and "facebook.com" not in url
        and "instagram.com" not in url
        for url in websites
    )

    has_facebook = any("facebook.com" in url for url in websites)
    has_instagram = any("instagram.com" in url for url in websites)

    if not has_website:
        score += 30

    if not has_facebook:
        score += 20

    if not has_instagram:
        score += 20

    if not business.get("address"):
        score += 15

    if not business.get("city"):
        score += 15

    score = min(score, 100)

    if score <= 30:
        level = "LOW"
    elif score <= 70:
        level = "MEDIUM"
    else:
        level = "HIGH"

    return {
        "score": score,
        "opportunity_level": level
    }
