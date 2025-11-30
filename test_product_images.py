#!/usr/bin/env python3
"""
Test script to verify Product image fields are working correctly
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__)))

from app.schemas import ProductCreate, Product
from app.models import Product as ProductModel
import json

def test_product_image_schemas():
    print("Testing Product schema with image fields...")
    
    # Test ProductCreate with image fields
    product_data = {
        "product_name": "Test Figure",
        "product_description": "A test collectible figure",
        "product_type": "static",
        "image_url": "https://example.com/image.jpg",
        "additional_images": [
            "https://example.com/image1.jpg",
            "https://example.com/image2.jpg"
        ]
    }
    
    try:
        product_create = ProductCreate(**product_data)
        print(f"✅ ProductCreate schema: SUCCESS")
        print(f"   Product Name: {product_create.product_name}")
        print(f"   Image URL: {product_create.image_url}")
        print(f"   Additional Images: {product_create.additional_images}")
    except Exception as e:
        print(f"❌ ProductCreate schema: FAILED - {e}")
        return False
    
    # Test Product schema with image fields
    try:
        product = Product(**product_data, **{
            "product_id": 1,
            "shipping_status": "pending",
            "approval_status": "pending",
            "rejection_reason": None,
            "suggested_by_user_id": None,
            "created_at": "2024-01-01T00:00:00",
            "updated_at": None
        })
        print(f"✅ Product schema: SUCCESS")
        print(f"   Product ID: {product.product_id}")
        print(f"   Image URL: {product.image_url}")
        print(f"   Additional Images: {product.additional_images}")
    except Exception as e:
        print(f"❌ Product schema: FAILED - {e}")
        return False
    
    return True

def test_json_serialization():
    print("\nTesting JSON serialization for additional_images...")
    
    # Test converting list to JSON string (as done in create_product)
    images_list = ["url1.jpg", "url2.jpg", "url3.jpg"]
    try:
        json_string = json.dumps(images_list)
        print(f"✅ List to JSON: SUCCESS")
        print(f"   Input: {images_list}")
        print(f"   JSON: {json_string}")
        
        # Test converting back from JSON to list
        parsed_list = json.loads(json_string)
        print(f"✅ JSON to List: SUCCESS")
        print(f"   Parsed: {parsed_list}")
        
        if parsed_list == images_list:
            print(f"✅ Round-trip conversion: SUCCESS")
        else:
            print(f"❌ Round-trip conversion: FAILED")
            return False
            
    except Exception as e:
        print(f"❌ JSON serialization: FAILED - {e}")
        return False
    
    return True

def test_model_fields():
    print("\nTesting Product model fields...")
    
    try:
        # Check if the model has the new fields
        product_model = ProductModel()
        
        # Check if image_url field exists
        if hasattr(product_model, 'image_url'):
            print(f"✅ Product model has image_url field")
        else:
            print(f"❌ Product model missing image_url field")
            return False
            
        # Check if additional_images field exists
        if hasattr(product_model, 'additional_images'):
            print(f"✅ Product model has additional_images field")
        else:
            print(f"❌ Product model missing additional_images field")
            return False
            
    except Exception as e:
        print(f"❌ Product model test: FAILED - {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("=" * 60)
    print("TESTING PRODUCT IMAGE FIELDS")
    print("=" * 60)
    
    test1 = test_product_image_schemas()
    test2 = test_json_serialization()
    test3 = test_model_fields()
    
    print("\n" + "=" * 60)
    if test1 and test2 and test3:
        print("✅ ALL TESTS PASSED - Product image fields working correctly!")
    else:
        print("❌ SOME TESTS FAILED - Please check the errors above")
    print("=" * 60)