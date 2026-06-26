ef score_business(business):
    score = 0

    has_website = bool(business.get("website"))
    has_facebook = bool(business.get("facebook"))
    has_instagram = bool(business.get("instagram"))
    has_phone = bool(business.get("phone"))
    has_email = bool(business.get("email"))
    has_address = bool(business.get("address"))

    # Missing website = high opportunity
    if not has_website:
        score += 30
    else:
        score -= 10

    # Missing Facebook
    if not has_facebook:
        score += 20

    # Missing Instagram
    if not has_instagram:
        score += 20

    # Missing phone
    if not has_phone:
        score += 15

    # Missing email
    if not has_email:
        score += 10

    # Missing address
    if not has_address:
        score += 5

    score = max(0, min(score, 100))

    if score >= 71:
        level = "HIGH"
    elif score >= 41:
        level = "MEDIUM"
    else:
        level = "LOW"

    return {
        "score": score,
        "opportunity_level": level,
        "has_website": has_website,
        "has_facebook": has_facebook,
        "has_instagram": has_instagram,
        "has_phone": has_phone,
        "has_email": has_email,
    }
