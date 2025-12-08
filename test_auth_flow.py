#!/usr/bin/env python3
"""
Test script to debug authentication flow and identify the 401 Unauthorized error
"""
import json
import sys
import os

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    import requests
    print("OK Requests module imported successfully")
except ImportError as e:
    print(f"ERROR Import error: {e}")
    sys.exit(1)

BASE_URL = "http://127.0.0.1:8000"

def test_register():
    """Test user registration"""
    print("\n=== Testing Registration ===")
    
    register_data = {
        "username": "admin",
        "email": "admin@example.com",
        "password": "Admin123@",
        "first_name": "Admin",
        "last_name": "User"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/auth/register", json=register_data)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            print("OK Registration successful")
            print(f"OTP Token received: {'Yes' if result.get('otp_token') else 'No'}")
            return True
        else:
            print("ERROR Registration failed")
            return False
    except Exception as e:
        print(f"ERROR Registration error: {e}")
        return False

def test_login():
    """Test user login"""
    print("\n=== Testing Login ===")
    
    login_data = {
        "username": "admin",
        "password": "Admin123@"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            access_token = result.get("access_token")
            refresh_token = result.get("refresh_token")
            
            print("OK Login successful")
            print(f"Access token: {access_token[:50]}...")
            print(f"Refresh token: {refresh_token[:50]}...")
            
            return access_token, refresh_token
        else:
            print("ERROR Login failed")
            return None, None
    except Exception as e:
        print(f"ERROR Login error: {e}")
        return None, None

def test_auth_me(access_token):
    """Test /auth/me endpoint"""
    print("\n=== Testing /auth/me endpoint ===")
    
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    
    try:
        response = requests.get(f"{BASE_URL}/auth/me", headers=headers)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            print("OK /auth/me successful")
            print(f"User: {result.get('username')} ({result.get('email')})")
            print(f"Role: {result.get('role')}")
            print(f"Activated: {result.get('activated')}")
            return True
        else:
            print(f"ERROR /auth/me failed with status {response.status_code}")
            return False
    except Exception as e:
        print(f"ERROR /auth/me error: {e}")
        return False

def test_debug_token(access_token):
    """Test debug endpoint to verify token structure"""
    print("\n=== Testing Debug Token Endpoint ===")
    
    debug_data = {
        "token": access_token,
        "token_type": "access"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/auth/debug/verify-token", json=debug_data)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get("valid"):
                print("OK Token is valid")
                print(f"Payload: {result.get('payload', {})}")
            else:
                print(f"ERROR Token is invalid: {result.get('message')}")
        else:
            print("ERROR Debug endpoint failed")
    except Exception as e:
        print(f"ERROR Debug endpoint error: {e}")

def main():
    print("Testing Authentication Flow")
    print("=" * 40)
    
    # Test 1: Register user
    if not test_register():
        print("Cannot proceed - registration failed")
        return
    
    # Test 2: Login
    access_token, refresh_token = test_login()
    if not access_token:
        print("Cannot proceed - login failed")
        return
    
    # Test 3: Debug token structure
    test_debug_token(access_token)
    
    # Test 4: Test /auth/me endpoint
    if test_auth_me(access_token):
        print("\nOK All authentication tests passed!")
    else:
        print("\nERROR /auth/me test failed - this is the issue!")

if __name__ == "__main__":
    main()