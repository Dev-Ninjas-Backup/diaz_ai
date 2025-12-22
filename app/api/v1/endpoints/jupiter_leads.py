from fastapi import APIRouter
from app.services.lead_generation_services import LeadGenerator

router = APIRouter()
lead_generator = LeadGenerator()

@router.get("/generate_daily_leads")
async def generate_daily_leads():
    leads = await lead_generator.generate_all_leads()

    return {
        "status": "success",
        "total_leads": len(leads),
        "leads": leads
    }
