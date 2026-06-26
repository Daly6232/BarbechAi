from collections import defaultdict
from datetime import datetime

from app.core.logging import get_logger

logger = get_logger(__name__)

AGENT_ACTIVITY = defaultdict(list)


def log_activity(
    agent_id: str,
    lead_id: str,
    action: str,
    notes: str = "",
):
    entry = {
        "agent_id": agent_id,
        "lead_id": lead_id,
        "action": action,
        "notes": notes,
        "timestamp": datetime.utcnow().isoformat(),
    }

    AGENT_ACTIVITY[agent_id].append(entry)

    logger.info(
        f"Agent {agent_id} performed '{action}' on lead {lead_id}"
    )

    return entry


def get_agent_stats(agent_id: str):
    activities = AGENT_ACTIVITY[agent_id]

    leads_contacted = sum(
        1
        for activity in activities
        if activity["action"] == "CONTACTED"
    )

    appointments = sum(
        1
        for activity in activities
        if activity["action"] == "APPOINTMENT_SET"
    )

    return {
        "agent_id": agent_id,
        "leads_contacted": leads_contacted,
        "appointments_set": appointments,
        "total_actions": len(activities),
    }
