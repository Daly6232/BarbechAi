#!/usr/bin/env python3
"""
Read-only audit: finds leads likely corrupted by the location/enrichment
bugs fixed on 2026-07-19 (city stamped from search param instead of real
coordinates; DuckDuckGo/Foursquare enrichment accepted results with no
geographic validation).

Makes ZERO writes to the database. Reuses the exact same validation
functions shipped in the fix (_resolve_real_city, _has_foreign_tld,
_looks_tunisian_phone) so the audit criteria match the fix criteria
exactly — nothing gets flagged that the fix wouldn't have caught, and
vice versa.

Usage: python3 scripts/audit_locations.py
Run this from the `backend` directory (or via Render's One-Off Jobs,
where the working directory and DATABASE_URL are already correct).
"""
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import SessionLocal, Business, Enrichment  # noqa: E402
from app.api.discover import _resolve_real_city  # noqa: E402
from app.services.enrichment_engine import _has_foreign_tld, _looks_tunisian_phone  # noqa: E402


def audit():
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

            # City mismatch: does the stored city match where the
            # coordinates actually say the business is?
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
                    "business_id": biz.id,
                    "name": biz.name,
                    "stored_city": biz.city,
                    "lat": biz.lat,
                    "lng": biz.lng,
                    "phone": phone,
                    "website": website,
                    "reasons": "; ".join(reasons),
                })

        # ── Summary ──────────────────────────────────────────────────
        print(f"\n{'=' * 60}")
        print(f"AUDIT SUMMARY")
        print(f"{'=' * 60}")
        print(f"Total businesses checked: {total}")
        print(f"Flagged as likely corrupted: {len(flagged)}")
        if total:
            print(f"Percentage: {len(flagged) / total * 100:.1f}%")

        city_only = sum(1 for f in flagged if "city_mismatch" in f["reasons"] and "non_tn_phone" not in f["reasons"] and "foreign_tld" not in f["reasons"])
        phone_flagged = sum(1 for f in flagged if "non_tn_phone" in f["reasons"])
        website_flagged = sum(1 for f in flagged if "foreign_tld" in f["reasons"])
        city_flagged = sum(1 for f in flagged if "city_mismatch" in f["reasons"])

        print(f"\nBreakdown (a lead can hit more than one):")
        print(f"  City mismatch:        {city_flagged}")
        print(f"  Non-Tunisian phone:   {phone_flagged}")
        print(f"  Foreign-TLD website:  {website_flagged}")
        print(f"{'=' * 60}\n")

        # ── Full list, CSV format for easy copy-paste ──────────────────
        if flagged:
            print("business_id,name,stored_city,lat,lng,phone,website,reasons")
            writer = csv.writer(sys.stdout)
            for f in flagged:
                writer.writerow([
                    f["business_id"], f["name"], f["stored_city"],
                    f["lat"], f["lng"], f["phone"], f["website"], f["reasons"],
                ])

        return flagged

    finally:
        db.close()


if __name__ == "__main__":
    audit()
