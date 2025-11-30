#!/usr/bin/env python3
"""
Simple test for Product image fields
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__)))

def test_product_schemas():
    try:
        from app.schemas import ProductCreate, Product
        
        # Test data with image fields
        product_data = {
            "product_name": "Test Figure",
            "product_description": "A test collectible",
            "product_type": "static",
            "image_url": "https://example.com/image.jpg",
            "additional_images": ["url1.jpg", "url2.jpg"]
        }
        
        # Test ProductCreate
        product_create = ProductCreate(**product_data)
        print("SUCCESS: ProductCreate with image fields works")
        print(f"Image URL: {product_create.image_url}")
        print(f"Additional Images: {product_create.additional_images}")
        
        # Test Product
        product = Product(**product_data, **{
            "product_id": 1,
            "shipping_status": "pending",
            "approval_status": "pending",
            "rejection_reason": None,
            "suggested_by_user_id": None,
            "created_at": "2024-01-01T00:00:00",
            "updated_at": None
        })
        print("SUCCESS: Product schema with image fields works")
        return True
        
    except Exception as e:
        print(f"FAILED: {e}")
        return False

if __name__ == "__main__":
    print("Testing Product image fields...")
    success = test_product_schemas()
    if success:
        print("\nAll tests passed! Product image fields are working.")
    else:
        print("\nTests failed!")