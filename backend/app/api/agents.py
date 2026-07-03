from fastapi import APIRouter, Header
from app.services.auth import require_auth
from app.services.agent_activity import log_activity, get_agent_stats

router = APIRouter()

AGENT_LOG_ROLES = ["field_agent", "back_office", "admin", "master_admin"]
AGENT_STATS_ROLES = ["admin", "master_admin"]


@router.post("/agent/log")
def log(agent_id: str, lead_id: str, action: str, notes: str = "", authorization: str = Header(None)):
    user, error = require_auth(authorization, AGENT_LOG_ROLES)
    if error:
        return error
    return log_activity(agent_id, lead_id, action, notes)


@router.get("/agent/stats")
def stats(agent_id: str, authorization: str = Header(None)):
    user, error = require_auth(authorization, AGENT_STATS_ROLES)
    if error:
        return error
    return get_agent_stats(agent_id)
