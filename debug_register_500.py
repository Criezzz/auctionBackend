#!/usr/bin/env python3
"""
Debug script to reproduce and capture the 500 error for product registration
"""
import requests
import json
import traceback

# Configuration
BASE_URL = "http://127.0.0.1:8000"
API_PREFIX = ""

def test_product_register_without_auth():
    """Test product registration without authentication to get detailed error"""
    print("Testing product registration without authentication to get error details...")
    
    url = f"{BASE_URL}{API_PREFIX}/products/register"
    
    data = {
        "product_name": "Test Product Debug",
        "product_description": "Testing product registration for 500 error",
        "product_type": "static"
    }
    
    headers = {}
    
    try:
        response = requests.post(
            url,
            headers=headers,
            json=data,
            timeout=10
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        print(f"Response Text: {response.text}")
        
        if response.status_code == 500:
            print("\nCONFIRMED: 500 Internal Server Error!")
            print("This confirms the issue reported by the user.")
            
            try:
                response_json = response.json()
                print(f"Response JSON: {json.dumps(response_json, indent=2)}")
            except:
                print("Response is not valid JSON")
        else:
            print(f"Different status code: {response.status_code}")
            
    except Exception as e:
        print(f"Exception occurred: {e}")
        print("Full traceback:")
        traceback.print_exc()

def test_get_products():
    """Test if basic product listing works"""
    print("\nTesting GET /products endpoint...")
    
    url = f"{BASE_URL}{API_PREFIX}/products"
    
    try:
        response = requests.get(url, timeout=10)
        print(f"Status Code: {response.status_code}")
        print(f"Response Text: {response.text}")
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    print("=" * 60)
    print("DEBUG: Product Registration 500 Error")
    print("=" * 60)
    
    # Test basic endpoints to understand the issue
    test_get_products()
    test_product_register_without_auth()
    
    print("\n" + "=" * 60)
    print("Debug completed!")
    print("=" * 60)