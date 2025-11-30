#!/usr/bin/env python3
"""
Simple test to check if image upload endpoint returns 401
"""
import requests
import json
import os

# Configuration
BASE_URL = "http://localhost:8000"

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
        return image_path
        
    except ImportError:
        # Create a dummy file for testing
        image_path = "test_image.jpg"
        with open(image_path, 'wb') as f:
            f.write(b"dummy image content")
        return image_path

def test_image_upload_401():
    """Test if image upload returns 401 without authentication"""
    print("Testing image upload without authentication (should return 401)...")
    
    image_path = create_test_image()
    
    if not os.path.exists(image_path):
        print("Test image not found")
        return
    
    try:
        url = f"{BASE_URL}/products/register-with-images"
        
        headers = {}  # No Authorization header
        
        with open(image_path, 'rb') as img_file:
            files = {
                "main_image": ("test_image.jpg", img_file, "image/jpeg")
            }
            
            data = {
                "product_name": "Test Product",
                "product_description": "Test Description",
                "product_type": "static"
            }
            
            response = requests.post(
                url,
                headers=headers,
                files=files,
                data=data,
                timeout=30
            )
        
        print(f"Response status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code in [401, 403]:
            print("CONFIRMED: Authentication required (401/403)")
        else:
            print(f"Unexpected status: {response.status_code}")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if os.path.exists(image_path):
            try:
                os.remove(image_path)
            except:
                pass  # Ignore file deletion errors

def test_normal_product_401():
    """Test if normal product creation returns 401 without authentication"""
    print("\nTesting normal product creation without authentication (should return 401)...")
    
    try:
        url = f"{BASE_URL}/products/register"
        
        headers = {}  # No Authorization header
        
        data = {
            "product_name": "Test Product",
            "product_description": "Test Description",
            "product_type": "static"
        }
        
        response = requests.post(
            url,
            headers=headers,
            json=data,
            timeout=10
        )
        
        print(f"Response status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 401:
            print("CONFIRMED: 401 Unauthorized without token (both endpoints behave the same)")
        else:
            print(f"Unexpected status: {response.status_code}")
            
    except Exception as e:
        print(f"Error: {e}")

def test_with_fake_token():
    """Test image upload with fake token"""
    print("\nTesting image upload with fake token (should return 401)...")
    
    image_path = create_test_image()
    
    if not os.path.exists(image_path):
        print("Test image not found")
        return
    
    try:
        url = f"{BASE_URL}/products/register-with-images"
        
        headers = {
            "Authorization": "Bearer fake_token_12345"
        }
        
        with open(image_path, 'rb') as img_file:
            files = {
                "main_image": ("test_image.jpg", img_file, "image/jpeg")
            }
            
            data = {
                "product_name": "Test Product",
                "product_description": "Test Description",
                "product_type": "static"
            }
            
            response = requests.post(
                url,
                headers=headers,
                files=files,
                data=data,
                timeout=30
            )
        
        print(f"Response status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code in [401, 403]:
            print("CONFIRMED: Authentication failed (401/403)")
        else:
            print(f"Unexpected status: {response.status_code}")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if os.path.exists(image_path):
            try:
                os.remove(image_path)
            except:
                pass  # Ignore file deletion errors

def main():
    """Main test function"""
    print("Testing 401 Error with Image Upload")
    print("=" * 40)
    
    # Test 1: No authentication
    test_image_upload_401()
    
    # Test 2: Normal product without auth
    test_normal_product_401()
    
    # Test 3: Invalid token
    test_with_fake_token()
    
    print("\n" + "=" * 40)
    print("CONCLUSION:")
    print("If all tests return 401, the issue is NOT with multipart/form-data")
    print("The issue is likely:")
    print("1. Frontend not sending token correctly")
    print("2. Token expired")
    print("3. User not authenticated properly")

if __name__ == "__main__":
    main()