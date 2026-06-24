from datetime import datetime

# In-memory pipeline store (we'll move to PostgreSQL later)
PIPELINE = {}

STATUS_FLOW = [
    "NEW",
    "CONTACTED",
    "INTERESTED",
    "NOT_INTERESTED",
    "APPOINTMENT_SET",
    "APPOINTMENT_DONE",
    "RESCHEDULED",
    "CLOSED"
]


def create_lead(business, score_data):
    lead_id = f"lead_{len(PIPELINE) + 1}"

    PIPELINE[lead_id] = {
        "id": lead_id,
        "business": business,
        "score": score_data,
        "status": "NEW",
        "assigned_agent": None,
        "notes": [],
        "created_at": datetime.utcnow().isoformat()
    }

    return PIPELINE[lead_id]


def update_status(lead_id, new_status):
    if lead_id not in PIPELINE:
        return {"error": "lead not found"}

    if new_status not in STATUS_FLOW:
        return {"error": "invalid status"}

    PIPELINE[lead_id]["status"] = new_status
    PIPELINE[lead_id]["updated_at"] = datetime.utcnow().isoformat()

    return PIPELINE[lead_id]


def add_note(lead_id, note):
    if lead_id not in PIPELINE:
        return {"error": "lead not found"}

    PIPELINE[lead_id]["notes"].append({
        "text": note,
        "time": datetime.utcnow().isoformat()
    })

    return PIPELINE[lead_id]


def get_pipeline():
    return list(PIPELINE.values())
