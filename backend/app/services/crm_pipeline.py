from app.database import SessionLocal, Business, Enrichment, Lead, CRMPipeline
import uuid
from datetime import datetime

def get_pipeline():
    db = SessionLocal()
    try:
        leads = db.query(Lead).order_by(Lead.created_at.desc()).all()
        results = []
        for lead in leads:
            biz = db.query(Business).filter(Business.id == lead.business_id).first()
            enrich = db.query(Enrichment).filter(Enrichment.business_id == lead.business_id).first()
            results.append({
                "id": lead.id,
                "business_id": lead.business_id,
                "name": biz.name if biz else "",
                "category": biz.category if biz else "",
                "city": biz.city if biz else "",
                "address": enrich.address or (biz.address if biz else "") if enrich else (biz.address if biz else ""),
                "phone": enrich.phone if enrich else "",
                "email": enrich.email if enrich else "",
                "website": enrich.website if enrich else "",
                "facebook": enrich.facebook if enrich else "",
                "instagram": enrich.instagram if enrich else "",
                "opening_hours": enrich.opening_hours if enrich else "",
                "score": lead.score,
                "opportunity_level": lead.opportunity_level,
                "status": lead.status,
                "assigned_agent": lead.assigned_agent,
                "created_at": lead.created_at.isoformat() if lead.created_at else "",
            })
        return {"count": len(results), "leads": results}
    except Exception as e:
        return {"count": 0, "leads": [], "error": str(e)}
    finally:
        db.close()

def create_lead(business: dict, score: dict):
    db = SessionLocal()
    try:
        lead = Lead(
            id=str(uuid.uuid4()),
            business_id=business.get("id", str(uuid.uuid4())),
            score=score.get("score", 0),
            opportunity_level=score.get("opportunity_level", "LOW"),
            status="NEW",
        )
        db.add(lead)
        db.commit()
        return {"success": True, "lead_id": lead.id}
    except Exception as e:
        db.rollback()
        return {"error": str(e)}
    finally:
        db.close()

def update_status(lead_id: str, new_status: str):
    db = SessionLocal()
    try:
        lead = db.query(Lead).filter(Lead.id == lead_id).first()
        if lead:
            lead.status = new_status
            db.commit()
            return {"success": True}
        return {"error": "Lead not found"}
    except Exception as e:
        db.rollback()
        return {"error": str(e)}
    finally:
        db.close()

def add_note(lead_id: str, note: str):
    db = SessionLocal()
    try:
        pipeline = db.query(CRMPipeline).filter(CRMPipeline.lead_id == lead_id).first()
        if pipeline:
            pipeline.notes = (pipeline.notes or "") + f"\n{datetime.utcnow().isoformat()}: {note}"
        else:
            pipeline = CRMPipeline(
                id=str(uuid.uuid4()),
                lead_id=lead_id,
                notes=f"{datetime.utcnow().isoformat()}: {note}",
            )
            db.add(pipeline)
        db.commit()
        return {"success": True}
    except Exception as e:
        db.rollback()
        return {"error": str(e)}
    finally:
        db.close()
