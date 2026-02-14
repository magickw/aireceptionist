"""
Seed test users and sample data
"""

import os
import sys

# Add the backend directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.db.session import SessionLocal
from app.core.security import get_password_hash
from app.models.models import User, Business


def seed_users():
    """Create test users with businesses"""
    db = SessionLocal()
    
    try:
        # Create admin user if not exists
        admin = db.query(User).filter(User.email == "admin@demo.com").first()
        if not admin:
            admin = User(
                email="admin@demo.com",
                name="Admin User",
                password=get_password_hash("admin123"),
                role="admin",
                status="active"
            )
            db.add(admin)
            print("Created user: admin@demo.com")
        
        # Create business owner if not exists
        owner = db.query(User).filter(User.email == "owner@demo.com").first()
        if not owner:
            owner = User(
                email="owner@demo.com",
                name="Business Owner",
                password=get_password_hash("owner123"),
                role="business_owner",
                status="active"
            )
            db.add(owner)
            print("Created user: owner@demo.com")
        
        # Create staff user if not exists
        staff = db.query(User).filter(User.email == "staff@demo.com").first()
        if not staff:
            staff = User(
                email="staff@demo.com",
                name="Staff Member",
                password=get_password_hash("staff123"),
                role="staff",
                status="active"
            )
            db.add(staff)
            print("Created user: staff@demo.com")
        
        db.commit()
        
        # Refresh users to get IDs
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
        print("Created business: Demo Medical Clinic")
        
        biz2 = Business(
            user_id=staff.id,
            name="Demo Law Office",
            type="legal",
            phone="+1987654321",
            address="456 Oak Avenue, Los Angeles, CA 90001",
            description="Law office providing legal services"
        )
        db.add(biz2)
        print("Created business: Demo Law Office")
        
        db.commit()
        
        print("\n" + "="*50)
        print("Seed completed successfully!")
        print("="*50)
        print("\nTest accounts:")
        print("  Email: admin@demo.com   | Password: admin123   | Role: Admin")
        print("  Email: owner@demo.com   | Password: owner123   | Role: Business Owner")
        print("  Email: staff@demo.com   | Password: staff123   | Role: Staff")
        
    except Exception as e:
        print(f"Error seeding users: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_users()
