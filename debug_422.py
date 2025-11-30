#!/usr/bin/env python3
import requests
import json
import time

def test_otp_422_error():
    print("Testing OTP 422 error...")
    
    # Test data
    username = f"test{int(time.time())}"
    email = f"{username}@test.com"
    
    # Step 1: Register
    register_data = {
        "username": username,
        "email": email,
        "password": "StrongPass123!",
        "first_name": "Test",
        "last_name": "User"
    }
    
    print("1. Registering user...")
    response = requests.post("http://127.0.0.1:8000/auth/register", json=register_data)
    print(f"   Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        otp_token = data.get('otp_token')
        print(f"   OTP Token received: {'Yes' if otp_token else 'No'}")
        
        if otp_token:
            print(f"   Token length: {len(otp_token)}")
            
            # Step 2: Test verification with otp_token
            print("2. Testing verification with otp_token...")
            verify_data = {
                "otp_code": "000000",  # Wrong code
                "otp_token": otp_token,
                "username": username
            }
            
            print("   Sending verification request...")
            verify_response = requests.post("http://127.0.0.1:8000/auth/register/verify", json=verify_data)
            print(f"   Status: {verify_response.status_code}")
            
            if verify_response.status_code == 422:
                error = verify_response.json()
                print(f"   ERROR 422: {error}")
                return "422_error"
            elif verify_response.status_code == 400:
                print("   Good: 400 error (wrong OTP code)")
                return "success"
            else:
                print(f"   Unexpected: {verify_response.text}")
                return "unexpected"
        else:
            print("   ERROR: No otp_token in response!")
            return "no_token"
    else:
        print(f"   Registration failed: {response.text}")
        return "registration_failed"

if __name__ == "__main__":
    result = test_otp_422_error()
    print(f"\nResult: {result}")
    
    if result == "422_error":
        print("CONFIRMED: 422 error is happening")
        print("This means otp_token is null or invalid")
    elif result == "success":
        print("SUCCESS: OTP flow is working correctly")
        print("The issue is in frontend implementation")
    else:
        print(f"OTHER ISSUE: {result}")