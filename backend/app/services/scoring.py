from app.core.constants import (
    DEFAULT_BUSINESS_TYPE,
)

# ── Dynamic Category Segment Mapping ──

# Local B2C consumer-facing industries (Instagram and Facebook are highly critical)
B2C_CATEGORIES = {
    "restaurant", "café", "lounge", "fast-food", "pizzeria", "sandwicherie", 
    "snack", "pâtisserie", "boulangerie", "boucherie", "épicerie", "supermarché",
    "hôtel", "maison d'hôtes", "auberge", "résidence touristique", "salon de coiffure", 
    "institut de beauté", "spa", "hammam", "centre d'esthétique", "onglerie", 
    "bijouterie", "vêtements", "chaussures", "maroquinerie", "lingerie", "articles de sport",
    "fleuriste"
}

# Professional and B2B services (Websites, Emails, and Google Maps SEO are critical)
B2B_PROFESSIONAL = {
    "cabinet juridique", "cabinet comptable", "notaire", "société informatique", 
    "agence digitale", "cabinet d'architecture", "bureau d'études", "clinique", 
    "laboratoire d'analyses", "cabinet médical", "dentiste", "radiologie", 
    "cabinet de kinésithérapie", "assurance", "agence immobilière", "transport", "logistique"
}

# ── Segmented Weight Configurations (Must always sum to exactly 100) ──

DEFAULT_WEIGHTS = {
    "website": 30,
    "facebook": 20,
    "instagram": 20,
    "phone": 15,
    "email": 10,
    "address": 5
}

B2C_WEIGHTS = {
    "website": 20,      # Socials carry the heaviest weight for consumer discovery
    "facebook": 25,
    "instagram": 25,
    "phone": 15,
    "email": 10,
    "address": 5
}

B2B_WEIGHTS = {
    "website": 45,      # High-end web presence and formal emails are paramount
    "facebook": 10,
    "instagram": 5,
    "phone": 15,
    "email": 20,
    "address": 5
}


def _is_valid_asset(value) -> bool:
    """Helper to catch dummy values, empty fields, and API placeholders."""
    if not value:
        return False
    s = str(value).strip().lower()
    return s not in {"", "none", "null", "n/a", "undefined", "false", "unknown"}


def score_business(business: dict) -> dict:
    category = business.get("category", DEFAULT_BUSINESS_TYPE).lower().strip()

    # Select weighting profile based on category vertical
    if category in B2C_CATEGORIES:
        weights = B2C_WEIGHTS
    elif category in B2B_PROFESSIONAL:
        weights = B2B_WEIGHTS
    else:
        weights = DEFAULT_WEIGHTS

    # Sanitize digital assets presence
    has_website = _is_valid_asset(business.get("website"))
    has_facebook = _is_valid_asset(business.get("facebook"))
    has_instagram = _is_valid_asset(business.get("instagram"))
    has_phone = _is_valid_asset(business.get("phone"))
    has_email = _is_valid_asset(business.get("email"))
    has_address = _is_valid_asset(business.get("address"))

    # Clean positive math: Missing assets add to the total opportunity score
    score = 0
    if not has_website:
        score += weights["website"]
    if not has_facebook:
        score += weights["facebook"]
    if not has_instagram:
        score += weights["instagram"]
    if not has_phone:
        score += weights["phone"]
    if not has_email:
        score += weights["email"]
    if not has_address:
        score += weights["address"]

    # Generate highly actionable outbound sales pitch opportunities
    service_opportunities = []
    if not has_website:
        service_opportunities.append("website_development")
    
    if not has_facebook and not has_instagram:
        service_opportunities.append("social_media_presence_setup")
    elif not has_instagram and category in B2C_CATEGORIES:
        service_opportunities.append("instagram_marketing_growth")
        
    if not has_phone:
        service_opportunities.append("contact_info_enrichment")
    if not has_email:
        service_opportunities.append("cold_email_infrastructure")
    if not has_address:
        service_opportunities.append("google_maps_local_seo")

    # Define Opportunity Levels
    if score >= 70:
        level = "HIGH"
    elif score >= 40:
        level = "MEDIUM"
    else:
        level = "LOW"

    return {
        "score": score,
        "opportunity_level": level,
        "business_type": category,
        "has_website": has_website,
        "has_facebook": has_facebook,
        "has_instagram": has_instagram,
        "has_phone": has_phone,
        "has_email": has_email,
        "has_address": has_address,
        "service_opportunities": service_opportunities,
    }
