from fastapi import APIRouter, Header
from app.services.auth import require_auth
from app.services.crm_pipeline import (
    get_pipeline,
    get_pipeline_stats,
    get_crm_leads,
    add_to_crm,
    update_crm_status,
    update_status,
    add_note,
    assign_lead,
    export_lead_data,
    anonymize_lead,
    retention_review,
    retention_purge,
)
from app.core.config import settings
from app.services.agent_activity import get_lead_activity

router = APIRouter()

CRM_ROLES = ["master_admin", "admin", "back_office"]


@router.get("/crm/lead/{lead_id}/activity")
def lead_activity(lead_id: str, authorization: str = Header(None)):
    """Full timeline of calls/notes/status changes for one lead, so managers
    can actually see who contacted whom and when."""
    user, error = require_auth(authorization, CRM_ROLES)
    if error:
        return error
    return get_lead_activity(lead_id)


@router.post("/crm/assign")
def assign(lead_id: str, agent_id: str, agent_name: str = "", authorization: str = Header(None)):
    """Assign a lead to a field agent. Requires admin/back_office/master_admin."""
    user, error = require_auth(authorization, CRM_ROLES)
    if error:
        return error
    return assign_lead(lead_id, agent_id, agent_name, requester=user)


@router.get("/crm/pipeline/stats")
def pipeline_stats(authorization: str = Header(None)):
    """True totals across the whole table, independent of pagination."""
    user, error = require_auth(authorization, CRM_ROLES)
    if error:
        return error
    return get_pipeline_stats()


@router.get("/crm/pipeline")
def pipeline(limit: int = 200, offset: int = 0, authorization: str = Header(None)):
    """All auto-discovered leads (Leads page)."""
    user, error = require_auth(authorization, CRM_ROLES)
    if error:
        return error
    return get_pipeline(limit=min(limit, 500), offset=offset)


@router.get("/crm/leads")
def crm_leads(limit: int = 200, offset: int = 0, authorization: str = Header(None)):
    """Only manually added CRM leads (CRM page)."""
    user, error = require_auth(authorization, CRM_ROLES)
    if error:
        return error
    return get_crm_leads(limit=min(limit, 500), offset=offset)


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


# --- Data privacy (GDPR-style) ---

@router.get("/crm/lead/{lead_id}/export")
def lead_export(lead_id: str, authorization: str = Header(None)):
    """Full record for one lead — data portability."""
    user, error = require_auth(authorization, CRM_ROLES)
    if error:
        return error
    return export_lead_data(lead_id)


@router.post("/crm/lead/{lead_id}/anonymize")
def lead_anonymize(lead_id: str, authorization: str = Header(None)):
    """Right-to-erasure for one lead. Admin/master_admin only — this is
    irreversible."""
    user, error = require_auth(authorization, ["admin", "master_admin"])
    if error:
        return error
    return anonymize_lead(lead_id, requester=user)


@router.get("/crm/retention-review")
def get_retention_review(authorization: str = Header(None)):
    """Lost leads past the retention window, awaiting a human decision."""
    user, error = require_auth(authorization, ["admin", "master_admin"])
    if error:
        return error
    return retention_review(settings.LOST_LEAD_RETENTION_DAYS)


@router.post("/crm/retention-purge")
def post_retention_purge(lead_ids: str, authorization: str = Header(None)):
    """Bulk-anonymize a reviewed list of retention candidates.
    lead_ids is a comma-separated string of lead ids (query param)."""
    user, error = require_auth(authorization, ["admin", "master_admin"])
    if error:
        return error
    ids = [i.strip() for i in lead_ids.split(",") if i.strip()]
    return retention_purge(ids, requester=user)
