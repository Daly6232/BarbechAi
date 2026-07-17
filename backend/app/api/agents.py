from fastapi import APIRouter, Header
from pydantic import BaseModel
from typing import Optional

from app.services.auth import require_auth
from app.services.agent_activity import (
    log_activity,
    get_my_leads,
    update_agent_lead,
    get_agent_stats,
)
from app.data.tunisia_locations import LOCATIONS

router = APIRouter()

# field_agent can only act as themselves — identity always comes from the JWT,
# never from a client-supplied agent_id (that was the old, spoofable design).
AGENT_ROLES = ["field_agent", "back_office", "admin", "master_admin"]
STATS_ROLES = ["field_agent", "admin", "master_admin"]


class LeadUpdate(BaseModel):
    status: Optional[str] = None
    appointment_date: Optional[str] = None
    appointment_location: Optional[str] = None
    meeting_completed_at: Optional[str] = None
    proposal_sent_at: Optional[str] = None
    contract_sent_at: Optional[str] = None
    deal_value: Optional[float] = None
    decline_reason: Optional[str] = None
    crm_notes: Optional[str] = None


@router.get("/agent/locations")
def locations():
    """Governorate -> delegations, for the queue's area filter. Public within
    the app (no sensitive data), still requires no special role."""
    return {"locations": LOCATIONS}


@router.get("/agent/my-leads")
def my_leads(governorate: str = None, delegation: str = None, authorization: str = Header(None)):
    """Leads assigned to the currently authenticated agent. Scoped by JWT
    identity — an agent can never pass someone else's id to see their leads."""
    user, error = require_auth(authorization, AGENT_ROLES)
    if error:
        return error
    return get_my_leads(user["id"], governorate=governorate, delegation=delegation)


@router.post("/agent/log")
def log(lead_id: str, action: str, notes: str = "", authorization: str = Header(None)):
    user, error = require_auth(authorization, AGENT_ROLES)
    if error:
        return error
    # Only a real field_agent logging their own activity should ever trigger
    # auto-assignment. Previously back_office/admin calling this endpoint
    # (also permitted here) could silently become "assigned_field_agent" on
    # an unclaimed lead with no name attached — this is what caused leads to
    # vanish from the actual field agent's queue with a blank owner shown in CRM.
    return log_activity(user["id"], lead_id, action, notes, requester_role=user["role"], requester_name=user["name"])


@router.post("/agent/lead/{lead_id}/update")
def update_lead(lead_id: str, body: LeadUpdate, authorization: str = Header(None)):
    """Update a lead's lifecycle fields. Field agents can only touch leads
    assigned to them; admin/master_admin can update any lead."""
    user, error = require_auth(authorization, AGENT_ROLES)
    if error:
        return error
    updates = body.dict(exclude_unset=True)
    return update_agent_lead(user["id"], lead_id, updates, requester_role=user["role"])


@router.get("/agent/stats")
def stats(authorization: str = Header(None)):
    user, error = require_auth(authorization, STATS_ROLES)
    if error:
        return error
    return get_agent_stats(user["id"])


@router.get("/agent/stats/{agent_id}")
def stats_for_agent(agent_id: str, authorization: str = Header(None)):
    """Admin/master_admin can check any specific agent's workload/performance."""
    user, error = require_auth(authorization, ["admin", "master_admin"])
    if error:
        return error
    return get_agent_stats(agent_id)
