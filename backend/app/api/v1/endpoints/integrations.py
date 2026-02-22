from typing import Any, List, Optional, Dict
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.api import deps
from app.models.models import Integration as IntegrationModel, User, Business
from app.services.integration_service import IntegrationService, get_integration_instance, BaseIntegration

router = APIRouter()

# Pydantic schemas for request/response
class IntegrationBase(BaseModel):
    integration_type: str
    name: str
    configuration: Dict
    credentials: Optional[Dict] = None # Credentials should ideally be handled more securely, e.g., KMS

class IntegrationCreate(IntegrationBase):
    pass

class IntegrationUpdate(IntegrationBase):
    integration_type: Optional[str] = None
    name: Optional[str] = None
    configuration: Optional[Dict] = None
    credentials: Optional[Dict] = None

class IntegrationResponse(IntegrationBase):
    id: int
    business_id: int
    status: str
    error_message: Optional[str] = None
    
    class Config:
        from_attributes = True

@router.post("/", response_model=IntegrationResponse, status_code=status.HTTP_201_CREATED)
async def create_integration(
    integration_in: IntegrationCreate,
    business_id: int = Depends(deps.get_current_business_id),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Create a new integration for a business.
    Attempts to connect/authenticate to verify credentials.
    """
    # Ensure credentials are not returned in the response later
    integration_data = integration_in.model_dump(exclude_unset=True)
    credentials_to_use = integration_data.pop("credentials", None) # Remove credentials from data to be saved to DB config if not needed

    db_integration = IntegrationModel(
        **integration_data,
        business_id=business_id,
        status="pending", # Start as pending
        credentials=credentials_to_use # Store credentials
    )

    # Attempt to connect/authenticate using the integration service
    integration_client: Optional[BaseIntegration] = get_integration_instance(
        db, business_id, db_integration.integration_type, db_integration.configuration
    )
    
    if not integration_client:
        db_integration.status = "failed"
        db_integration.error_message = "Unsupported integration type or client not found"
        db.add(db_integration)
        db.commit()
        db.refresh(db_integration)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported integration type: {integration_in.integration_type}"
        )

    try:
        # For simplicity, pass credentials directly. In a real app, these would be
        # managed more securely (e.g., encrypted in DB, retrieved from KMS).
        if await integration_client.authenticate(credentials_to_use):
            db_integration.status = "active"
            db_integration.error_message = None
        else:
            db_integration.status = "failed"
            db_integration.error_message = "Authentication failed"
    except Exception as e:
        db_integration.status = "failed"
        db_integration.error_message = f"Connection error: {str(e)}"
        print(f"Integration connection error: {e}")

    db.add(db_integration)
    db.commit()
    db.refresh(db_integration)
    
    # Do not return credentials in the response
    db_integration.credentials = {}
    return db_integration

@router.get("/", response_model=List[IntegrationResponse])
def read_integrations(
    business_id: int = Depends(deps.get_current_business_id),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """Retrieve all integrations for a business."""
    integrations = db.query(IntegrationModel).filter(IntegrationModel.business_id == business_id).all()
    # Ensure credentials are not returned
    for integration in integrations:
        integration.credentials = {}
    return integrations

@router.get("/{integration_id}", response_model=IntegrationResponse)
def read_integration_by_id(
    integration_id: int,
    business_id: int = Depends(deps.get_current_business_id),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """Retrieve a specific integration by ID."""
    integration = db.query(IntegrationModel).filter(
        IntegrationModel.id == integration_id,
        IntegrationModel.business_id == business_id
    ).first()
    if not integration:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Integration not found")
    
    # Do not return credentials
    integration.credentials = {}
    return integration

@router.put("/{integration_id}", response_model=IntegrationResponse)
async def update_integration(
    integration_id: int,
    integration_in: IntegrationUpdate,
    business_id: int = Depends(deps.get_current_business_id),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Update an existing integration.
    Attempts to reconnect/authenticate if credentials or config change.
    """
    db_integration = db.query(IntegrationModel).filter(
        IntegrationModel.id == integration_id,
        IntegrationModel.business_id == business_id
    ).first()

    if not db_integration:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Integration not found")

    update_data = integration_in.model_dump(exclude_unset=True)
    credentials_to_use = update_data.pop("credentials", None)
    
    # Apply updates
    for field, value in update_data.items():
        setattr(db_integration, field, value)
    
    if credentials_to_use:
        db_integration.credentials = credentials_to_use

    # Re-attempt connection/authentication if relevant fields changed
    integration_client: Optional[BaseIntegration] = get_integration_instance(
        db, business_id, db_integration.integration_type, db_integration.configuration
    )
    
    if not integration_client:
        db_integration.status = "failed"
        db_integration.error_message = "Unsupported integration type or client not found"
    else:
        try:
            if await integration_client.authenticate(db_integration.credentials):
                db_integration.status = "active"
                db_integration.error_message = None
            else:
                db_integration.status = "failed"
                db_integration.error_message = "Authentication failed"
        except Exception as e:
            db_integration.status = "failed"
            db_integration.error_message = f"Connection error: {str(e)}"
            print(f"Integration reconnection error: {e}")

    db.add(db_integration) # Re-add to ensure status update is picked up
    db.commit()
    db.refresh(db_integration)
    
    # Do not return credentials
    db_integration.credentials = {}
    return db_integration

@router.delete("/{integration_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_integration(
    integration_id: int,
    business_id: int = Depends(deps.get_current_business_id),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> None:
    """Delete an integration."""
    db_integration = db.query(IntegrationModel).filter(
        IntegrationModel.id == integration_id,
        IntegrationModel.business_id == business_id
    ).first()

    if not db_integration:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Integration not found")

    db.delete(db_integration)
    db.commit()