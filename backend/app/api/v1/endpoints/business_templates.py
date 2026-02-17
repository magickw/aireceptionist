"""Admin API endpoints for business template management"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from app.api.deps import get_db, get_current_active_user
from app.models.models import User, BusinessTemplate
from app.services.business_template_service import template_service
from app.services.business_type_detection import suggest_business_types
from pydantic import BaseModel


router = APIRouter()


# Pydantic schemas
class RiskProfileSchema(BaseModel):
    high_risk_intents: List[str] = []
    auto_escalate_threshold: float = 0.5
    confidence_threshold: float = 0.6


class BookingFlowSchema(BaseModel):
    type: Optional[str] = None
    steps: List[dict] = []
    final_action: Optional[str] = None
    confirmation_message: Optional[str] = None


class BusinessTemplateCreate(BaseModel):
    template_key: str
    name: str
    icon: Optional[str] = None
    description: Optional[str] = None
    autonomy_level: str = "MEDIUM"
    risk_profile: RiskProfileSchema
    common_intents: List[str] = []
    fields: dict = {}
    booking_flow: BookingFlowSchema
    system_prompt_addition: Optional[str] = None
    example_responses: dict = {}
    is_active: bool = True
    is_default: bool = False


class BusinessTemplateUpdate(BaseModel):
    name: Optional[str] = None
    icon: Optional[str] = None
    description: Optional[str] = None
    autonomy_level: Optional[str] = None
    risk_profile: Optional[RiskProfileSchema] = None
    common_intents: Optional[List[str]] = None
    fields: Optional[dict] = None
    booking_flow: Optional[BookingFlowSchema] = None
    system_prompt_addition: Optional[str] = None
    example_responses: Optional[dict] = None
    is_active: Optional[bool] = None
    is_default: Optional[bool] = None
    change_description: Optional[str] = "Template updated"


class BusinessTemplateResponse(BaseModel):
    id: int
    template_key: str
    name: str
    icon: Optional[str]
    description: Optional[str]
    autonomy_level: str
    risk_profile: dict
    common_intents: List[str]
    fields: dict
    booking_flow: dict
    system_prompt_addition: Optional[str]
    example_responses: dict
    is_active: bool
    is_default: bool
    version: int
    created_at: Optional[str]
    updated_at: Optional[str]
    
    class Config:
        from_attributes = True


class BusinessTypeSuggestionResponse(BaseModel):
    business_type: str
    confidence: float
    name: str
    icon: str


class TemplateVersionResponse(BaseModel):
    id: int
    template_id: int
    version_number: int
    name: Optional[str]
    icon: Optional[str]
    description: Optional[str]
    autonomy_level: Optional[str]
    change_description: Optional[str]
    is_active: bool
    created_at: Optional[str]


@router.get("/", response_model=List[BusinessTemplateResponse])
def list_templates(
    active_only: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    List all business templates.
    
    Args:
        active_only: Only return active templates
        db: Database session
        current_user: Authenticated user
    
    Returns:
        List of business templates
    """
    # Check if user has admin role
    if current_user.role not in ["admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can list all templates"
        )
    
    templates = template_service.get_all_templates(db, active_only)
    return templates


@router.get("/{template_id}", response_model=BusinessTemplateResponse)
def get_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get a specific business template by ID.
    
    Args:
        template_id: Template ID
        db: Database session
        current_user: Authenticated user
    
    Returns:
        Business template details
    """
    # Check if user has admin role
    if current_user.role not in ["admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can view templates"
        )
    
    template = template_service.get_template_by_id(template_id, db)
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found"
        )
    
    return template


@router.get("/by-key/{template_key}", response_model=BusinessTemplateResponse)
def get_template_by_key(
    template_key: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get a business template by key.
    
    Args:
        template_key: Template key (e.g., 'restaurant', 'medical')
        db: Database session
        current_user: Authenticated user
    
    Returns:
        Business template details
    """
    # Check if user has admin role
    if current_user.role not in ["admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can view templates"
        )
    
    try:
        template = template_service.get_template(template_key, db)
        return template
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found"
        )


@router.post("/", response_model=BusinessTemplateResponse, status_code=status.HTTP_201_CREATED)
def create_template(
    template_data: BusinessTemplateCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Create a new business template.
    
    Args:
        template_data: Template configuration
        db: Database session
        current_user: Authenticated user
    
    Returns:
        Created business template
    """
    # Check if user has admin role
    if current_user.role not in ["admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can create templates"
        )
    
    # Check if template key already exists
    existing = db.query(BusinessTemplate).filter(
        BusinessTemplate.template_key == template_data.template_key
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Template with key '{template_data.template_key}' already exists"
        )
    
    # Convert to dict for service
    template_dict = template_data.dict()
    template_dict["risk_profile"] = template_data.risk_profile.dict()
    template_dict["booking_flow"] = template_data.booking_flow.dict()
    
    template = template_service.create_template(
        template_dict,
        current_user.id,
        db
    )
    
    return template_service.get_template_by_id(template.id, db)


@router.put("/{template_id}", response_model=BusinessTemplateResponse)
def update_template(
    template_id: int,
    template_data: BusinessTemplateUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Update an existing business template.
    
    Args:
        template_id: Template ID
        template_data: Updated template configuration
        db: Database session
        current_user: Authenticated user
    
    Returns:
        Updated business template
    """
    # Check if user has admin role
    if current_user.role not in ["admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can update templates"
        )
    
    # Convert to dict for service
    template_dict = template_data.dict(exclude_unset=True)
    if "risk_profile" in template_dict and template_data.risk_profile:
        template_dict["risk_profile"] = template_data.risk_profile.dict()
    if "booking_flow" in template_dict and template_data.booking_flow:
        template_dict["booking_flow"] = template_data.booking_flow.dict()
    
    template = template_service.update_template(
        template_id,
        template_dict,
        current_user.id,
        db
    )
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found"
        )
    
    return template_service.get_template_by_id(template.id, db)


@router.delete("/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Delete (soft delete) a business template.
    
    Args:
        template_id: Template ID
        db: Database session
        current_user: Authenticated user
    """
    # Check if user has admin role
    if current_user.role not in ["admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can delete templates"
        )
    
    success = template_service.delete_template(template_id, db)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found"
        )


@router.get("/{template_id}/versions", response_model=List[TemplateVersionResponse])
def list_template_versions(
    template_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    List all versions of a template.
    
    Args:
        template_id: Template ID
        db: Database session
        current_user: Authenticated user
    
    Returns:
        List of template versions
    """
    # Check if user has admin role
    if current_user.role not in ["admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can view template versions"
        )
    
    # Verify template exists
    template = template_service.get_template_by_id(template_id, db)
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found"
        )
    
    versions = template_service.get_template_versions(template_id, db)
    return versions


@router.post("/{template_id}/versions/{version_id}/restore", response_model=BusinessTemplateResponse)
def restore_template_version(
    template_id: int,
    version_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Restore a template to a previous version.
    
    Args:
        template_id: Template ID
        version_id: Version ID to restore
        db: Database session
        current_user: Authenticated user
    
    Returns:
        Restored business template
    """
    # Check if user has admin role
    if current_user.role not in ["admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can restore template versions"
        )
    
    # Verify template exists
    template = template_service.get_template_by_id(template_id, db)
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found"
        )
    
    restored_template = template_service.restore_version(version_id, current_user.id, db)
    
    if not restored_template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Version not found"
        )
    
    return template_service.get_template_by_id(template_id, db)


@router.post("/suggest", response_model=List[BusinessTypeSuggestionResponse])
def suggest_business_type(
    description: str,
    top_n: int = 3,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Suggest business types based on description using NLP.
    
    Args:
        description: Business description
        top_n: Number of suggestions to return
        db: Database session
        current_user: Authenticated user
    
    Returns:
        List of business type suggestions with confidence scores
    """
    suggestions = suggest_business_types(description, db, top_n)
    return suggestions


@router.post("/cache/clear", status_code=status.HTTP_204_NO_CONTENT)
def clear_template_cache(
    current_user: User = Depends(get_current_active_user)
):
    """
    Clear the template cache.
    
    Args:
        current_user: Authenticated user
    """
    # Check if user has admin role
    if current_user.role not in ["admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can clear template cache"
        )
    
    template_service.clear_all_cache()