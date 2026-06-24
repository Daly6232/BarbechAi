from datetime import datetime

AGENT_ACTIVITY = {}

def log_activity(agent_id: str, lead_id: str, action: str, notes: str = ""):
    entry = {
        "agent_id": agent_id,
        "lead_id": lead_id,
        "action": action,
        "notes": notes,
        "timestamp": datetime.utcnow().isoformat()
    }

    if agent_id not in AGENT_ACTIVITY:
        AGENT_ACTIVITY[agent_id] = []

    AGENT_ACTIVITY[agent_id].append(entry)

    return entry


def get_agent_stats(agent_id: str):
    activities = AGENT_ACTIVITY.get(agent_id, [])

    leads_contacted = len([a for a in activities if a["action"] == "CONTACTED"])
    appointments = len([a for a in activities if a["action"] == "APPOINTMENT_SET"])

    return {
        "agent_id": agent_id,
        "leads_contacted": leads_contacted,
        "appointments_set": appointments,
        "total_actions": len(activities)
    }
