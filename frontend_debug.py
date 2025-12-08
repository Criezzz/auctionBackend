#!/usr/bin/env python3
"""
Frontend-Backend Debug Script
This script simulates exactly what the frontend does to identify the exact issue
"""
import json
import sys
import os
import requests

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal
from app import models
from app.auth import get_password_hash, create_access_token, create_refresh_token

BASE_URL = "http://127.0.0.1:8000"

def simulate_frontend_login():
    """Simulate frontend login flow"""
    print("=== Simulating Frontend Login ===")
    
    # 1. Frontend makes login request
    login_data = {
        "username": "admin",
        "password": "Admin123@"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
        print(f"Login Status: {response.status_code}")
        print(f"Login Response: {response.text}")
        
        if response.status_code == 200:
            tokens = response.json()
            print("\n✓ Frontend receives these tokens:")
            print(f"access_token: {tokens['access_token'][:50]}...")
            print(f"refresh_token: {tokens['refresh_token'][:50]}...")
            print(f"token_type: {tokens['token_type']}")
            print(f"expires_in: {tokens['expires_in']}")
            
            # 2. Frontend stores tokens in localStorage (we'll simulate this)
            stored_tokens = {
                "access_token": tokens["access_token"],
                "refresh_token": tokens["refresh_token"],
                "token_type": tokens["token_type"],
                "expires_in": tokens["expires_in"]
            }
            
            print(f"\nTokens stored in localStorage: {json.dumps(stored_tokens, indent=2)}")
            
            return stored_tokens
        else:
            print("❌ Login failed")
            return None
            
    except Exception as e:
        print(f"❌ Login error: {e}")
        return None

def simulate_frontend_auth_me_request(stored_tokens):
    """Simulate frontend /auth/me request with stored tokens"""
    print("\n=== Simulating Frontend /auth/me Request ===")
    
    # 3. Frontend retrieves tokens from localStorage
    access_token = stored_tokens.get("access_token")
    print(f"Retrieved access_token from localStorage: {access_token[:50]}...")
    
    # 4. Frontend adds Authorization header
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    print(f"Request Headers: {headers}")
    
    try:
        # 5. Frontend sends request
        response = requests.get(f"{BASE_URL}/auth/me", headers=headers)
        print(f"/auth/me Status: {response.status_code}")
        print(f"/auth/me Response: {response.text}")
        
        if response.status_code == 200:
            print("✅ Frontend /auth/me SUCCESS!")
            return True
        else:
            print("❌ Frontend /auth/me FAILED!")
            return False
            
    except Exception as e:
        print(f"❌ /auth/me error: {e}")
        return False

def test_token_manually():
    """Test token manually by creating our own JWT"""
    print("\n=== Testing Manual Token Creation ===")
    
    db = SessionLocal()
    try:
        user = db.query(models.Account).filter(models.Account.username == "admin").first()
        if user:
            print(f"Found admin user: {user.username} (activated: {user.activated})")
            
            # Create tokens manually like the backend does
            manual_access_token = create_access_token(
                data={"sub": user.username, "user_id": user.account_id}
            )
            manual_refresh_token = create_refresh_token(
                data={"sub": user.username, "user_id": user.account_id}
            )
            
            print(f"Manual access token: {manual_access_token[:50]}...")
            
            # Test with manual token
            headers = {"Authorization": f"Bearer {manual_access_token}"}
            response = requests.get(f"{BASE_URL}/auth/me", headers=headers)
            print(f"Manual token test status: {response.status_code}")
            print(f"Manual token test response: {response.text}")
            
    finally:
        db.close()

def test_cors_and_headers():
    """Test CORS and header issues"""
    print("\n=== Testing CORS and Headers ===")
    
    # Test with different header combinations
    test_cases = [
        {
            "name": "Standard Bearer token",
            "headers": {"Authorization": "Bearer test_token"}
        },
        {
            "name": "With Content-Type",
            "headers": {
                "Authorization": "Bearer test_token",
                "Content-Type": "application/json"
            }
        },
        {
            "name": "With Accept",
            "headers": {
                "Authorization": "Bearer test_token",
                "Accept": "application/json"
            }
        },
        {
            "name": "All headers",
            "headers": {
                "Authorization": "Bearer test_token",
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
        }
    ]
    
    for test_case in test_cases:
        print(f"\nTesting {test_case['name']}:")
        try:
            response = requests.get(f"{BASE_URL}/auth/me", headers=test_case['headers'])
            print(f"  Status: {response.status_code} (Expected: 401 for invalid token)")
            if response.status_code != 401:
                print(f"  Response: {response.text[:100]}...")
        except Exception as e:
            print(f"  Error: {e}")

def main():
    print("Frontend-Backend Authentication Debug")
    print("=" * 50)
    
    # Test 1: Simulate complete frontend flow
    stored_tokens = simulate_frontend_login()
    if stored_tokens:
        success = simulate_frontend_auth_me_request(stored_tokens)
        if success:
            print("\n✅ FRONTEND-BACKEND FLOW WORKS CORRECTLY!")
            print("The issue might be in the frontend token storage/retrieval")
        else:
            print("\n❌ FRONTEND-BACKEND FLOW FAILS!")
            print("Issue identified in the authentication flow")
    
    # Test 2: Manual token creation
    test_token_manually()
    
    # Test 3: CORS and header testing
    test_cors_and_headers()
    
    print("\n" + "=" * 50)
    print("DEBUG COMPLETE")
    print("Check the results above to identify the exact issue.")

if __name__ == "__main__":
    main()