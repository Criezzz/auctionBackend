"""
Seed database với user mẫu để test authentication
Run: python -m app.seed_db
"""
from datetime import datetime
from sqlalchemy import create_engine, text
from app.database import SessionLocal, engine, SQLALCHEMY_DATABASE_URL
from app import models
from app.auth import get_password_hash


def create_database_if_not_exists():
    """Tạo database auction_db nếu chưa tồn tại"""
    try:
        # Parse connection string to get database name
        # Format: mysql+pymysql://user:password@host:port/dbname
        parts = SQLALCHEMY_DATABASE_URL.split('/')
        db_name = parts[-1] if len(parts) > 0 else 'auction_db'
        
        # Connection URL without database name
        base_url = '/'.join(parts[:-1])
        
        # Use SQLAlchemy to connect to the server without selecting a database
        engine_no_db = create_engine(base_url, pool_pre_ping=True)
        with engine_no_db.connect() as conn:
            # Some DBAPIs require autocommit for CREATE DATABASE
            conn = conn.execution_options(isolation_level="AUTOCOMMIT")
            conn.execute(text(f"CREATE DATABASE IF NOT EXISTS `{db_name}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"))
            print(f" Database '{db_name}' ready")
        engine_no_db.dispose()
        
    except Exception as e:
        print("  Make sure the database server is running and the connection URL is correct")

def seed_database():
    # Create database first
    create_database_if_not_exists()
    
    # Create tables
    models.Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        # Check if admin already exists
        existing_admin = db.query(models.Account).filter(
            models.Account.username == "admin"
        ).first()
        
        if existing_admin:
            print("✓ Admin user already exists")
            return
        
        # Create admin user
        admin = models.Account(
            username="admin",
            email="admin@auction.com",
            password=get_password_hash("admin123"),
            first_name="Admin",
            last_name="User",
            phone_num="0123456789",
            created_at=datetime.utcnow(),
            activated=True,
            is_admin=True,
            is_authenticated=False
        )
        
        # Create regular user
        user = models.Account(
            username="user1",
            email="user1@auction.com",
            password=get_password_hash("user123"),
            first_name="John",
            last_name="Doe",
            phone_num="0987654321",
            created_at=datetime.utcnow(),
            activated=True,
            is_admin=False,
            is_authenticated=False
        )
        
        db.add(admin)
        db.add(user)
        db.commit()
        
        print(" Database seeded successfully!")
        print("\nTest accounts:")
        print("  Admin - username: admin, password: admin123")
        print("  User  - username: user1, password: user123")
        
    except Exception as e:
        print(f"✗ Error seeding database: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
