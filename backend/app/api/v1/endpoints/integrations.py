from typing import Any, List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, Dict

from app.api import deps
from app.models.models import Integration as IntegrationModel, User, Business

class IntegrationBase(BaseModel):
    integration_type: str
    name: str
    status: str
    configuration: Optional[Dict] = {}

class IntegrationCreate(IntegrationBase):
    business_id: int

class Integration(IntegrationBase):
    id: int
    business_id: int
    
    class Config:
        from_attributes = True

router = APIRouter()

@router.get("/business/{business_id}", response_model=List[Integration])
def read_integrations(
    business_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    integrations = db.query(IntegrationModel).filter(IntegrationModel.business_id == business_id).all()
    return integrations
