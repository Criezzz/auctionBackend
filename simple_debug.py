#!/usr/bin/env python3
"""
Simple frontend-backend debug without unicode characters
"""
import json
import requests

BASE_URL = "http://127.0.0.1:8000"

def test_login_and_auth():
    print("=== Testing Login and /auth/me Flow ===")
    
    # Step 1: Login
    login_data = {"username": "admin", "password": "Admin123@"}
    try:
        response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
        print(f"Login status: {response.status_code}")
        
        if response.status_code == 200:
            tokens = response.json()
            access_token = tokens["access_token"]
            print(f"Access token: {access_token[:50]}...")
            
            # Step 2: Test /auth/me with the token
            headers = {"Authorization": f"Bearer {access_token}"}
            me_response = requests.get(f"{BASE_URL}/auth/me", headers=headers)
            print(f"/auth/me status: {me_response.status_code}")
            print(f"/auth/me response: {me_response.text[:200]}...")
            
            if me_response.status_code == 200:
                print("SUCCESS: Backend authentication works correctly!")
                print("Issue is in frontend token handling")
                return True
            else:
                print("FAILURE: Backend rejecting valid token")
                return False
        else:
            print("Login failed")
            return False
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_different_scenarios():
    print("\n=== Testing Different Scenarios ===")
    
    # Get a valid token first
    login_response = requests.post(f"{BASE_URL}/auth/login", json={"username": "admin", "password": "Admin123@"})
    if login_response.status_code != 200:
        print("Could not get valid token")
        return
    
    tokens = login_response.json()
    access_token = tokens["access_token"]
    
    scenarios = [
        {
            "name": "Bearer token with space",
            "headers": {"Authorization": f"Bearer {access_token}"}
        },
        {
            "name": "Bearer token no space",
            "headers": {"Authorization": f"Bearer{access_token}"}
        },
        {
            "name": "Token only (no Bearer)",
            "headers": {"Authorization": access_token}
        },
        {
            "name": "With Content-Type",
            "headers": {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
        },
        {
            "name": "With Accept",
            "headers": {
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/json"
            }
        }
    ]
    
    for scenario in scenarios:
        print(f"\nTesting {scenario['name']}:")
        try:
            response = requests.get(f"{BASE_URL}/auth/me", headers=scenario['headers'])
            print(f"  Status: {response.status_code}")
            if response.status_code != 200:
                print(f"  Error: {response.text[:100]}...")
        except Exception as e:
            print(f"  Exception: {e}")

def check_token_expiration():
    print("\n=== Checking Token Expiration ===")
    
    # Login and get token
    login_response = requests.post(f"{BASE_URL}/auth/login", json={"username": "admin", "password": "Admin123@"})
    if login_response.status_code == 200:
        tokens = login_response.json()
        access_token = tokens["access_token"]
        expires_in = tokens["expires_in"]
        
        print(f"Token expires in: {expires_in} seconds ({expires_in/60:.1f} minutes)")
        
        # Decode JWT manually to check expiration
        import base64
        import json
        
        try:
            # JWT structure: header.payload.signature
            parts = access_token.split('.')
            payload = parts[1]
            # Add padding if needed
            payload += '=' * (4 - len(payload) % 4)
            decoded = base64.b64decode(payload)
            payload_data = json.loads(decoded)
            
            print(f"Token payload: {payload_data}")
            
            # Check if token is expired
            import time
            current_time = time.time()
            exp_time = payload_data.get('exp', 0)
            
            if current_time < exp_time:
                time_left = exp_time - current_time
                print(f"Token valid for {time_left:.1f} more seconds")
            else:
                print("Token is expired!")
                
        except Exception as e:
            print(f"Could not decode token: {e}")

def main():
    print("Simple Frontend-Backend Debug")
    print("=" * 40)
    
    # Test main flow
    works = test_login_and_auth()
    
    if works:
        print("\n" + "=" * 40)
        print("TESTING DIFFERENT HEADER FORMATS")
        test_different_scenarios()
        
        print("\n" + "=" * 40)
        check_token_expiration()
        
        print("\n" + "=" * 40)
        print("CONCLUSION:")
        print("- Backend authentication works correctly")
        print("- Issue is likely in frontend token storage/retrieval")
        print("- Check browser localStorage for token corruption")
    else:
        print("\n" + "=" * 40)
        print("Backend authentication has issues")

if __name__ == "__main__":
    main()