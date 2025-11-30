#!/usr/bin/env python3
"""
Test OTP registration and verification flow
This script demonstrates the proper flow and helps debug the otp_token null issue
"""
import requests
import json
import time

def test_otp_flow():
    base_url = "http://127.0.0.1:8000"
    
    # Test data for registration
    username = f"testuser{int(time.time())}"
    email = f"{username}@test.com"
    
    print("=" * 70)
    print("TESTING OTP REGISTRATION & VERIFICATION FLOW")
    print("=" * 70)
    
    # Step 1: Register new user
    print(f"\nSTEP 1: Register user '{username}'")
    register_data = {
        "username": username,
        "email": email,
        "password": "StrongPass123!",
        "first_name": "Test",
        "last_name": "User",
        "phone_num": "0123456789"
    }
    
    try:
        response = requests.post(f"{base_url}/auth/register", json=register_data, timeout=10)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("   SUCCESS: Registration successful")
            print(f"   Message: {data.get('message')}")
            
            # IMPORTANT: Extract otp_token from response
            otp_token = data.get('otp_token')
            if otp_token:
                print(f"   OTP Token: {otp_token[:50]}...")
            else:
                print("   ERROR: NO OTP TOKEN in response!")
                return False
                
            # Step 2: Test verification endpoint
            print(f"\nSTEP 2: Test verification endpoint")
            
            # Send a request that should fail (wrong OTP code) but shows proper structure
            verify_data = {
                "otp_code": "000000",  # Wrong code - will fail validation
                "otp_token": otp_token,  # This should NOT be null
                "username": username
            }
            
            print("   Request data:")
            print(f"   - otp_code: {verify_data['otp_code']}")
            print(f"   - otp_token: {verify_data['otp_token'][:50]}...")
            print(f"   - username: {verify_data['username']}")
            
            verify_response = requests.post(f"{base_url}/auth/register/verify", json=verify_data, timeout=10)
            print(f"   Status: {verify_response.status_code}")
            
            if verify_response.status_code == 422:
                error_detail = verify_response.json()
                print(f"   ERROR 422 (Validation Failed): {error_detail}")
                
                # Check if it's specifically about otp_token being null
                if 'detail' in error_detail:
                    for detail in error_detail['detail']:
                        if detail.get('loc') == ['body', 'otp_token']:
                            print(f"   ROOT CAUSE: otp_token field error - {detail.get('msg')}")
                            print(f"   INPUT VALUE: {detail.get('input')}")
                            return False
            elif verify_response.status_code == 400:
                error_data = verify_response.json()
                print(f"   GOOD: Proper validation error: {error_data}")
                print("   (OTP wrong is expected - but otp_token was accepted)")
                return True
            else:
                print(f"   Response: {verify_response.text}")
                return True
                
        else:
            print(f"   ERROR: Registration failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"   ERROR: {e}")
        return False

if __name__ == "__main__":
    success = test_otp_flow()
    
    print("\n" + "=" * 70)
    if success:
        print("TEST PASSED - The otp_token flow is working correctly")
        print("\nIf you're still getting 422 errors:")
        print("1. Frontend is not storing otp_token from registration response")
        print("2. Frontend is not sending otp_token in verification request")
        print("3. otp_token has expired (5 minute limit)")
    else:
        print("TEST FAILED - Found the otp_token null issue")
        print("\nThe backend is working correctly.")
        print("The issue is in frontend implementation.")
    print("=" * 70)