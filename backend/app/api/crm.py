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
    set_follow_up,
    get_followups,
)
from app.core.config import settings
from app.services.agent_activity import get_lead_activity
from app.services.location_audit import run_location_audit
from app.services.reports import conversion_and_revenue_trends, agent_leaderboard

router = APIRouter()

CRM_ROLES = ["master_admin", "admin", "back_office"]


@router.post("/crm/lead/{lead_id}/follow-up")
def follow_up(lead_id: str, next_action: str, callback_date: str = None, authorization: str = Header(None)):
    """Set the next action + due date for a lead."""
    user, error = require_auth(authorization, CRM_ROLES)
    if error:
        return error
    return set_follow_up(lead_id, next_action, callback_date, requester=user)


@router.get("/crm/followups")
def followups(overdue_only: bool = False, agent_id: str = None, authorization: str = Header(None)):
    """Pending follow-ups, optionally filtered to overdue and/or one agent."""
    user, error = require_auth(authorization, CRM_ROLES + ["field_agent"])
    if error:
        return error
    return get_followups(overdue_only=overdue_only, agent_id=agent_id)


@router.get("/reports/trends")
def report_trends(months: int = 6, authorization: str = Header(None)):
    user, error = require_auth(authorization, ["admin", "master_admin"])
    if error:
        return error
    return conversion_and_revenue_trends(months=min(months, 24))


@router.get("/reports/leaderboard")
def report_leaderboard(authorization: str = Header(None)):
    user, error = require_auth(authorization, ["admin", "master_admin"])
    if error:
        return error
    return agent_leaderboard()


@router.get("/crm/location-audit")
def location_audit(authorization: str = Header(None)):
    """Read-only: flags leads likely corrupted by the city/phone/website
    validation bugs fixed 2026-07-19. Makes zero writes. master_admin only —
    added because Render's One-Off Jobs (the normal way to run this) turned
    out to require a paid plan this account doesn't have."""
    user, error = require_auth(authorization, ["master_admin"])
    if error:
        return error
    return run_location_audit()


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
