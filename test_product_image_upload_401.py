#!/usr/bin/env python3
"""
Test script to debug 401 error when uploading product with images
"""
import requests
import json
import os
from pathlib import Path

# Configuration
BASE_URL = "http://localhost:8000"
API_PREFIX = ""

def test_login():
    """Login and get access token"""
    print("Testing login...")
    
    login_data = {
        "username": "testuser",
        "password": "password123"
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
    print("\\nTesting product upload with images...")
    
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
        
        print(f"\\nResponse status: {response.status_code}")
        print(f"Response headers: {dict(response.headers)}")
        print(f"Response content: {response.text}")
        
        if response.status_code == 200:
            print("Product with image uploaded successfully!")
            result = response.json()
            print(f"Product ID: {result.get('product_id')}")
            print(f"Image URL: {result.get('image_url')}")
        elif response.status_code == 401:
            print("401 Unauthorized - Token issue detected!")
            print("This confirms the authentication problem with multipart upload")
        else:
            print(f"Unexpected status code: {response.status_code}")
            
    except Exception as e:
        print(f"Upload error: {e}")
    finally:
        # Clean up
        if os.path.exists(image_path):
            os.remove(image_path)

def test_token_validation():
    """Test if token is valid by calling a simple endpoint"""
    print("\\nTesting token validation...")
    
    access_token = test_login()
    if not access_token:
        return
    
    try:
        # Test /auth/me endpoint
        headers = {
            "Authorization": f"Bearer {access_token}"
        }
        
        response = requests.get(
            f"{BASE_URL}{API_PREFIX}/auth/me",
            headers=headers,
            timeout=10
        )
        
        print(f"Token validation status: {response.status_code}")
        if response.status_code == 200:
            user_data = response.json()
            print(f"Token valid. User: {user_data.get('username')}")
        else:
            print(f"Token invalid: {response.text}")
            
    except Exception as e:
        print(f"Token validation error: {e}")

def test_product_without_images():
    """Test creating product without images (should work)"""
    print("\\nTesting product upload without images...")
    
    access_token = test_login()
    if not access_token:
        return
    
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
            print("Product without image uploaded successfully!")
        else:
            print(f"Unexpected status code: {response.status_code}")
            
    except Exception as e:
        print(f"No-image upload error: {e}")

def main():
    """Main test function"""
    print("Starting Product Image Upload 401 Debug Test")
    print("=" * 50)
    
    # Test 1: Basic token validation
    test_token_validation()
    
    # Test 2: Product without images (should work)
    test_product_without_images()
    
    # Test 3: Product with images (problematic)
    access_token = test_login()
    test_upload_product_with_images(access_token)
    
    print("\\n" + "=" * 50)
    print("Debug Summary:")
    print("1. If /auth/me works but /products/register-with-images fails with 401:")
    print("   -> Issue with multipart/form-data authentication")
    print("2. If both fail with 401:")
    print("   -> Issue with token generation or validation")
    print("3. If /products/register works but /products/register-with-images fails:")
    print("   -> Specific issue with image upload endpoint")

if __name__ == "__main__":
    main()