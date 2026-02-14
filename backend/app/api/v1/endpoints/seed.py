"""
Seed endpoint to create test users - for development only
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api import deps
from app.core.security import get_password_hash
from app.models.models import User, Business

router = APIRouter()


@router.post("/seed")
def seed_database(
    db: Session = Depends(deps.get_db),
) -> dict:
    """
    Seed the database with test users - WARNING: For development only!
    """
    
    # Check if users already exist
    existing = db.query(User).first()
    if existing:
        return {"message": "Database already seeded, skipping..."}
    
    # Create admin user
    admin = User(
        email="admin@demo.com",
        name="Admin User",
        password=get_password_hash("admin123"),
        role="admin",
        status="active"
    )
    db.add(admin)
    
    # Create business owner
    owner = User(
        email="owner@demo.com",
        name="Business Owner",
        password=get_password_hash("owner123"),
        role="business_owner",
        status="active"
    )
    db.add(owner)
    
    # Create staff user
    staff = User(
        email="staff@demo.com",
        name="Staff Member",
        password=get_password_hash("staff123"),
        role="staff",
        status="active"
    )
    db.add(staff)
    
    db.commit()
    db.refresh(admin)
    db.refresh(owner)
    db.refresh(staff)
    
    # Create businesses
    biz1 = Business(
        user_id=owner.id,
        name="Demo Medical Clinic",
        type="healthcare",
        phone="+1234567890",
        address="123 Main Street, San Francisco, CA 94102",
        description="Medical clinic providing general healthcare services"
    )
    db.add(biz1)
    
    biz2 = Business(
        user_id=staff.id,
        name="Demo Law Office",
        type="legal",
        phone="+1987654321",
        address="456 Oak Avenue, Los Angeles, CA 90001",
        description="Law office providing legal services"
    )
    db.add(biz2)
    
    db.commit()
    
    return {
        "message": "Database seeded successfully!",
        "users": [
            {"email": "admin@demo.com", "password": "admin123", "role": "admin"},
            {"email": "owner@demo.com", "password": "owner123", "role": "business_owner"},
            {"email": "staff@demo.com", "password": "staff123", "role": "staff"},
        ]
    }
