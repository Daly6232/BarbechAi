from collections import defaultdict
from datetime import datetime

from app.core.logging import get_logger
from app.database import SessionLocal, Lead, Business, Enrichment

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

    # Also update the lead's assigned_agent field if not set
    db = SessionLocal()
    try:
        lead = db.query(Lead).filter(Lead.id == lead_id).first()
        if lead and not lead.assigned_agent:
            lead.assigned_agent = agent_id
            db.commit()
    except Exception as exc:
        db.rollback()
        logger.exception(exc)
    finally:
        db.close()

    logger.info(
        f"Agent {agent_id} performed '{action}' on lead {lead_id}"
    )

    return entry


def get_agent_stats(agent_id: str):
    db = SessionLocal()

    try:
        # Get all leads assigned to this agent
        leads = db.query(Lead).filter(Lead.assigned_agent == agent_id).order_by(Lead.created_at.desc()).all()

        total_assigned = len(leads)
        contacted = sum(1 for l in leads if l.status in ("CONTACTED", "INTERESTED", "NOT_INTERESTED", "APPOINTMENT_SET"))
        interested = sum(1 for l in leads if l.status == "INTERESTED")
        appointments = sum(1 for l in leads if l.status == "APPOINTMENT_SET")

        leads_data = []

        for lead in leads:
            business = db.query(Business).filter(Business.id == lead.business_id).first()
            enrichment = db.query(Enrichment).filter(Enrichment.business_id == lead.business_id).first()

            leads_data.append({
                "id": lead.id,
                "business_id": lead.business_id,
                "name": business.name if business else "",
                "category": business.category if business else "",
                "city": business.city if business else "",
                "address": enrichment.address if enrichment and enrichment.address else (business.address if business else ""),
                "phone": enrichment.phone if enrichment else "",
                "email": enrichment.email if enrichment else "",
                "website": enrichment.website if enrichment else "",
                "facebook": enrichment.facebook if enrichment else "",
                "instagram": enrichment.instagram if enrichment else "",
                "score": lead.score,
                "opportunity_level": lead.opportunity_level,
                "status": lead.status,
                "assigned_agent": lead.assigned_agent,
                "created_at": lead.created_at.isoformat() if lead.created_at else "",
            })

        # Also count from in-memory log
        activities = AGENT_ACTIVITY[agent_id]

        log_contacted = sum(1 for a in activities if a["action"] == "CONTACTED")
        log_appointments = sum(1 for a in activities if a["action"] == "APPOINTMENT_SET")

        return {
            "agent_id": agent_id,
            "total_assigned": total_assigned,
            "contacted": contacted,
            "interested": interested,
            "appointments": appointments,
            "leads_contacted": max(contacted, log_contacted),
            "appointments_set": max(appointments, log_appointments),
            "total_actions": len(activities),
            "leads": leads_data,
        }

    except Exception as exc:
        logger.exception(exc)
        return {
            "agent_id": agent_id,
            "total_assigned": 0,
            "contacted": 0,
            "interested": 0,
            "appointments": 0,
            "leads_contacted": 0,
            "appointments_set": 0,
            "total_actions": 0,
            "leads": [],
            "error": str(exc),
        }

    finally:
        db.close()
