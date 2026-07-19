import uuid

from app.database import SessionLocal, Business, Lead, Enrichment
from app.services.crm_pipeline import (
    export_lead_data,
    anonymize_lead,
    get_pipeline_stats,
    get_pipeline,
    get_crm_leads,
    assign_lead,
)


def _create_test_lead(name="Test Business", opportunity_level="HIGH", status="ENRICHED"):
    db = SessionLocal()
    try:
        business = Business(id=str(uuid.uuid4()), name=name, category="restaurant", city="Tunis")
        db.add(business)
        db.flush()
        enrichment = Enrichment(
            id=str(uuid.uuid4()), business_id=business.id,
            phone="+21600000000", email="biz@example.com",
        )
        db.add(enrichment)
        lead = Lead(
            id=str(uuid.uuid4()), business_id=business.id,
            score=90, opportunity_level=opportunity_level, status=status,
        )
        db.add(lead)
        db.commit()
        return lead.id
    finally:
        db.close()


# --- Import integrity ---
# This is the regression test for the actual July 2026 incident: a function
# silently disappeared from crm_pipeline.py during an edit, which passed a
# syntax check but broke `from app.services.crm_pipeline import get_pipeline`
# at server startup. Importing every expected symbol here means CI fails
# loudly on the next accidental deletion instead of only failing in prod.

def test_all_expected_functions_are_importable():
    import app.services.crm_pipeline as module
    expected = [
        "get_pipeline", "get_pipeline_stats", "get_crm_leads", "add_to_crm",
        "update_crm_status", "update_status", "add_note", "assign_lead",
        "export_lead_data", "anonymize_lead", "retention_review", "retention_purge",
    ]
    for name in expected:
        assert hasattr(module, name), f"{name} is missing from crm_pipeline module"
        assert callable(getattr(module, name))


# --- Export / erasure ---

def test_export_lead_data_includes_business_and_enrichment():
    lead_id = _create_test_lead(name="Export Test Biz")
    data = export_lead_data(lead_id)
    assert "error" not in data
    assert data["lead"]["name"] == "Export Test Biz"
    assert data["lead"]["phone"] == "+21600000000"
    assert data["legal_basis"] == "legitimate_interest_b2b"
    assert "activity_history" in data


def test_export_missing_lead_returns_error():
    data = export_lead_data("does-not-exist")
    assert "error" in data


def test_anonymize_lead_scrubs_pii():
    lead_id = _create_test_lead(name="Sensitive Biz")
    result = anonymize_lead(lead_id)
    assert result.get("success") is True

    data = export_lead_data(lead_id)
    assert data["lead"]["name"] == "[SUPPRIMÉ]"
    assert data["lead"]["phone"] is None
    assert data["lead"]["email"] is None


def test_anonymize_missing_lead_returns_error():
    result = anonymize_lead("does-not-exist")
    assert "error" in result


# --- Assignment ---

def test_assign_lead_sets_agent_name():
    lead_id = _create_test_lead(name="Assign Test Biz")
    result = assign_lead(lead_id, "agent-123", "Agent Smith")
    assert result.get("success") is True

    data = export_lead_data(lead_id)
    assert data["lead"]["assigned_agent_name"] == "Agent Smith"


# --- Aggregate stats (the pagination-badge bug fix) ---

def test_pipeline_stats_counts_across_whole_table():
    _create_test_lead(opportunity_level="HIGH", status="ENRICHED")
    _create_test_lead(opportunity_level="LOW", status="NEW")
    stats = get_pipeline_stats()
    assert stats["total"] >= 2
    assert stats["high"] >= 1
    assert stats["low"] >= 1
    # Stats must never depend on pagination — this is what broke last time.
    paginated = get_pipeline(limit=1, offset=0)
    assert stats["total"] >= paginated["total"]


def test_get_pipeline_respects_limit():
    for i in range(3):
        _create_test_lead(name=f"Paginated Biz {i}")
    result = get_pipeline(limit=2, offset=0)
    assert len(result["leads"]) <= 2
    assert result["total"] >= 3


def test_get_crm_leads_only_returns_leads_in_crm():
    lead_id = _create_test_lead(name="Not In CRM Biz")
    result = get_crm_leads(limit=500, offset=0)
    ids_in_crm = {lead["id"] for lead in result["leads"]}
    assert lead_id not in ids_in_crm
