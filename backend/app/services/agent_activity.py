from datetime import datetime, date

from app.core.logging import get_logger
from app.core.security import generate_uuid
from app.database import SessionLocal, Lead, Business, Enrichment, AgentActivity
from app.data.tunisia_locations import LOCATIONS

logger = get_logger(__name__)

# Reverse map: "La Soukra" -> "Ariana", built once at import time.
_CITY_TO_GOVERNORATE = {
    city: gov for gov, cities in LOCATIONS.items() for city in cities
}


def _lead_to_dict(lead, business, enrichment):
    return {
        "id": lead.id,
        "business_id": lead.business_id,
        "name": business.name if business else "",
        "category": business.category if business else "",
        "city": business.city if business else "",
        "governorate": _CITY_TO_GOVERNORATE.get(business.city, "") if business else "",
        "address": enrichment.address if enrichment and enrichment.address else (business.address if business else ""),
        "phone": enrichment.phone if enrichment else "",
        "email": enrichment.email if enrichment else "",
        "website": enrichment.website if enrichment else "",
        "facebook": enrichment.facebook if enrichment else "",
        "instagram": enrichment.instagram if enrichment else "",
        "score": lead.score,
        "opportunity_level": lead.opportunity_level,
        "status": lead.status,
        "crm_status": lead.crm_status or "NEW",
        "crm_notes": lead.crm_notes or "",
        "assigned_field_agent": lead.assigned_field_agent,
        "assigned_agent_name": lead.assigned_agent_name,
        "appointment_date": lead.appointment_date.isoformat() if lead.appointment_date else None,
        "appointment_location": lead.appointment_location,
        "meeting_completed_at": lead.meeting_completed_at.isoformat() if lead.meeting_completed_at else None,
        "proposal_sent_at": lead.proposal_sent_at.isoformat() if lead.proposal_sent_at else None,
        "contract_sent_at": lead.contract_sent_at.isoformat() if lead.contract_sent_at else None,
        "deal_value": lead.deal_value,
        "decline_reason": lead.decline_reason,
        "created_at": lead.created_at.isoformat() if lead.created_at else "",
    }


def log_activity(user_id: str, lead_id: str, action: str, notes: str = "", requester_role: str = None, requester_name: str = ""):
    """Persist an agent action to the AgentActivity table (survives restarts,
    unlike the old in-memory dict this replaced)."""
    db = SessionLocal()
    try:
        entry = AgentActivity(
            id=generate_uuid(),
            agent_id=user_id,
            user_id=user_id,
            lead_id=lead_id,
            action=action,
            notes=notes,
            timestamp=datetime.utcnow(),
        )
        db.add(entry)

        # Auto-assign on first contact if nobody has claimed this lead yet —
        # but only when the actor is an actual field_agent. back_office/admin
        # users can also call this endpoint to log notes; they must never be
        # silently recorded as the lead's field agent, and the name is always
        # set together with the id so the CRM never shows a blank owner.
        lead = db.query(Lead).filter(Lead.id == lead_id).first()
        if lead and not lead.assigned_field_agent and requester_role == "field_agent":
            lead.assigned_field_agent = user_id
            lead.assigned_agent_name = requester_name

        db.commit()
        return {
            "success": True,
            "agent_id": user_id,
            "lead_id": lead_id,
            "action": action,
            "notes": notes,
            "timestamp": entry.timestamp.isoformat(),
        }
    except Exception as exc:
        db.rollback()
        logger.exception(exc)
        return {"error": str(exc)}
    finally:
        db.close()


def get_lead_activity(lead_id: str):
    """Full contact/activity timeline for a single lead — every call, note,
    and status change, with the acting user's name attached. Nothing in the
    UI surfaced this before even though it was being logged the whole time."""
    db = SessionLocal()
    try:
        from app.database import User

        rows = (
            db.query(AgentActivity, User)
            .outerjoin(User, AgentActivity.user_id == User.id)
            .filter(AgentActivity.lead_id == lead_id)
            .order_by(AgentActivity.timestamp.desc())
            .all()
        )
        return {
            "count": len(rows),
            "activity": [
                {
                    "id": activity.id,
                    "action": activity.action,
                    "notes": activity.notes or "",
                    "timestamp": activity.timestamp.isoformat() if activity.timestamp else None,
                    "agent_name": user.name if user else "Unknown",
                    "agent_role": user.role if user else None,
                }
                for activity, user in rows
            ],
        }
    except Exception as exc:
        logger.exception(exc)
        return {"count": 0, "activity": [], "error": str(exc)}
    finally:
        db.close()


def get_my_leads(user_id: str, governorate: str = None, delegation: str = None):
    """Leads assigned to this specific agent (JWT-derived id, never a free-text param).
    Optional governorate/delegation filter for sweeping one area at a time."""
    db = SessionLocal()
    try:
        leads = (
            db.query(Lead)
            .filter(Lead.assigned_field_agent == user_id)
            .order_by(Lead.created_at.desc())
            .all()
        )
        results = []
        for lead in leads:
            business = db.query(Business).filter(Business.id == lead.business_id).first()
            enrichment = db.query(Enrichment).filter(Enrichment.business_id == lead.business_id).first()
            entry = _lead_to_dict(lead, business, enrichment)
            if delegation and business and business.city != delegation:
                continue
            if governorate and entry["governorate"] != governorate:
                continue
            results.append(entry)
        return {"count": len(results), "leads": results}
    except Exception as exc:
        logger.exception(exc)
        return {"count": 0, "leads": [], "error": str(exc)}
    finally:
        db.close()


def update_agent_lead(user_id: str, lead_id: str, updates: dict, requester_role: str = None):
    """Field agent updates a lead's own lifecycle fields. Ownership-checked:
    an agent can only touch leads assigned to them, unless they're admin/master_admin."""
    db = SessionLocal()
    try:
        lead = db.query(Lead).filter(Lead.id == lead_id).first()
        if not lead:
            return {"error": "Lead not found"}

        is_privileged = requester_role in ("admin", "master_admin")
        if not is_privileged and lead.assigned_field_agent != user_id:
            return {"error": "This lead is not assigned to you"}

        allowed_fields = {
            "status", "appointment_date", "appointment_location",
            "meeting_completed_at", "proposal_sent_at", "contract_sent_at",
            "deal_value", "decline_reason", "crm_notes",
        }
        applied = {}
        for field, value in updates.items():
            if field not in allowed_fields or value is None:
                continue
            if field in ("appointment_date", "meeting_completed_at", "proposal_sent_at", "contract_sent_at"):
                try:
                    value = datetime.fromisoformat(value)
                except (ValueError, TypeError):
                    continue
            setattr(lead, field, value)
            applied[field] = updates[field]

        db.commit()

        entry = AgentActivity(
            id=generate_uuid(),
            agent_id=user_id,
            user_id=user_id,
            lead_id=lead_id,
            action=f"UPDATE:{','.join(applied.keys())}" if applied else "UPDATE:noop",
            notes="",
            timestamp=datetime.utcnow(),
        )
        db.add(entry)
        db.commit()

        return {"success": True, "applied": applied}
    except Exception as exc:
        db.rollback()
        logger.exception(exc)
        return {"error": str(exc)}
    finally:
        db.close()


def get_agent_stats(user_id: str):
    db = SessionLocal()
    try:
        leads = db.query(Lead).filter(Lead.assigned_field_agent == user_id).all()

        total_assigned = len(leads)
        contacted = sum(1 for l in leads if l.status in ("CONTACTED", "INTERESTED", "NOT_INTERESTED", "APPOINTMENT_SET"))
        interested = sum(1 for l in leads if l.status == "INTERESTED")
        appointments = sum(1 for l in leads if l.status == "APPOINTMENT_SET")
        deals_closed = sum(1 for l in leads if l.contract_sent_at is not None)
        total_deal_value = sum(l.deal_value or 0 for l in leads)

        activity_count = (
            db.query(AgentActivity).filter(AgentActivity.agent_id == user_id).count()
        )
        today_start = datetime.combine(date.today(), datetime.min.time())
        calls_today = (
            db.query(AgentActivity)
            .filter(AgentActivity.agent_id == user_id)
            .filter(AgentActivity.timestamp >= today_start)
            .filter(AgentActivity.action.in_(["CONTACTED", "NO_ANSWER", "CALLBACK", "INTERESTED", "NOT_INTERESTED"]))
            .count()
        )

        return {
            "agent_id": user_id,
            "total_assigned": total_assigned,
            "contacted": contacted,
            "interested": interested,
            "appointments": appointments,
            "deals_closed": deals_closed,
            "total_deal_value": total_deal_value,
            "total_actions": activity_count,
            "calls_today": calls_today,
        }
    except Exception as exc:
        logger.exception(exc)
        return {
            "agent_id": user_id, "total_assigned": 0, "contacted": 0,
            "interested": 0, "appointments": 0, "deals_closed": 0,
            "total_deal_value": 0, "total_actions": 0, "calls_today": 0, "error": str(exc),
        }
    finally:
        db.close()
