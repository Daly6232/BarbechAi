def score_business(business):
    """
    Simple but realistic lead scoring engine (0–100).
    """

    score = 0

    enrichment = business.get("enrichment", {})
    website = enrichment.get("website_candidates", [])

    # ------------------------
    # WEBSITE SCORE
    # ------------------------
    if not website:
        score += 40   # no website = big opportunity
    else:
        score += 10   # has some presence

    # ------------------------
    # SOCIAL SCORE (mock for now)
    # ------------------------
    has_facebook = any("facebook" in url for url in website)
    has_instagram = any("instagram" in url for url in website)

    if has_facebook:
        score += 10
    else:
        score += 5

    if has_instagram:
        score += 10
    else:
        score += 5

    # ------------------------
    # BUSINESS TYPE BONUS
    # ------------------------
    category = business.get("category", "")

    if category in ["restaurant", "cafe", "fast_food"]:
        score += 10

    # ------------------------
    # FINAL CLAMP
    # ------------------------
    score = min(100, score)

    # ------------------------
    # OPPORTUNITY LEVEL
    # ------------------------
    if score <= 40:
        level = "LOW"
    elif score <= 70:
        level = "MEDIUM"
    else:
        level = "HIGH"

    return {
        "score": score,
        "opportunity_level": level
    }
