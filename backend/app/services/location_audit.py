"""
Read-only audit: finds leads likely corrupted by the location/enrichment
bugs fixed on 2026-07-19 (city stamped from search param instead of real
coordinates; DuckDuckGo/Foursquare enrichment accepted results with no
geographic validation).

Makes ZERO writes to the database. Reuses the exact same validation
functions shipped in the fix, so the audit criteria match the fix criteria
exactly.

This lives in app/services (not just scripts/) so it's importable from an
API endpoint — Render's One-Off Jobs turned out to require a paid plan,
which this account isn't on, so scripts/audit_locations.py alone wasn't
reachable. The CLI script now just calls this.
"""
from app.database import SessionLocal, Business, Enrichment
from app.api.discover import _resolve_real_city
from app.services.enrichment_engine import _has_foreign_tld, _looks_tunisian_phone


def run_location_audit(max_flagged_returned: int = 1000):
    db = SessionLocal()
    try:
        rows = (
            db.query(Business, Enrichment)
            .outerjoin(Enrichment, Enrichment.business_id == Business.id)
            .all()
        )
        total = len(rows)
        flagged = []
        for biz, enr in rows:
            reasons = []
            if biz.lat is not None and biz.lng is not None:
                resolved = _resolve_real_city(biz.lat, biz.lng, biz.city)
                if resolved != biz.city:
                    reasons.append(f"city_mismatch(stored={biz.city!r}, resolved={resolved!r})")
            phone = (enr.phone if enr else "") or ""
            if phone and not _looks_tunisian_phone(phone):
                reasons.append(f"non_tn_phone({phone!r})")
            website = (enr.website if enr else "") or ""
            if website and _has_foreign_tld(website):
                reasons.append(f"foreign_tld_website({website!r})")
            if reasons:
                flagged.append({
                    "business_id": biz.id, "name": biz.name, "stored_city": biz.city,
                    "lat": biz.lat, "lng": biz.lng, "phone": phone,
                    "website": website, "reasons": "; ".join(reasons),
                })

        phone_flagged = sum(1 for f in flagged if "non_tn_phone" in f["reasons"])
        website_flagged = sum(1 for f in flagged if "foreign_tld" in f["reasons"])
        city_flagged = sum(1 for f in flagged if "city_mismatch" in f["reasons"])

        return {
            "total_checked": total,
            "flagged_count": len(flagged),
            "flagged_percent": round(len(flagged) / total * 100, 1) if total else 0,
            "city_mismatch_count": city_flagged,
            "non_tn_phone_count": phone_flagged,
            "foreign_tld_count": website_flagged,
            "flagged": flagged[:max_flagged_returned],
            "truncated": len(flagged) > max_flagged_returned,
        }
    finally:
        db.close()
