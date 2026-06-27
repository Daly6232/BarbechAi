from fastapi import APIRouter
from app.services.crm_pipeline import (
    get_pipeline,
    get_crm_leads,
    add_to_crm,
    update_crm_status,
    update_status,
    add_note,
    create_lead,
)

router = APIRouter()


@router.get("/crm/pipeline")
def pipeline():
    """All auto-discovered leads (Leads page)."""
    return get_pipeline()


@router.get("/crm/leads")
def crm_leads():
    """Only manually added CRM leads (CRM page)."""
    return get_crm_leads()


@router.post("/crm/add")
def add_lead_to_crm(lead_id: str, notes: str = ""):
    """Add existing lead to CRM pipeline."""
    return add_to_crm(lead_id, notes)


@router.post("/crm/status")
def status(lead_id: str, new_status: str):
    """Update CRM pipeline status."""
    return update_crm_status(lead_id, new_status)


@router.post("/crm/lead-status")
def lead_status(lead_id: str, new_status: str):
    """Update discovery lead status."""
    return update_status(lead_id, new_status)


@router.post("/crm/note")
def note(lead_id: str, note: str):
    """Add note to lead."""
    return add_note(lead_id, note)


@router.post("/crm/create")
def create(business: dict, score: dict):
    """Legacy: create lead manually."""
    return create_lead(business, score)
