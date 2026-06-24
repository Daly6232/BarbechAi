from fastapi import APIRouter
from app.services.crm_pipeline import create_lead, update_status, add_note, get_pipeline

router = APIRouter()

@router.get("/crm/pipeline")
def pipeline():
    return get_pipeline()


@router.post("/crm/create")
def create(business: dict, score: dict):
    return create_lead(business, score)


@router.post("/crm/status")
def status(lead_id: str, new_status: str):
    return update_status(lead_id, new_status)


@router.post("/crm/note")
def note(lead_id: str, note: str):
    return add_note(lead_id, note)
