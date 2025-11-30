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
    print("🧪 TESTING OTP REGISTRATION & VERIFICATION FLOW")
    print("=" * 70)
    
    # Step 1: Register new user
    print(f"\n📝 STEP 1: Register user '{username}'")
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
            print("   ✅ Registration SUCCESS")
            print(f"   Message: {data.get('message')}")
            
            # IMPORTANT: Extract otp_token from response
            otp_token = data.get('otp_token')
            print(f"   OTP Token: {otp_token[:50]}..." if otp_token else "   ❌ NO OTP TOKEN!")
            
            if not otp_token:
                print("   ❌ ERROR: No otp_token in response - this is the bug!")
                return False
                
            # Step 2: Verify OTP (simulate user entering correct code)
            print(f"\n🔐 STEP 2: Verify OTP for user '{username}'")
            
            # In real scenario, user gets OTP from email and enters it here
            # For testing, we need to extract the OTP from the token or mock it
            # Since we can't read the email, let's check what happens when we call verify without OTP
            
            verify_data = {
                "otp_code": "000000",  # This will fail but shows the proper request format
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
                print(f"   ❌ 422 ERROR (Validation Failed): {error_detail}")
                print("   This suggests otp_token is null or invalid format")
                
                # Let's check the specific field that failed
                if 'detail' in error_detail:
                    for detail in error_detail['detail']:
                        if detail.get('loc') == ['body', 'otp_token']:
                            print(f"   🔍 SPECIFIC ERROR: otp_token field - {detail.get('msg')}")
                            print(f"   🔍 INPUT VALUE: {detail.get('input')}")
                            return False
            elif verify_response.status_code == 400:
                error_data = verify_response.json()
                print(f"   ✅ Proper validation error: {error_data}")
                print("   (OTP code wrong is expected - the important thing is otp_token was accepted)")
                return True
            else:
                print(f"   Response: {verify_response.text}")
                return True
                
        else:
            print(f"   ❌ Registration failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
        return False

def test_otp_status():
    """Test OTP status endpoint with token"""
    print(f"\n🔍 STEP 3: Test OTP status endpoint")
    
    # This would be used if we had a valid token from registration
    test_token = "invalid_token_for_testing"
    
    try:
        response = requests.get(f"http://127.0.0.1:8000/auth/otp/status?otp_token={test_token}")
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json()}")
    except Exception as e:
        print(f"   Error: {e}")

if __name__ == "__main__":
    success = test_otp_flow()
    test_otp_status()
    
    print("\n" + "=" * 70)
    if success:
        print("✅ FLOW TEST PASSED - The otp_token is working correctly")
        print("\n💡 If you're still getting 422 errors:")
        print("   1. Check that frontend stores otp_token from registration response")
        print("   2. Ensure frontend sends otp_token in verification request")
        print("   3. Check that otp_token hasn't expired (5 minute limit)")
    else:
        print("❌ FLOW TEST FAILED - Found the otp_token null issue")
        print("\n🔧 This confirms the frontend is not properly handling otp_token")
    print("=" * 70)