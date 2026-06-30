"""
Reconciliation Engine
Phase 2: Merges multi-source results with OSM data.
Handles deduplication, conflict detection, and confidence scoring.
"""

import re
from difflib import SequenceMatcher
from typing import List, Dict, Any

from app.core.logging import get_logger

logger = get_logger(__name__)

# ───────────────────────────────────────────────────────────────
# NAME NORMALIZATION
# ───────────────────────────────────────────────────────────────

def _normalize_name(name: str) -> str:
    """Normalize a business name for comparison."""
    if not name:
        return ""
    name = name.lower().strip()
    name = re.sub(r"[^\w\s]", "", name)  # Remove punctuation
    name = re.sub(r"\s+", " ", name)     # Collapse whitespace
    # Remove common filler words
    for word in ["le", "la", "les", "de", "du", "des", "el", "al", "dar"]:
        name = re.sub(rf"\b{word}\b", "", name)
    return name.strip()


def _name_similarity(name1: str, name2: str) -> float:
    """Return 0-1 similarity score between two business names."""
    n1 = _normalize_name(name1)
    n2 = _normalize_name(name2)
    if not n1 or not n2:
        return 0.0
    if n1 == n2:
        return 1.0
    return SequenceMatcher(None, n1, n2).ratio()


# ───────────────────────────────────────────────────────────────
# MERGE FIELDS
# ───────────────────────────────────────────────────────────────

def _merge_field(existing_value: str, new_value: str, source_name: str) -> tuple:
    """
    Merge a single field. Returns (merged_value, is_conflict, conflict_sources).
    Conflict = both have different non-empty values.
    """
    existing = (existing_value or "").strip()
    new = (new_value or "").strip()

    if not existing and not new:
        return ("", False, [])
    if not existing:
        return (new, False, [source_name])
    if not new:
        return (existing, False, [])
    if existing.lower() == new.lower():
        return (existing, False, [source_name])

    # Conflict: both have different values
    return (f"{existing} ⚠ {new}", True, [source_name])


def _merge_businesses(existing: Dict[str, Any], incoming: Dict[str, Any]) -> Dict[str, Any]:
    """Merge two business records from different sources. Returns merged record."""
    merged = dict(existing)
    conflicts = list(existing.get("conflict_fields", []))
    sources = list(existing.get("sources_used", [existing.get("source", "unknown")]))

    source_name = incoming.get("source", "unknown")
    if source_name not in sources:
        sources.append(source_name)

    for field in ["phone", "website", "facebook", "instagram", "email", "address", "opening_hours"]:
        existing_val = existing.get(field, "")
        incoming_val = incoming.get(field, "")
        merged_val, is_conflict, _ = _merge_field(existing_val, incoming_val, source_name)

        if merged_val and merged_val != existing_val:
            merged[field] = merged_val
        if is_conflict and field not in conflicts:
            conflicts.append(field)
        if not merged.get(field) and incoming_val:
            merged[field] = incoming_val

    # Keep best lat/lng (prefer existing if present)
    if not merged.get("lat") and incoming.get("lat"):
        merged["lat"] = incoming["lat"]
    if not merged.get("lng") and incoming.get("lng"):
        merged["lng"] = incoming["lng"]

    merged["sources_used"] = sources
    merged["conflict_fields"] = conflicts
    merged["has_conflicts"] = len(conflicts) > 0

    return merged


# ───────────────────────────────────────────────────────────────
# CONFIDENCE SCORING
# ───────────────────────────────────────────────────────────────

def _calculate_confidence(business: Dict[str, Any]) -> int:
    """
    Calculate confidence score 0-100.
    +25 per source that found this business
    +10 if phone present
    +10 if website present
    +5 if address present
    +5 if lat/lng present
    -15 per conflicting field
    Cap at 100, floor at 10.
    """
    sources = len(business.get("sources_used", []))
    conflicts = len(business.get("conflict_fields", []))

    score = sources * 25
    if business.get("phone"):
        score += 10
    if business.get("website"):
        score += 10
    if business.get("address"):
        score += 5
    if business.get("lat") and business.get("lng"):
        score += 5
    score -= conflicts * 15

    return max(10, min(100, score))


# ───────────────────────────────────────────────────────────────
# RECONCILIATION ORCHESTRATOR
# ───────────────────────────────────────────────────────────────

def reconcile(osm_results: List[Dict[str, Any]], multi_source_results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Merge OSM results with multi-source results.

    Returns:
        merged: All businesses (OSM + new discoveries), merged and deduplicated
        new_discoveries: Businesses found only by external sources
        total_sources: Count of unique sources used
    """
    if not osm_results:
        osm_results = []

    # Build index of normalized OSM names
    osm_index = {}
    for biz in osm_results:
        key = _normalize_name(biz.get("name", ""))
        if key:
            osm_index[key] = dict(biz)
            osm_index[key]["sources_used"] = ["osm"]
            osm_index[key]["conflict_fields"] = []
            osm_index[key]["has_conflicts"] = False

    merged = {k: v for k, v in osm_index.items()}
    new_discoveries = []

    # Process each multi-source result
    for ext_biz in multi_source_results:
        name = ext_biz.get("name", "")
        if not name:
            continue

        norm = _normalize_name(name)
        if not norm:
            continue

        # Try to match with existing OSM business
        matched_key = None
        best_score = 0.0

        for osm_key, osm_biz in merged.items():
            sim = _name_similarity(name, osm_biz.get("name", ""))
            if sim > best_score and sim >= 0.75:
                best_score = sim
                matched_key = osm_key

        if matched_key:
            # Merge with existing
            merged[matched_key] = _merge_businesses(merged[matched_key], ext_biz)
        else:
            # Check against other multi-source results
            ext_matched = None
            for nk, nb in enumerate(new_discoveries):
                sim = _name_similarity(name, nb.get("name", ""))
                if sim >= 0.75:
                    ext_matched = nk
                    break

            if ext_matched is not None:
                new_discoveries[ext_matched] = _merge_businesses(new_discoveries[ext_matched], ext_biz)
            else:
                # Brand new business
                ext_biz["sources_used"] = ext_biz.get("source", ["unknown"]) if isinstance(ext_biz.get("source"), list) else [ext_biz.get("source", "unknown")]
                ext_biz["conflict_fields"] = []
                ext_biz["has_conflicts"] = False
                ext_biz["is_new_discovery"] = True
                new_discoveries.append(ext_biz)

    # Calculate confidence for all
    all_businesses = list(merged.values())
    for biz in all_businesses:
        biz["confidence"] = _calculate_confidence(biz)
        biz["is_new_discovery"] = False

    for biz in new_discoveries:
        biz["confidence"] = _calculate_confidence(biz)

    # Count unique sources
    all_sources = set()
    for biz in all_businesses + new_discoveries:
        for s in biz.get("sources_used", []):
            all_sources.add(s)

    logger.info(
        "Reconciliation: %d OSM + %d new = %d total from %d sources",
        len(all_businesses), len(new_discoveries),
        len(all_businesses) + len(new_discoveries),
        len(all_sources),
    )

    return {
        "merged": all_businesses,
        "new_discoveries": new_discoveries,
        "total_sources": len(all_sources),
        "source_list": sorted(all_sources),
    }
