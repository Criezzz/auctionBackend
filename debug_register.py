#!/usr/bin/env python3
"""
Debug register endpoint with detailed error messages
"""
import requests
import json

def test_register():
    url = "http://127.0.0.1:8000/auth/register"
    
    # Test data with strong password
    data = {
        "username": "testdebug123",
        "email": "testdebug@gmail.com",
        "password": "StrongPass123!",
        "first_name": "Test",
        "last_name": "Debug",
        "phone_num": "0123456789",
        "date_of_birth": "2005-01-06T00:00:00"
    }
    
    print("=" * 60)
    print("DEBUG: Testing /auth/register endpoint")
    print("=" * 60)
    print(f"\nRequest URL: {url}")
    print(f"\nRequest Body:")
    print(json.dumps(data, indent=2))
    print("\n" + "=" * 60)
    
    try:
        response = requests.post(url, json=data, timeout=10)
        
        print(f"\nResponse Status Code: {response.status_code}")
        print(f"\nResponse Headers:")
        for key, value in response.headers.items():
            if 'cors' in key.lower() or 'access-control' in key.lower():
                print(f"  {key}: {value}")
        
        print(f"\nResponse Body:")
        try:
            print(json.dumps(response.json(), indent=2))
        except:
            print(response.text)
        
        print("\n" + "=" * 60)
        
        if response.status_code == 200:
            print("✅ SUCCESS - Registration completed")
        elif response.status_code == 400:
            print("⚠️  VALIDATION ERROR - Check input data")
        elif response.status_code == 500:
            print("❌ SERVER ERROR - Check backend logs in terminal")
        else:
            print(f"⚠️  UNEXPECTED STATUS CODE: {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print("❌ ERROR: Cannot connect to server")
        print("   Make sure server is running: fastapi dev .\\app\\main.py")
    except Exception as e:
        print(f"❌ ERROR: {type(e).__name__}: {e}")
    
    print("=" * 60)

if __name__ == "__main__":
    test_register()
