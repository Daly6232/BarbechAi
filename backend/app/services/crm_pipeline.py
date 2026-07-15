from datetime import datetime
from app.core.logging import get_logger
from app.core.security import generate_uuid
from app.database import (
    Business,
    CRMPipeline,
    Enrichment,
    Lead,
    SessionLocal,
)

logger = get_logger(__name__)


def _build_lead_dict(lead, business, enrichment):
    return {
        "id": lead.id,
        "business_id": lead.business_id,
        "name": business.name if business else "",
        "category": business.category if business else "",
        "city": business.city if business else "",
        "address": (
            enrichment.address if enrichment and enrichment.address
            else business.address if business else ""
        ),
        "phone": enrichment.phone if enrichment else "",
        "email": enrichment.email if enrichment else "",
        "website": enrichment.website if enrichment else "",
        "facebook": enrichment.facebook if enrichment else "",
        "instagram": enrichment.instagram if enrichment else "",
        "opening_hours": enrichment.opening_hours if enrichment else "",
        "score": lead.score,
        "opportunity_level": lead.opportunity_level,
        "status": lead.status,
        "in_crm": lead.in_crm,
        "crm_status": lead.crm_status or "NEW",
        "crm_notes": lead.crm_notes or "",
        "assigned_agent": lead.assigned_field_agent or lead.assigned_back_office or "",
        "assigned_agent_name": lead.assigned_agent_name or "",
        "created_at": lead.created_at.isoformat() if lead.created_at else "",
    }


def get_pipeline():
    """Returns all auto-discovered leads (Leads page)."""
    db = SessionLocal()
    try:
        leads = db.query(Lead).order_by(Lead.created_at.desc()).all()
        results = []
        for lead in leads:
            business = db.query(Business).filter(Business.id == lead.business_id).first()
            enrichment = db.query(Enrichment).filter(Enrichment.business_id == lead.business_id).first()
            results.append(_build_lead_dict(lead, business, enrichment))
        return {"count": len(results), "leads": results}
    except Exception as exc:
        logger.exception(exc)
        return {"count": 0, "leads": [], "error": str(exc)}
    finally:
        db.close()


def get_crm_leads():
    """Returns only leads manually added to CRM (CRM page)."""
    db = SessionLocal()
    try:
        leads = db.query(Lead).filter(Lead.in_crm == "true").order_by(Lead.created_at.desc()).all()
        results = []
        for lead in leads:
            business = db.query(Business).filter(Business.id == lead.business_id).first()
            enrichment = db.query(Enrichment).filter(Enrichment.business_id == lead.business_id).first()
            results.append(_build_lead_dict(lead, business, enrichment))
        return {"count": len(results), "leads": results}
    except Exception as exc:
        logger.exception(exc)
        return {"count": 0, "leads": [], "error": str(exc)}
    finally:
        db.close()


def add_to_crm(lead_id: str, notes: str = ""):
    """Mark an existing lead as added to CRM."""
    db = SessionLocal()
    try:
        lead = db.query(Lead).filter(Lead.id == lead_id).first()
        if not lead:
            return {"error": "Lead not found"}
        lead.in_crm = "true"
        lead.crm_status = "NEW"
        if notes:
            lead.crm_notes = notes
        pipeline = db.query(CRMPipeline).filter(CRMPipeline.lead_id == lead_id).first()
        if not pipeline:
            pipeline = CRMPipeline(
                id=generate_uuid(),
                lead_id=lead_id,
                status="NEW",
                notes=notes,
            )
            db.add(pipeline)
        db.commit()
        return {"success": True, "lead_id": lead_id}
    except Exception as exc:
        db.rollback()
        logger.exception(exc)
        return {"error": str(exc)}
    finally:
        db.close()


def update_crm_status(lead_id: str, new_status: str):
    """Update CRM pipeline status."""
    db = SessionLocal()
    try:
        lead = db.query(Lead).filter(Lead.id == lead_id).first()
        if not lead:
            return {"error": "Lead not found"}
        lead.crm_status = new_status
        pipeline = db.query(CRMPipeline).filter(CRMPipeline.lead_id == lead_id).first()
        if pipeline:
            pipeline.status = new_status
        db.commit()
        return {"success": True}
    except Exception as exc:
        db.rollback()
        logger.exception(exc)
        return {"error": str(exc)}
    finally:
        db.close()


def update_status(lead_id: str, new_status: str):
    """Update lead discovery status."""
    db = SessionLocal()
    try:
        lead = db.query(Lead).filter(Lead.id == lead_id).first()
        if not lead:
            return {"error": "Lead not found"}
        lead.status = new_status
        db.commit()
        return {"success": True}
    except Exception as exc:
        db.rollback()
        logger.exception(exc)
        return {"error": str(exc)}
    finally:
        db.close()


def assign_lead(lead_id: str, agent_id: str, agent_name: str = ""):
    """Assign a lead to a field agent. This didn't exist before —
    assigned_field_agent was a column nothing ever wrote to."""
    db = SessionLocal()
    try:
        lead = db.query(Lead).filter(Lead.id == lead_id).first()
        if not lead:
            return {"error": "Lead not found"}
        lead.assigned_field_agent = agent_id
        lead.assigned_agent_name = agent_name
        db.commit()
        return {"success": True, "lead_id": lead_id, "assigned_field_agent": agent_id}
    except Exception as exc:
        db.rollback()
        logger.exception(exc)
        return {"error": str(exc)}
    finally:
        db.close()


def add_note(lead_id: str, note: str):
    """Add a note to a lead's CRM pipeline."""
    db = SessionLocal()
    try:
        lead = db.query(Lead).filter(Lead.id == lead_id).first()
        if lead:
            timestamp = datetime.utcnow().isoformat()
            lead.crm_notes = (lead.crm_notes or "") + f"\n{timestamp}: {note}"
        pipeline = db.query(CRMPipeline).filter(CRMPipeline.lead_id == lead_id).first()
        timestamp = datetime.utcnow().isoformat()
        if pipeline:
            pipeline.notes = (pipeline.notes or "") + f"\n{timestamp}: {note}"
        else:
            pipeline = CRMPipeline(
                id=generate_uuid(),
                lead_id=lead_id,
                notes=f"{timestamp}: {note}",
            )
            db.add(pipeline)
        db.commit()
        return {"success": True}
    except Exception as exc:
        db.rollback()
        logger.exception(exc)
        return {"error": str(exc)}
    finally:
        db.close()


