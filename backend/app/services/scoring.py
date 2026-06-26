from app.core.constants import (
    DEFAULT_BUSINESS_TYPE,
)


WEBSITE_WEIGHT = 30
FACEBOOK_WEIGHT = 20
INSTAGRAM_WEIGHT = 20
PHONE_WEIGHT = 15
EMAIL_WEIGHT = 10
ADDRESS_WEIGHT = 5


def score_business(business: dict) -> dict:
    score = 0

    has_website = bool(business.get("website"))
    has_facebook = bool(business.get("facebook"))
    has_instagram = bool(business.get("instagram"))
    has_phone = bool(business.get("phone"))
    has_email = bool(business.get("email"))
    has_address = bool(business.get("address"))

    if not has_website:
        score += WEBSITE_WEIGHT
    else:
        score -= 10

    if not has_facebook:
        score += FACEBOOK_WEIGHT

    if not has_instagram:
        score += INSTAGRAM_WEIGHT

    if not has_phone:
        score += PHONE_WEIGHT

    if not has_email:
        score += EMAIL_WEIGHT

    if not has_address:
        score += ADDRESS_WEIGHT

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
        "business_type": business.get(
            "category",
            DEFAULT_BUSINESS_TYPE,
        ),
        "has_website": has_website,
        "has_facebook": has_facebook,
        "has_instagram": has_instagram,
        "has_phone": has_phone,
        "has_email": has_email,
        "has_address": has_address,
    }
