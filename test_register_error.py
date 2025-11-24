#!/usr/bin/env python3
"""
Test script to reproduce the register endpoint 500 error
"""
import requests
import json
import sys

def test_register_endpoint():
    """Test both register endpoints and capture the error"""
    # Test data - use unique username
    unique_id = str(int(__import__("time").time()))
    data = {
        "username": f"newuser_{unique_id}",
        "email": f"test_{unique_id}@example.com", 
        "password": "Test123!",
        "first_name": "Test",
        "last_name": "User"
    }
    
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    endpoints = [
        ("/auth/register", "Auth Register (OTP enabled)"),
        ("/accounts/register", "Accounts Register (simple)")
    ]
    
    for endpoint, description in endpoints:
        url = f"http://127.0.0.1:8000{endpoint}"
        
        try:
            print(f"\n{'='*50}")
            print(f"Testing {description}: {url}")
            print(f"Request data: {json.dumps(data, indent=2)}")
            
            response = requests.post(url, json=data, headers=headers, timeout=10)
            
            print(f"\nResponse Status Code: {response.status_code}")
            print(f"Response Headers: {dict(response.headers)}")
            
            try:
                response_json = response.json()
                print(f"Response Body: {json.dumps(response_json, indent=2)}")
            except json.JSONDecodeError:
                print(f"Response Body (raw): {response.text}")
                
            if response.status_code == 500:
                print("\n*** 500 ERROR DETECTED ***")
                print("This is the endpoint causing the issue!")
                return response
            
        except requests.exceptions.ConnectionError:
            print("ERROR: Could not connect to server. Is it running on port 8000?")
            return None
        except Exception as e:
            print(f"ERROR: {str(e)}")
            return None
    
    print("\n*** No 500 errors detected - both endpoints working fine ***")
    return None

if __name__ == "__main__":
    test_register_endpoint()