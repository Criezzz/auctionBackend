#!/usr/bin/env python3
"""
Simple database connection test
"""
import sys
import os

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

try:
    # Test database connection
    from database import SessionLocal
    from models import Product
    
    print("Testing database connection...")
    
    # Try to create a session
    db = SessionLocal()
    print("Database session created successfully")
    
    # Test basic query
    try:
        products = db.query(Product).limit(1).all()
        print(f"Query successful, got {len(products)} products")
    except Exception as e:
        print(f"Query error: {e}")
        import traceback
        traceback.print_exc()
    
    db.close()
    print("Database session closed")
    
except Exception as e:
    print(f"Database connection error: {e}")
    import traceback
    traceback.print_exc()