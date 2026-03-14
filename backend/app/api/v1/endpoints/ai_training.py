"""
AI Training API Endpoints
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api import deps
from app.models.models import User, Business
from app.services.ai_training_service import ai_training_service

router = APIRouter()


# Pydantic schemas
class TrainingScenarioCreate(BaseModel):
    title: str
    user_input: str
    expected_response: str
    description: Optional[str] = None
    category: Optional[str] = "general_inquiry"


class TrainingScenarioUpdate(BaseModel):
    title: Optional[str] = None
    user_input: Optional[str] = None
    expected_response: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    is_active: Optional[bool] = None


class TrainingScenarioResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    category: str
    user_input: str
    expected_response: str
    is_active: bool
    success_rate: Optional[float]
    last_tested: Optional[str]
    created_at: str
    
    class Config:
        from_attributes = True


# Endpoints
@router.get("/")
async def list_scenarios(
    category: Optional[str] = None,
    is_active: Optional[bool] = None,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> List[TrainingScenarioResponse]:
    """List all training scenarios for the user's business"""
    
    business_id = await deps.get_current_business_id(current_user, db)
    scenarios = await ai_training_service.list_scenarios(
        db, business_id, category, is_active
    )
    
    return [
        TrainingScenarioResponse(
            id=s.id,
            title=s.title,
            description=s.description,
            category=s.category,
            user_input=s.user_input,
            expected_response=s.expected_response,
            is_active=s.is_active,
            success_rate=float(s.success_rate) if s.success_rate else None,
            last_tested=s.last_tested.isoformat() if s.last_tested else None,
            created_at=s.created_at.isoformat() if s.created_at else ""
        )
        for s in scenarios
    ]


@router.post("/")
async def create_scenario(
    scenario: TrainingScenarioCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> TrainingScenarioResponse:
    """Create a new training scenario"""
    
    business_id = await deps.get_current_business_id(current_user, db)
    
    new_scenario = await ai_training_service.create_scenario(
        db=db,
        business_id=business_id,
        title=scenario.title,
        user_input=scenario.user_input,
        expected_response=scenario.expected_response,
        description=scenario.description,
        category=scenario.category
    )
    
    return TrainingScenarioResponse(
        id=new_scenario.id,
        title=new_scenario.title,
        description=new_scenario.description,
        category=new_scenario.category,
        user_input=new_scenario.user_input,
        expected_response=new_scenario.expected_response,
        is_active=new_scenario.is_active,
        success_rate=None,
        last_tested=None,
        created_at=new_scenario.created_at.isoformat() if new_scenario.created_at else ""
    )


@router.get("/statistics")
async def get_statistics(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """Get training statistics"""
    
    business_id = await deps.get_current_business_id(current_user, db)
    return await ai_training_service.get_statistics(db, business_id)


@router.post("/test/{scenario_id}")
async def test_scenario(
    scenario_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """Test a single training scenario"""
    
    business_id = await deps.get_current_business_id(current_user, db)
    
    # Get business context for the AI
    business = db.query(Business).filter(Business.id == business_id).first()
    
    business_context = {
        "name": business.name if business else "Demo Business",
        "hours": "9 AM to 5 PM",
        "services": ["consultation", "support"]
    }
    
    return await ai_training_service.test_scenario(
        db, scenario_id, business_id, business_context
    )


@router.post("/test-all")
async def test_all_scenarios(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """Test all active training scenarios"""
    
    business_id = await deps.get_current_business_id(current_user, db)
    
    # Get business context
    business = db.query(Business).filter(Business.id == business_id).first()
    
    business_context = {
        "name": business.name if business else "Demo Business",
        "hours": "9 AM to 5 PM",
        "services": ["consultation", "support"]
    }
    
    return await ai_training_service.test_all_scenarios(
        db, business_id, business_context
    )


@router.post("/generate")
async def generate_scenarios(
    count: int = 5,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> List[TrainingScenarioResponse]:
    """Generate synthetic training scenarios based on business context"""
    
    business_id = await deps.get_current_business_id(current_user, db)
    
    # Cap count to avoid abuse/timeout
    count = min(max(count, 1), 10)
    
    scenarios = await ai_training_service.generate_synthetic_scenarios(
        db, business_id, count
    )
    
    return [
        TrainingScenarioResponse(
            id=s.id,
            title=s.title,
            description=s.description,
            category=s.category,
            user_input=s.user_input,
            expected_response=s.expected_response,
            is_active=s.is_active,
            success_rate=None,
            last_tested=s.last_tested.isoformat() if s.last_tested else None,
            created_at=s.created_at.isoformat() if s.created_at else ""
        )
        for s in scenarios
    ]


@router.post("/snapshots")
async def create_snapshot(
    name: str,
    description: Optional[str] = None,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """Create a versioned snapshot of current training scenarios"""
    business_id = await deps.get_current_business_id(current_user, db)
    return await ai_training_service.create_snapshot(db, business_id, name, description)


@router.get("/snapshots")
async def list_snapshots(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """List all training snapshots"""
    business_id = await deps.get_current_business_id(current_user, db)
    return await ai_training_service.list_snapshots(db, business_id)


@router.post("/snapshots/{snapshot_id}/rollback")
async def rollback_snapshot(
    snapshot_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """
    Rollback training data to a specific snapshot.
    This will replace all current training scenarios with those from the snapshot.
    """
    business_id = await deps.get_current_business_id(current_user, db)
    return await ai_training_service.rollback_snapshot(db, business_id, snapshot_id)


@router.get("/benchmarks")
async def get_benchmarks(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """Get recent benchmark results"""
    business_id = await deps.get_current_business_id(current_user, db)
    return await ai_training_service.get_benchmarks(db, business_id)


@router.post("/test-input")
async def test_input(
    test_input: dict,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """Test AI with custom input and return full reasoning details (Playground)"""
    from app.services.nova_reasoning import nova_reasoning, get_training_context
    from app.api.v1.endpoints.voice import _get_business_context
    from app.services.knowledge_base import knowledge_base_service
    
    business_id = await deps.get_current_business_id(current_user, db)
    business_context = await _get_business_context(business_id, db)
    customer_context = {
        "name": "Test Customer",
        "phone": "+1 (555) 123-4567",
        "call_count": 0,
        "last_contact": "Never",
        "satisfaction_score": 5.0,
        "preferred_services": [],
        "complaint_count": 0
    }
    
    # Capture the contexts being used for the playground
    input_text = test_input.get("input", "")
    
    knowledge_context = await knowledge_base_service.get_relevant_context(
        query=input_text,
        business_id=business_id,
        db=db
    )
    
    training_context = await get_training_context(
        business_id=business_id,
        db=db,
        conversation=input_text
    )
    
    result = await nova_reasoning.reason(
        conversation=input_text,
        business_context=business_context,
        customer_context=customer_context,
        db=db
    )
    
    # Add debug context for the playground
    result["playground_context"] = {
        "knowledge_base": knowledge_context,
        "training_examples": training_context,
        "business_profile": business_context
    }
    
    return result


@router.get("/categories")
async def get_categories():
    """Get available training categories"""
    return {"categories": ai_training_service.CATEGORIES}


@router.get("/{scenario_id}")
async def get_scenario(
    scenario_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> TrainingScenarioResponse:
    """Get a specific training scenario"""
    
    business_id = await deps.get_current_business_id(current_user, db)
    scenario = await ai_training_service.get_scenario(db, scenario_id, business_id)
    
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")
    
    return TrainingScenarioResponse(
        id=scenario.id,
        title=scenario.title,
        description=scenario.description,
        category=scenario.category,
        user_input=scenario.user_input,
        expected_response=scenario.expected_response,
        is_active=scenario.is_active,
        success_rate=float(scenario.success_rate) if scenario.success_rate else None,
        last_tested=scenario.last_tested.isoformat() if scenario.last_tested else None,
        created_at=scenario.created_at.isoformat() if scenario.created_at else ""
    )


@router.put("/{scenario_id}")
async def update_scenario(
    scenario_id: int,
    scenario_update: TrainingScenarioUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> TrainingScenarioResponse:
    """Update a training scenario"""
    
    business_id = await deps.get_current_business_id(current_user, db)
    
    scenario = await ai_training_service.update_scenario(
        db, scenario_id, business_id, **scenario_update.dict(exclude_unset=True)
    )
    
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")
    
    return TrainingScenarioResponse(
        id=scenario.id,
        title=scenario.title,
        description=scenario.description,
        category=scenario.category,
        user_input=scenario.user_input,
        expected_response=scenario.expected_response,
        is_active=scenario.is_active,
        success_rate=float(scenario.success_rate) if scenario.success_rate else None,
        last_tested=scenario.last_tested.isoformat() if scenario.last_tested else None,
        created_at=scenario.created_at.isoformat() if scenario.created_at else ""
    )


@router.delete("/{scenario_id}")
async def delete_scenario(
    scenario_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """Delete a training scenario"""
    
    business_id = await deps.get_current_business_id(current_user, db)
    
    success = await ai_training_service.delete_scenario(db, scenario_id, business_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Scenario not found")
    
    return {"message": "Scenario deleted successfully"}


class CallLogCorrection(BaseModel):
    user_input: str
    expected_response: str
    category: Optional[str] = "general_inquiry"


@router.post("/convert-approval/{approval_id}")
async def convert_approval(
    approval_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> TrainingScenarioResponse:
    """Convert an approval request into a training scenario"""
    
    business_id = await deps.get_current_business_id(current_user, db)
    
    scenario = await ai_training_service.create_scenario_from_approval(
        db, business_id, approval_id
    )
    
    if not scenario:
        raise HTTPException(
            status_code=404, 
            detail="Approval request not found or not reviewed"
        )
    
    return TrainingScenarioResponse(
        id=scenario.id,
        title=scenario.title,
        description=scenario.description,
        category=scenario.category,
        user_input=scenario.user_input,
        expected_response=scenario.expected_response,
        is_active=scenario.is_active,
        success_rate=None,
        last_tested=None,
        created_at=scenario.created_at.isoformat() if scenario.created_at else ""
    )


@router.post("/convert-call-log/{call_session_id}")
async def convert_call_log(
    call_session_id: str,
    correction: CallLogCorrection,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> TrainingScenarioResponse:
    """Convert a call log correction into a training scenario"""
    
    business_id = await deps.get_current_business_id(current_user, db)
    
    scenario = await ai_training_service.create_scenario_from_call_log(
        db, business_id, call_session_id, correction.user_input, 
        correction.expected_response, correction.category
    )
    
    return TrainingScenarioResponse(
        id=scenario.id,
        title=scenario.title,
        description=scenario.description,
        category=scenario.category,
        user_input=scenario.user_input,
        expected_response=scenario.expected_response,
        is_active=scenario.is_active,
        success_rate=None,
        last_tested=None,
        created_at=scenario.created_at.isoformat() if scenario.created_at else ""
    )
