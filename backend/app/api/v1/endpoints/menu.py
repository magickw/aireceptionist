"""
Menu API endpoints for managing business menus (restaurants, retail, etc.)
"""
from typing import List, Optional, Set, Dict
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.api import deps
from app.models.models import User, MenuItem, Business

router = APIRouter()

# Define allowed menu categories for each business type
# This prevents inappropriate menu items (e.g., food in dental clinics)
BUSINESS_TYPE_CATEGORIES: Dict[str, Set[str]] = {
    "restaurant": {
        "Appetizers", "Main Course", "Desserts", "Drinks", "Beverages",
        "Side Dishes", "Soups", "Salads", "Seafood", "Poultry", "Meat",
        "Vegetarian", "Vegan", "Gluten-Free", "Kids Menu", "Specials"
    },
    "medical": {
        "Consultations", "Checkups", "Vaccinations", "Lab Tests", "X-rays",
        "Procedures", "Treatments", "Therapy", "Screenings", "Follow-up",
        "Emergency", "Specialist", "Diagnostics", "Immunizations"
    },
    "dental": {
        "Checkups", "Cleanings", "Fillings", "Extractions", "Root Canals",
        "Crowns", "Bridges", "Dentures", "Implants", "Orthodontics",
        "Cosmetic", "Whitening", "X-rays", "Consultations", "Emergency",
        "Pediatric", "Periodontal", "Oral Surgery"
    },
    "hotel": {
        "Standard Room", "Deluxe Room", "Suite", "Executive Suite",
        "Breakfast", "Lunch", "Dinner", "Room Service", "Amenities",
        "Spa", "Gym", "Pool", "Parking", "WiFi", "Concierge"
    },
    "salon": {
        "Haircut", "Styling", "Coloring", "Highlights", "Balayage",
        "Manicure", "Pedicure", "Facial", "Massage", "Waxing",
        "Makeup", "Bridal", "Hair Treatment", "Scalp Treatment"
    },
    "spa": {
        "Massage", "Facial", "Body Treatment", "Sauna", "Steam Room",
        "Hydrotherapy", "Aromatherapy", "Hot Stone", "Reflexology",
        "Wellness Package", "Couple's Package", "Detox"
    },
    "fitness": {
        "Personal Training", "Group Classes", "Yoga", "Pilates",
        "CrossFit", "Spin", "Membership", "Day Pass", "Training Plan",
        "Nutrition Consultation", "Physical Therapy"
    },
    "retail": {
        "Clothing", "Electronics", "Books", "Home Goods", "Accessories",
        "Shoes", "Jewelry", "Toys", "Sports Equipment", "Beauty Products"
    },
    "law_firm": {
        "Consultation", "Document Review", "Legal Representation",
        "Contract Drafting", "Litigation", "Mediation", "Arbitration",
        "Legal Research", "Notary Services", "Specialized Services"
    },
    "real_estate": {
        "Apartments", "Houses", "Condos", "Commercial Properties",
        "Land", "Property Management", "Rental", "Leasing",
        "Property Valuation", "Home Inspection"
    },
    "hvac": {
        "Installation", "Repair", "Maintenance", "Inspection",
        "Duct Cleaning", "Air Quality Testing", "Emergency Service",
        "System Upgrade", "Thermostat Installation", "Consultation"
    },
    "accounting": {
        "Tax Preparation", "Bookkeeping", "Audit", "Financial Planning",
        "Payroll Services", "Consultation", "Business Advisory",
        "Financial Statements", "Tax Planning", "Compliance"
    }
}

def validate_menu_category_for_business_type(business_type: str, category: Optional[str]) -> bool:
    """
    Validate that the menu category is appropriate for the business type.
    
    Args:
        business_type: The type of business (e.g., 'restaurant', 'dental')
        category: The menu item category
    
    Returns:
        True if valid, False otherwise
    """
    if not category:
        # No category specified, allow it
        return True
    
    # Get allowed categories for this business type
    allowed_categories = BUSINESS_TYPE_CATEGORIES.get(business_type.lower())
    
    if not allowed_categories:
        # No restrictions defined for this business type, allow any category
        return True
    
    # Check if the category is in the allowed set (case-insensitive)
    return category.strip() in allowed_categories


# Pydantic schemas
class MenuItemBase(BaseModel):
    name: str
    description: Optional[str] = None
    price: Optional[float] = None
    unit: Optional[str] = "per item"  # e.g., per item, per lb, per kg, per hour, per ton
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
    unit: Optional[str] = None
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
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> List[MenuItem]:
    """Get all menu items for a business"""
    query = db.query(MenuItem).filter(MenuItem.business_id == business_id)

    if category:
        query = query.filter(MenuItem.category == category)

    if available_only:
        query = query.filter(MenuItem.available == True)

    return query.filter(MenuItem.is_active == True).order_by(MenuItem.category, MenuItem.name).offset(skip).limit(limit).all()


@router.post("/", response_model=MenuItemResponse)
def create_menu_item(
    menu_item: MenuItemCreate,
    business_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> MenuItem:
    """Create a new menu item"""
    # Get the business to check its type
    business = db.query(Business).filter(Business.id == business_id).first()
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")
    
    # Validate that the category is appropriate for the business type
    if not validate_menu_category_for_business_type(business.type, menu_item.category):
        allowed_cats = BUSINESS_TYPE_CATEGORIES.get(business.type.lower(), set())
        raise HTTPException(
            status_code=400,
            detail=f"Invalid menu category '{menu_item.category}' for business type '{business.type}'. "
                   f"Allowed categories: {', '.join(sorted(allowed_cats)) if allowed_cats else 'Any category'}"
        )
    
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
    
    # Get the business to check its type
    business = db.query(Business).filter(Business.id == business_id).first()
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")
    
    # Validate the category if it's being updated
    if menu_item.category is not None:
        if not validate_menu_category_for_business_type(business.type, menu_item.category):
            allowed_cats = BUSINESS_TYPE_CATEGORIES.get(business.type.lower(), set())
            raise HTTPException(
                status_code=400,
                detail=f"Invalid menu category '{menu_item.category}' for business type '{business.type}'. "
                       f"Allowed categories: {', '.join(sorted(allowed_cats)) if allowed_cats else 'Any category'}"
            )
    
    for field, value in menu_item.model_dump(exclude_unset=True).items():
        setattr(db_item, field, value)
    
    db.commit()
    db.refresh(db_item)
    return db_item


class MenuItemInventoryUpdate(BaseModel):
    inventory: int

@router.put("/{item_id}/inventory", response_model=MenuItemResponse)
def update_inventory(
    item_id: int,
    business_id: int,
    inventory_update: MenuItemInventoryUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> MenuItem:
    """Update the inventory for a specific menu item."""
    db_item = db.query(MenuItem).filter(
        MenuItem.id == item_id,
        MenuItem.business_id == business_id
    ).first()

    if not db_item:
        raise HTTPException(status_code=404, detail="Menu item not found")

    db_item.inventory = inventory_update.inventory
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
