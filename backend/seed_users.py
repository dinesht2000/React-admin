"""
Pre-seed script to insert admin and corporate_admin users.
Run this script to create initial users with proper hashed passwords.
"""
from app.db.session import SessionLocal
from app.db.models import User, AccountRoleEnum, StatusEnum
from app.core.security import get_password_hash

def seed_users():
    """Create admin and corporate_admin users if they don't exist."""
    db = SessionLocal()
    
    try:
        # Default password for both users (change in production)
        default_password = "admin123"
        hashed_password = get_password_hash(default_password)
        
        # Check if admin user already exists
        admin_user = db.query(User).filter(User.email == "admin@example.com").first()
        if not admin_user:
            admin_user = User(
                name="Admin_001",
                email="admin@example.com",
                password=hashed_password,
                account_role=AccountRoleEnum.admin,
                status=StatusEnum.active
            )
            db.add(admin_user)
            print("✓ Admin user created: admin@example.com")
        else:
            print("⚠ Admin user already exists: admin@example.com")
        
        # Check if corporate admin user already exists
        corporate_user = db.query(User).filter(User.email == "corporate@example.com").first()
        if not corporate_user:
            corporate_user = User(
                name="Corporate Admin User",
                email="corporate@example.com",
                password=hashed_password,
                account_role=AccountRoleEnum.corporate_admin,
                status=StatusEnum.active
            )
            db.add(corporate_user)
            print("✓ Corporate admin user created: corporate@example.com")
        else:
            print("⚠ Corporate admin user already exists: corporate@example.com")
        
        # Commit changes
        db.commit()
        print("\n✅ Seeding completed successfully!")
        print(f"Default password for both users: {default_password}")
        print("⚠ Please change the default password in production!")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error seeding users: {str(e)}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    seed_users()

