"""
Menu API endpoints for managing business menus (restaurants, retail, etc.)
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.api import deps
from app.models.models import User, MenuItem

router = APIRouter()


# Pydantic schemas
class MenuItemBase(BaseModel):
    name: str
    description: Optional[str] = None
    price: Optional[float] = None
    category: Optional[str] = None
    available: bool = True
    dietary_info: Optional[dict] = None
    image_url: Optional[str] = None


class MenuItemCreate(MenuItemBase):
    pass


class MenuItemUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    category: Optional[str] = None
    available: Optional[bool] = None
    dietary_info: Optional[dict] = None
    image_url: Optional[str] = None
    is_active: Optional[bool] = None


class MenuItemResponse(MenuItemBase):
    id: int
    business_id: int
    is_active: bool

    class Config:
        from_attributes = True


@router.get("/", response_model=List[MenuItemResponse])
def read_menu_items(
    business_id: int,
    category: Optional[str] = None,
    available_only: bool = False,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> List[MenuItem]:
    """Get all menu items for a business"""
    query = db.query(MenuItem).filter(MenuItem.business_id == business_id)
    
    if category:
        query = query.filter(MenuItem.category == category)
    
    if available_only:
        query = query.filter(MenuItem.available == True)
    
    return query.filter(MenuItem.is_active == True).order_by(MenuItem.category, MenuItem.name).all()


@router.post("/", response_model=MenuItemResponse)
def create_menu_item(
    menu_item: MenuItemCreate,
    business_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> MenuItem:
    """Create a new menu item"""
    db_item = MenuItem(
        **menu_item.model_dump(),
        business_id=business_id
    )
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item


@router.get("/{item_id}", response_model=MenuItemResponse)
def read_menu_item(
    item_id: int,
    business_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> MenuItem:
    """Get a specific menu item"""
    item = db.query(MenuItem).filter(
        MenuItem.id == item_id,
        MenuItem.business_id == business_id
    ).first()
    
    if not item:
        raise HTTPException(status_code=404, detail="Menu item not found")
    
    return item


@router.put("/{item_id}", response_model=MenuItemResponse)
def update_menu_item(
    item_id: int,
    menu_item: MenuItemUpdate,
    business_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> MenuItem:
    """Update a menu item"""
    db_item = db.query(MenuItem).filter(
        MenuItem.id == item_id,
        MenuItem.business_id == business_id
    ).first()
    
    if not db_item:
        raise HTTPException(status_code=404, detail="Menu item not found")
    
    for field, value in menu_item.model_dump(exclude_unset=True).items():
        setattr(db_item, field, value)
    
    db.commit()
    db.refresh(db_item)
    return db_item


@router.delete("/{item_id}")
def delete_menu_item(
    item_id: int,
    business_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> dict:
    """Soft delete a menu item (set is_active to false)"""
    db_item = db.query(MenuItem).filter(
        MenuItem.id == item_id,
        MenuItem.business_id == business_id
    ).first()
    
    if not db_item:
        raise HTTPException(status_code=404, detail="Menu item not found")
    
    db_item.is_active = False
    db.commit()
    
    return {"status": "deleted"}


@router.get("/categories/list")
def get_menu_categories(
    business_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> List[str]:
    """Get list of all menu categories"""
    categories = db.query(MenuItem.category).filter(
        MenuItem.business_id == business_id,
        MenuItem.is_active == True,
        MenuItem.category.isnot(None)
    ).distinct().all()
    
    return [c[0] for c in categories if c[0]]
