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


def export_lead_data(lead_id: str):
    """Full record for one lead — data portability. Includes everything
    held about this business/contact: profile, enrichment, pipeline status,
    and the complete activity/contact history."""
    db = SessionLocal()
    try:
        from app.database import AgentActivity, User

        lead = db.query(Lead).filter(Lead.id == lead_id).first()
        if not lead:
            return {"error": "Lead not found"}
        business = db.query(Business).filter(Business.id == lead.business_id).first()
        enrichment = db.query(Enrichment).filter(Enrichment.business_id == lead.business_id).first()
        activity_rows = (
            db.query(AgentActivity, User)
            .outerjoin(User, AgentActivity.user_id == User.id)
            .filter(AgentActivity.lead_id == lead_id)
            .order_by(AgentActivity.timestamp.asc())
            .all()
        )

        return {
            "export_generated_at": datetime.utcnow().isoformat(),
            "lead": _build_lead_dict(lead, business, enrichment),
            "legal_basis": getattr(business, "data_basis", None) or "legitimate_interest_b2b",
            "pipeline_stage_history": {
                "current_status": lead.status,
                "current_crm_status": lead.crm_status,
                "confirmed_by": lead.confirmed_by,
                "confirmed_at": lead.confirmed_at.isoformat() if lead.confirmed_at else None,
            },
            "activity_history": [
                {
                    "action": a.action,
                    "notes": a.notes or "",
                    "timestamp": a.timestamp.isoformat() if a.timestamp else None,
                    "by": u.name if u else "Unknown",
                }
                for a, u in activity_rows
            ],
        }
    except Exception as exc:
        logger.exception(exc)
        return {"error": str(exc)}
    finally:
        db.close()


def anonymize_lead(lead_id: str, requester: dict = None):
    """Right-to-erasure for a single lead: scrubs personally-identifying
    contact fields (name, phone, email, socials, address, notes) while
    leaving the pipeline-stage/score/audit skeleton intact, so aggregate
    pipeline stats and past audit entries don't silently corrupt."""
    db = SessionLocal()
    try:
        lead = db.query(Lead).filter(Lead.id == lead_id).first()
        if not lead:
            return {"error": "Lead not found"}
        business = db.query(Business).filter(Business.id == lead.business_id).first()
        enrichment = db.query(Enrichment).filter(Enrichment.business_id == lead.business_id).first()

        if business:
            business.name = "[SUPPRIMÉ]"
            business.address = None
        if enrichment:
            enrichment.phone = None
            enrichment.email = None
            enrichment.website = None
            enrichment.facebook = None
            enrichment.instagram = None
            enrichment.address = None
        lead.crm_notes = "[Données personnelles supprimées]"
        lead.client_requests = None
        db.commit()

        from app.services.audit import log_audit_event
        log_audit_event("LEAD_ANONYMIZED", actor=requester, target_type="lead", target_id=lead_id)
        return {"success": True, "lead_id": lead_id}
    except Exception as exc:
        db.rollback()
        logger.exception(exc)
        return {"error": str(exc)}
    finally:
        db.close()


def retention_review(days: int):
    """Leads sitting in LOST status older than the retention window, not
    yet anonymized — surfaced for a human to review/act on, never
    auto-deleted silently."""
    from datetime import timedelta
    cutoff = datetime.utcnow() - timedelta(days=days)
    db = SessionLocal()
    try:
        candidates = (
            db.query(Lead)
            .filter(Lead.crm_status == "LOST")
            .filter(Lead.created_at < cutoff)
            .filter(Lead.crm_notes != "[Données personnelles supprimées]")
            .all()
        )
        results = []
        for lead in candidates:
            business = db.query(Business).filter(Business.id == lead.business_id).first()
            results.append({
                "lead_id": lead.id,
                "name": business.name if business else "",
                "created_at": lead.created_at.isoformat() if lead.created_at else None,
            })
        return {"count": len(results), "candidates": results, "retention_days": days}
    finally:
        db.close()


def retention_purge(lead_ids: list, requester: dict = None):
    """Bulk-anonymize a reviewed list of retention candidates."""
    results = [anonymize_lead(lid, requester=requester) for lid in lead_ids]
    succeeded = sum(1 for r in results if r.get("success"))
    return {"success": True, "anonymized": succeeded, "requested": len(lead_ids)}
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


def assign_lead(lead_id: str, agent_id: str, agent_name: str = "", requester: dict = None):
    """Assign a lead to a field agent. This didn't exist before —
    assigned_field_agent was a column nothing ever wrote to."""
    db = SessionLocal()
    try:
        lead = db.query(Lead).filter(Lead.id == lead_id).first()
        if not lead:
            return {"error": "Lead not found"}
        previous_agent = lead.assigned_agent_name
        lead.assigned_field_agent = agent_id
        lead.assigned_agent_name = agent_name
        db.commit()
        from app.services.audit import log_audit_event
        log_audit_event("LEAD_REASSIGNED", actor=requester, target_type="lead", target_id=lead_id,
                         details=f"{previous_agent or 'unassigned'} -> {agent_name or agent_id}")
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


