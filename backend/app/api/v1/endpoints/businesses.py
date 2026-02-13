from typing import List, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api import deps
from app.models.models import Business, User
from app.schemas.business import BusinessCreate, BusinessUpdate, Business as BusinessSchema

router = APIRouter()

@router.get("/", response_model=List[BusinessSchema])
def read_businesses(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Retrieve businesses.
    """
    if current_user.role == "admin":
        businesses = db.query(Business).offset(skip).limit(limit).all()
    else:
        businesses = db.query(Business).filter(Business.user_id == current_user.id).offset(skip).limit(limit).all()
    return businesses

@router.post("/", response_model=BusinessSchema)
def create_business(
    *,
    db: Session = Depends(deps.get_db),
    business_in: BusinessCreate,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Create new business.
    """
    business = Business(
        **business_in.model_dump(),
        user_id=current_user.id
    )
    db.add(business)
    db.commit()
    db.refresh(business)
    return business

@router.get("/{id}", response_model=BusinessSchema)
def read_business(
    *,
    db: Session = Depends(deps.get_db),
    id: int,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get business by ID.
    """
    business = db.query(Business).filter(Business.id == id).first()
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")
    if current_user.role != "admin" and business.user_id != current_user.id:
        raise HTTPException(status_code=400, detail="Not enough permissions")
    return business
