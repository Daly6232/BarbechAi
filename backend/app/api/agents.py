from fastapi import APIRouter
from app.services.agent_activity import log_activity, get_agent_stats

router = APIRouter()

@router.post("/agent/log")
def log(agent_id: str, lead_id: str, action: str, notes: str = ""):
    return log_activity(agent_id, lead_id, action, notes)


@router.get("/agent/stats")
def stats(agent_id: str):
    return get_agent_stats(agent_id)
