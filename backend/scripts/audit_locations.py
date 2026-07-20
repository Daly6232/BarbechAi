#!/usr/bin/env python3
"""
CLI wrapper around app.services.location_audit — kept for if/when Render's
One-Off Jobs (paid-tier) becomes available. For now, use the admin UI
button (Users page -> "Audit géographique") or GET /crm/location-audit
directly, since One-Off Jobs requires a paid Render plan.

Usage: python3 scripts/audit_locations.py
Run this from the `backend` directory.
"""
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.services.location_audit import run_location_audit


def main():
    result = run_location_audit(max_flagged_returned=100000)
    print(f"\n{'=' * 60}\nAUDIT SUMMARY\n{'=' * 60}")
    print(f"Total businesses checked: {result['total_checked']}")
    print(f"Flagged as likely corrupted: {result['flagged_count']}")
    print(f"Percentage: {result['flagged_percent']}%")
    print(f"\nBreakdown (a lead can hit more than one):")
    print(f"  City mismatch:        {result['city_mismatch_count']}")
    print(f"  Non-Tunisian phone:   {result['non_tn_phone_count']}")
    print(f"  Foreign-TLD website:  {result['foreign_tld_count']}")
    print(f"{'=' * 60}\n")
    if result["flagged"]:
        print("business_id,name,stored_city,lat,lng,phone,website,reasons")
        writer = csv.writer(sys.stdout)
        for f in result["flagged"]:
            writer.writerow([f["business_id"], f["name"], f["stored_city"],
                              f["lat"], f["lng"], f["phone"], f["website"], f["reasons"]])
    return result["flagged"]


if __name__ == "__main__":
    main()
