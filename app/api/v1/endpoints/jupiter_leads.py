# from fastapi import APIRouter
# from app.services.lead_generation_services import LeadGenerator

# router = APIRouter()
# lead_generator = LeadGenerator()

# @router.get("/generate_daily_leads")
# async def generate_daily_leads():
#     leads = await lead_generator.generate_all_leads()

#     return {
#         "status": "success",
#         "total_leads": len(leads),
#         "leads": leads
#     }


from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.lead_generation_services import LeadGenerator
from app.services.lead_storage_services import LeadStorageService

router = APIRouter()
lead_generator = LeadGenerator()
lead_storage = LeadStorageService()

class UpdateLeadStatusRequest(BaseModel):
    status: str  # "not contacted" or "connected"

@router.get("/generate_daily_leads")
async def generate_daily_leads():
    """
    Analyze recent chat history, refresh the persisted 24-hour lead bucket,
    and return the currently active daily leads.
    """
    await lead_generator.generate_all_leads()
    await lead_storage.init_db()
    await lead_storage.delete_expired_daily_leads()
    leads = await lead_storage.get_active_daily_leads()

    return {
        "status": "success",
        "total_leads": len(leads),
        "leads": leads
    }

@router.get("/daily_leads")
async def get_daily_leads():
    """
    Get the currently active daily leads that have not expired yet.
    """
    await lead_storage.init_db()
    await lead_storage.delete_expired_daily_leads()
    leads = await lead_storage.get_active_daily_leads()

    return {
        "status": "success",
        "total_leads": len(leads),
        "leads": leads
    }

@router.get("/leads")
async def get_all_leads():
    """
    Get all leads from database
    """
    await lead_storage.init_db()
    leads = await lead_storage.get_all_leads()
    
    return {
        "status": "success",
        "total_leads": len(leads),
        "leads": leads
    }

@router.get("/leads/{lead_id}")
async def get_lead(lead_id: int):
    """
    Get a specific lead by ID
    """
    await lead_storage.init_db()
    lead = await lead_storage.get_lead_by_id(lead_id)
    
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    return {
        "status": "success",
        "lead": lead
    }

@router.patch("/leads/{lead_id}/status")
async def update_lead_status(lead_id: int, request: UpdateLeadStatusRequest):
    """
    Update the status of a lead manually.
    Status can be 'not contacted' or 'contacted'
    """
    await lead_storage.init_db()
    
    # Validate status
    if request.status not in ["not contacted", "contacted"]:
        raise HTTPException(
            status_code=400, 
            detail="Status must be 'not contacted' or 'contacted'"
        )
    
    try:
        updated_lead = await lead_storage.update_lead_status(lead_id, request.status)
        
        if not updated_lead:
            raise HTTPException(status_code=404, detail="Lead not found")
        
        return {
            "status": "success",
            "message": f"Lead status updated to '{request.status}'",
            "lead": updated_lead
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")

@router.get("/leads/user/{user_id}")
async def get_user_leads(user_id: str):
    """
    Get all leads for a specific user
    """
    await lead_storage.init_db()
    leads = await lead_storage.get_leads_by_user(user_id)
    
    return {
        "status": "success",
        "user_id": user_id,
        "total_leads": len(leads),
        "leads": leads
    }
