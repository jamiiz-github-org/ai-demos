"""Lead capture route."""
import logging

from fastapi import APIRouter, HTTPException

from app.schemas.leads import LeadRequest, LeadResponse
from app.services.lead_service import save_lead

logger = logging.getLogger("jamiiz.routes.leads")
router = APIRouter(prefix="/leads", tags=["leads"])


@router.post("", response_model=LeadResponse)
async def capture_lead(body: LeadRequest) -> LeadResponse:
    try:
        lead_id = save_lead(
            email=body.email,
            name=body.name,
            business=body.business,
            pain_point=body.pain_point,
            hours_saved=body.hours_saved,
            assistant=body.assistant,
            session_id=body.session_id,
        )
        return LeadResponse(id=lead_id)
    except Exception as exc:
        logger.exception("Failed to save lead")
        raise HTTPException(status_code=500, detail=str(exc))
