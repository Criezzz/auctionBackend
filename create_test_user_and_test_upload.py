#!/usr/bin/env python3
"""
Create test user and test product image upload
"""
import requests
import json
import os

# Configuration
BASE_URL = "http://localhost:8000"
API_PREFIX = ""

def register_test_user():
    """Register a new test user"""
    print("Creating test user...")
    
    register_data = {
        "username": "testuser123",
        "email": "test@example.com",
        "password": "password123",
        "first_name": "Test",
        "last_name": "User",
        "phone_num": "+1234567890"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}{API_PREFIX}/auth/register",
            json=register_data,
            timeout=10
        )
        
        print(f"Register response status: {response.status_code}")
        print(f"Register response: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            otp_token = data.get("otp_token")
            print(f"User created successfully. OTP token: {otp_token[:20]}...")
            return otp_token
        else:
            print("Registration failed")
            return None
            
    except Exception as e:
        print(f"Registration error: {e}")
        return None

def verify_otp(otp_token, username="testuser123", otp_code="123456"):
    """Verify OTP code"""
    print(f"Verifying OTP for user: {username}")
    
    verify_data = {
        "otp_code": otp_code,
        "otp_token": otp_token,
        "username": username
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}{API_PREFIX}/auth/register/verify",
            json=verify_data,
            timeout=10
        )
        
        print(f"Verify response status: {response.status_code}")
        print(f"Verify response: {response.text}")
        
        if response.status_code == 200:
            print("OTP verified successfully!")
            return True
        else:
            print("OTP verification failed")
            return False
            
    except Exception as e:
        print(f"OTP verification error: {e}")
        return False

def login(username="testuser123", password="password123"):
    """Login and get access token"""
    print("Testing login...")
    
    login_data = {
        "username": username,
        "password": password
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}{API_PREFIX}/auth/login",
            json=login_data,
            timeout=10
        )
        
        print(f"Login response status: {response.status_code}")
        print(f"Login response: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            return data["access_token"]
        else:
            print("Login failed")
            return None
            
    except Exception as e:
        print(f"Login error: {e}")
        return None

def create_test_image():
    """Create a simple test image"""
    try:
        from PIL import Image, ImageDraw
        
        # Create a simple test image
        img = Image.new('RGB', (400, 300), color='red')
        draw = ImageDraw.Draw(img)
        
        # Add some text
        draw.text((150, 140), "TEST IMAGE", fill='white')
        
        # Save image
        image_path = "test_image.jpg"
        img.save(image_path, "JPEG")
        print(f"Created test image: {image_path}")
        return image_path
        
    except ImportError:
        print("PIL not available, creating dummy file...")
        # Create a dummy file for testing
        image_path = "test_image.jpg"
        with open(image_path, 'wb') as f:
            f.write(b"dummy image content")
        return image_path

def test_upload_product_with_images(access_token):
    """Test uploading product with images"""
    print("\nTesting product upload with images...")
    
    if not access_token:
        print("No access token available")
        return
    
    # Create test image
    image_path = create_test_image()
    
    if not os.path.exists(image_path):
        print("Test image not found")
        return
    
    try:
        # Prepare form data
        url = f"{BASE_URL}{API_PREFIX}/products/register-with-images"
        
        headers = {
            "Authorization": f"Bearer {access_token}"
        }
        
        files = {
            "main_image": ("test_image.jpg", open(image_path, "rb"), "image/jpeg")
        }
        
        data = {
            "product_name": "Test Product with Image",
            "product_description": "This is a test product uploaded with image",
            "product_type": "static"
        }
        
        print(f"Sending request to: {url}")
        print(f"Headers: {headers}")
        print(f"Form data: {data}")
        print(f"Files: {list(files.keys())}")
        
        response = requests.post(
            url,
            headers=headers,
            files=files,
            data=data,
            timeout=30
        )
        
        print(f"\nResponse status: {response.status_code}")
        print(f"Response headers: {dict(response.headers)}")
        print(f"Response content: {response.text}")
        
        if response.status_code == 200:
            print("SUCCESS: Product with image uploaded successfully!")
            result = response.json()
            print(f"Product ID: {result.get('product_id')}")
            print(f"Image URL: {result.get('image_url')}")
        elif response.status_code == 401:
            print("401 ERROR: Token issue detected!")
            print("This confirms the authentication problem with multipart upload")
            print("The issue is with how Bearer token is handled in multipart/form-data requests")
        else:
            print(f"Unexpected status code: {response.status_code}")
            
    except Exception as e:
        print(f"Upload error: {e}")
    finally:
        # Clean up
        if os.path.exists(image_path):
            os.remove(image_path)

def test_product_without_images(access_token):
    """Test creating product without images (should work)"""
    print("\nTesting product upload without images...")
    
    try:
        url = f"{BASE_URL}{API_PREFIX}/products/register"
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        data = {
            "product_name": "Test Product No Image",
            "product_description": "This is a test product without image",
            "product_type": "static"
        }
        
        response = requests.post(
            url,
            headers=headers,
            json=data,
            timeout=10
        )
        
        print(f"No-image upload status: {response.status_code}")
        print(f"No-image response: {response.text}")
        
        if response.status_code == 200:
            print("SUCCESS: Product without image uploaded successfully!")
        else:
            print(f"ERROR: Unexpected status code: {response.status_code}")
            
    except Exception as e:
        print(f"No-image upload error: {e}")

def main():
    """Main test function"""
    print("Creating Test User and Testing Product Image Upload")
    print("=" * 60)
    
    # Step 1: Register test user
    otp_token = register_test_user()
    
    if otp_token:
        # Step 2: Verify OTP (assuming OTP is 123456)
        if verify_otp(otp_token):
            print("\nUser activated successfully!")
            
            # Step 3: Login
            access_token = login()
            
            if access_token:
                print("\nLogin successful!")
                
                # Step 4: Test product without images (baseline)
                test_product_without_images(access_token)
                
                # Step 5: Test product with images (the problematic one)
                test_upload_product_with_images(access_token)
                
                print("\n" + "=" * 60)
                print("ANALYSIS:")
                print("1. If product without image works but with image fails 401:")
                print("   -> CONFIRMED: Issue is with multipart/form-data + Bearer token")
                print("2. If both fail with 401:")
                print("   -> Issue with token or user activation")
                print("3. If both work:")
                print("   -> Issue might be frontend-specific")
            else:
                print("Login failed after OTP verification")
        else:
            print("OTP verification failed")
    else:
        print("User registration failed")

if __name__ == "__main__":
    main()