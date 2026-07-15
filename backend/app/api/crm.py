from fastapi import APIRouter, Header
from app.services.auth import require_auth
from app.services.crm_pipeline import (
    get_pipeline,
    get_crm_leads,
    add_to_crm,
    update_crm_status,
    update_status,
    add_note,
    assign_lead,
)

router = APIRouter()

CRM_ROLES = ["master_admin", "admin", "back_office"]


@router.post("/crm/assign")
def assign(lead_id: str, agent_id: str, agent_name: str = "", authorization: str = Header(None)):
    """Assign a lead to a field agent. Requires admin/back_office/master_admin."""
    user, error = require_auth(authorization, CRM_ROLES)
    if error:
        return error
    return assign_lead(lead_id, agent_id, agent_name)


@router.get("/crm/pipeline")
def pipeline(authorization: str = Header(None)):
    """All auto-discovered leads (Leads page)."""
    user, error = require_auth(authorization, CRM_ROLES)
    if error:
        return error
    return get_pipeline()


@router.get("/crm/leads")
def crm_leads(authorization: str = Header(None)):
    """Only manually added CRM leads (CRM page)."""
    user, error = require_auth(authorization, CRM_ROLES)
    if error:
        return error
    return get_crm_leads()


@router.post("/crm/add")
def add_lead_to_crm(lead_id: str, notes: str = "", authorization: str = Header(None)):
    """Add existing lead to CRM pipeline."""
    user, error = require_auth(authorization, CRM_ROLES)
    if error:
        return error
    return add_to_crm(lead_id, notes)


@router.post("/crm/status")
def status(lead_id: str, new_status: str, authorization: str = Header(None)):
    """Update CRM pipeline status."""
    user, error = require_auth(authorization, CRM_ROLES)
    if error:
        return error
    return update_crm_status(lead_id, new_status)


@router.post("/crm/lead-status")
def lead_status(lead_id: str, new_status: str, authorization: str = Header(None)):
    """Update discovery lead status."""
    user, error = require_auth(authorization, CRM_ROLES)
    if error:
        return error
    return update_status(lead_id, new_status)


@router.post("/crm/note")
def note(lead_id: str, note: str, authorization: str = Header(None)):
    """Add note to lead."""
    user, error = require_auth(authorization, CRM_ROLES)
    if error:
        return error
    return add_note(lead_id, note)
