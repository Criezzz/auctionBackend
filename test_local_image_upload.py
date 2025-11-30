#!/usr/bin/env python3
"""
Test local image upload system
"""
import requests
import json
import os
from pathlib import Path

def test_image_upload():
    """Test image upload functionality"""
    
    # First, login to get access token
    print("=" * 60)
    print("TESTING LOCAL IMAGE UPLOAD SYSTEM")
    print("=" * 60)
    
    # Login
    login_url = "http://127.0.0.1:8000/auth/login"
    login_data = {
        "username": "namtotet205",
        "password": "StrongPass123!"
    }
    
    print("\n1. Logging in...")
    try:
        response = requests.post(login_url, json=login_data, timeout=10)
        if response.status_code == 200:
            tokens = response.json()
            access_token = tokens["access_token"]
            print("✅ Login successful")
        else:
            print(f"❌ Login failed: {response.status_code}")
            print(response.text)
            return
    except Exception as e:
        print(f"❌ Login error: {e}")
        return
    
    # Test supported formats
    print("\n2. Testing supported image formats...")
    formats_url = "http://127.0.0.1:8000/images/formats"
    headers = {"Authorization": f"Bearer {access_token}"}
    
    try:
        response = requests.get(formats_url, headers=headers, timeout=10)
        if response.status_code == 200:
            formats = response.json()
            print(f"✅ Supported formats: {formats['supported_formats']}")
            print(f"✅ Max file size: {formats['max_file_size_mb']}MB")
            print(f"✅ Max files per request: {formats['max_files_per_request']}")
        else:
            print(f"❌ Failed to get formats: {response.status_code}")
    except Exception as e:
        print(f"❌ Error getting formats: {e}")
    
    # Create sample image data for testing
    print("\n3. Creating sample images for testing...")
    
    # Create a simple 1x1 pixel JPEG image in base64
    jpeg_base64 = "/9j/4AAQSkZJRgABAQEAYABgAAD/2wBDAAEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQH/2wBDAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQH/wAARCAABAAEDASIAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAv/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/8QAFQEBAQAAAAAAAAAAAAAAAAAAAAX/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIRAxEAPwDdfwAADQAA/8QAFQEBAQAAAAAAAAAAAAAAAAAAAAX/2gAIAQEAAwCs/wD/ABAA"
    
    import base64
    jpeg_data = base64.b64decode(jpeg_base64)
    
    # Create temporary image files
    test_dir = Path("test_images")
    test_dir.mkdir(exist_ok=True)
    
    test_files = []
    for i in range(3):
        test_file = test_dir / f"test_image_{i}.jpg"
        test_file.write_bytes(jpeg_data)
        test_files.append(test_file)
    
    print(f"✅ Created {len(test_files)} test image files")
    
    # Test single image upload
    print("\n4. Testing single image upload...")
    upload_url = "http://127.0.0.1:8000/images/upload"
    
    try:
        with open(test_files[0], 'rb') as f:
            files = {'file': ('test_image.jpg', f, 'image/jpeg')}
            data = {'product_id': '100'}  # Test product ID
            
            response = requests.post(upload_url, files=files, data=data, headers=headers, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                print("✅ Single image upload successful")
                print(f"   Image path: {result['image_path']}")
                print(f"   Image URL: {result['image_url']}")
                print(f"   File size: {result['size_bytes']} bytes")
            else:
                print(f"❌ Single upload failed: {response.status_code}")
                print(response.text)
                
    except Exception as e:
        print(f"❌ Single upload error: {e}")
    
    # Test multiple image upload
    print("\n5. Testing multiple image upload...")
    
    try:
        files = []
        for i, test_file in enumerate(test_files[1:], 1):
            files.append(('files', (f'test_image_{i}.jpg', open(test_file, 'rb'), 'image/jpeg')))
        
        data = {'product_id': '101'}  # Different product ID
        
        response = requests.post(
            "http://127.0.0.1:8000/images/upload/multiple", 
            files=files, 
            data=data, 
            headers=headers, 
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Multiple image upload successful")
            print(f"   Total uploaded: {result['total_uploaded']}")
            print(f"   Total failed: {result['total_failed']}")
            for img in result['images']:
                if img['success']:
                    print(f"   ✅ {img['filename']}: {img['image_url']}")
                else:
                    print(f"   ❌ {img['filename']}: {img['error']}")
        else:
            print(f"❌ Multiple upload failed: {response.status_code}")
            print(response.text)
            
        # Close files
        for _, file_tuple in files:
            file_tuple[1].close()
            
    except Exception as e:
        print(f"❌ Multiple upload error: {e}")
    
    # Test listing images
    print("\n6. Testing image listing...")
    
    try:
        response = requests.get("http://127.0.0.1:8000/images/list", headers=headers, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Image listing successful")
            print(f"   Total images: {result['total_count']}")
            print(f"   Storage path: {result['storage_path']}")
            
            for img in result['images'][:5]:  # Show first 5
                print(f"   📸 {img['filename']}: {img['size_bytes']} bytes")
                print(f"      URL: {img['image_url']}")
        else:
            print(f"❌ Image listing failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Image listing error: {e}")
    
    # Test product creation with images
    print("\n7. Testing product creation with images...")
    
    try:
        product_url = "http://127.0.0.1:8000/products/register-with-images"
        
        # Prepare multipart form data
        data = {
            'product_name': 'Test Product with Images',
            'product_description': 'Testing local image upload functionality',
            'product_type': 'static'
        }
        
        files = {}
        if test_files[0].exists():
            files['main_image'] = ('test_main.jpg', open(test_files[0], 'rb'), 'image/jpeg')
        if test_files[1].exists():
            files['additional_images'] = ('test_additional.jpg', open(test_files[1], 'rb'), 'image/jpeg')
        
        response = requests.post(
            product_url, 
            data=data, 
            files=files, 
            headers=headers, 
            timeout=30
        )
        
        if response.status_code == 200:
            product = response.json()
            print("✅ Product creation with images successful")
            print(f"   Product ID: {product['product_id']}")
            print(f"   Product name: {product['product_name']}")
            print(f"   Main image: {product['image_url']}")
            if product.get('additional_images'):
                print(f"   Additional images: {len(product['additional_images'])}")
                for i, img_path in enumerate(product['additional_images']):
                    print(f"      {i+1}. {img_path}")
        else:
            print(f"❌ Product creation failed: {response.status_code}")
            print(response.text)
        
        # Close files
        for file_field, file_tuple in files.items():
            file_tuple[1].close()
            
    except Exception as e:
        print(f"❌ Product creation error: {e}")
    
    # Cleanup
    print("\n8. Cleaning up test files...")
    try:
        for test_file in test_files:
            if test_file.exists():
                test_file.unlink()
        if test_dir.exists():
            test_dir.rmdir()
        print("✅ Test files cleaned up")
    except Exception as e:
        print(f"⚠️  Cleanup warning: {e}")
    
    print("\n" + "=" * 60)
    print("LOCAL IMAGE UPLOAD TEST COMPLETED")
    print("=" * 60)

if __name__ == "__main__":
    test_image_upload()