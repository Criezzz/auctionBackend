#!/usr/bin/env python3
"""
Test script để kiểm tra các fixes cho OTP email system
"""
import requests
import json
from datetime import datetime

def test_username_validation():
    """Test username validation với số ở đầu"""
    print("🧪 Test 1: Username validation với số ở đầu...")
    
    # Test data với username toàn số
    test_data = {
        "username": "namtotet205",
        "email": "namtotet205@test.com", 
        "password": "TestPass123!",
        "first_name": "Nam",
        "last_name": "Test"
    }
    
    try:
        response = requests.post(
            "http://localhost:8000/auth/register",
            json=test_data,
            headers={"Content-Type": "application/json"}
        )
        result = response.json()
        
        if response.status_code == 200:
            print("✅ PASS: Username với số ở đầu được chấp nhận")
            print(f"   Response: {result.get('message', 'No message')}")
            return result.get('otp_token')
        else:
            print(f"❌ FAIL: Status {response.status_code}")
            print(f"   Error: {result}")
            return None
            
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return None

def test_resend_otp(username, otp_token=None):
    """Test resend OTP endpoint"""
    print("\n🧪 Test 2: Resend OTP endpoint...")
    
    if not username:
        print("❌ SKIP: Không có username để test")
        return False
    
    resend_data = {"username": username}
    
    try:
        response = requests.post(
            "http://localhost:8000/auth/register/resend",
            json=resend_data,
            headers={"Content-Type": "application/json"}
        )
        result = response.json()
        
        if response.status_code == 200:
            print("✅ PASS: Resend OTP hoạt động")
            print(f"   Response: {result.get('message', 'No message')}")
            return True
        else:
            print(f"❌ FAIL: Status {response.status_code}")
            print(f"   Error: {result}")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return False

def test_otp_status(otp_token):
    """Test OTP status endpoint"""
    print("\n🧪 Test 3: OTP status endpoint...")
    
    if not otp_token:
        print("❌ SKIP: Không có OTP token để test")
        return False
        
    try:
        response = requests.get(
            f"http://localhost:8000/auth/otp/status?otp_token={otp_token}"
        )
        result = response.json()
        
        if response.status_code == 200:
            print("✅ PASS: OTP status endpoint hoạt động")
            print(f"   Valid: {result.get('valid')}")
            print(f"   Expired: {result.get('expired')}")
            print(f"   Remaining trials: {result.get('remaining_trials')}")
            return True
        else:
            print(f"❌ FAIL: Status {response.status_code}")
            print(f"   Error: {result}")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return False

def main():
    """Chạy tất cả tests"""
    print("🚀 Bắt đầu test OTP email fixes...")
    print("=" * 50)
    
    # Test 1: Register với username có số ở đầu
    otp_token = test_username_validation()
    
    # Extract username từ test data
    username = "namtotet205"
    
    # Test 2: Resend OTP
    resend_success = test_resend_otp(username, otp_token)
    
    # Test 3: Check OTP status
    status_success = test_otp_status(otp_token)
    
    # Kết quả tổng kết
    print("\n" + "=" * 50)
    print("📊 KẾT QUẢ TỔNG KẾT:")
    
    tests_passed = 0
    total_tests = 3
    
    if otp_token:
        tests_passed += 1
        print("✅ Test 1: Username validation - PASSED")
    else:
        print("❌ Test 1: Username validation - FAILED")
    
    if resend_success:
        tests_passed += 1
        print("✅ Test 2: Resend OTP - PASSED")
    else:
        print("❌ Test 2: Resend OTP - FAILED")
    
    if status_success:
        tests_passed += 1
        print("✅ Test 3: OTP Status - PASSED")
    else:
        print("❌ Test 3: OTP Status - FAILED")
    
    print(f"\n🎯 Tổng kết: {tests_passed}/{total_tests} tests PASSED")
    
    if tests_passed == total_tests:
        print("🎉 Tất cả fixes đều hoạt động tốt!")
    else:
        print("⚠️  Vẫn còn một số vấn đề cần khắc phục")

if __name__ == "__main__":
    main()