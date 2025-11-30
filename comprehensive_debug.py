#!/usr/bin/env python3
"""
Comprehensive test for product registration with authentication
"""
import requests
import json

# Configuration
BASE_URL = "http://127.0.0.1:8000"

def register_and_login():
    """Register a test user and get authentication token"""
    print("1. Registering test user...")
    
    register_data = {
        "username": "testproductuser",
        "email": "testproduct@example.com",
        "password": "TestPass123!",
        "first_name": "Test",
        "last_name": "User"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/auth/register", json=register_data, timeout=10)
        print(f"Register status: {response.status_code}")
        print(f"Register response: {response.text}")
        
        if response.status_code == 200:
            print("Registration successful!")
            register_result = response.json()
            if 'otp_token' in register_result:
                print("OTP verification required")
                return None, None
            else:
                print("Registration completed successfully")
                return None, None
        else:
            print(f"Registration failed: {response.status_code}")
            return None, None
            
    except Exception as e:
        print(f"Registration error: {e}")
        return None, None

def test_products_endpoint():
    """Test the products endpoint with comprehensive error handling"""
    print("\n2. Testing products endpoint...")
    
    url = f"{BASE_URL}/products"
    
    try:
        response = requests.get(url, timeout=10)
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        print(f"Response Text: {response.text}")
        
        if response.status_code == 500:
            print("CONFIRMED: Still getting 500 error on products endpoint")
            try:
                response_json = response.json()
                print(f"Error details: {json.dumps(response_json, indent=2)}")
            except:
                print("Response is not valid JSON")
        else:
            print(f"Products endpoint status: {response.status_code}")
            
    except Exception as e:
        print(f"Exception testing products endpoint: {e}")

def test_product_register_with_data():
    """Test product registration with minimal data"""
    print("\n3. Testing product registration endpoint...")
    
    url = f"{BASE_URL}/products/register"
    
    # Minimal valid data
    data = {
        "product_name": "Test Figure",
        "product_description": "A test product",
        "product_type": "static"
    }
    
    try:
        response = requests.post(
            url,
            json=data,
            timeout=10
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Text: {response.text}")
        
        if response.status_code == 500:
            print("CONFIRMED: 500 error on product registration")
            try:
                response_json = response.json()
                print(f"Error details: {json.dumps(response_json, indent=2)}")
            except:
                print("Response is not valid JSON")
        elif response.status_code in [401, 403]:
            print("EXPECTED: Authentication required (401/403)")
        else:
            print(f"Unexpected status: {response.status_code}")
            
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    print("=" * 60)
    print("COMPREHENSIVE: Product Registration Debug")
    print("=" * 60)
    
    # Run tests
    register_and_login()
    test_products_endpoint()
    test_product_register_with_data()
    
    print("\n" + "=" * 60)
    print("Check the server terminal logs above for detailed error information")
    print("=" * 60)