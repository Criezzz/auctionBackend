#!/usr/bin/env python3
"""
Direct database test to isolate the issue
"""
import sys
import os

# Set UTF-8 encoding
import locale
import codecs

# Set UTF-8 as default encoding
if sys.platform.startswith('win'):
    import _locale
    _locale._getdefaultlocale = (lambda *args: ['en_US', 'utf8'])

os.environ['PYTHONIOENCODING'] = 'utf-8'

try:
    # Test importing app modules
    from app.database import SessionLocal
    from app.models import Product
    
    print("Testing database query directly...")
    
    # Create database session
    db = SessionLocal()
    
    try:
        # Test basic query
        print("Testing basic Product query...")
        products = db.query(Product).limit(5).all()
        print(f"SUCCESS: Query returned {len(products)} products")
        
        # Test query with count
        print("Testing count query...")
        count = db.query(Product).count()
        print(f"SUCCESS: Product count is {count}")
        
        print("Database operations working correctly!")
        
    except Exception as e:
        print(f"ERROR in database query: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        db.close()
    
    print("Database test completed successfully")
    
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()