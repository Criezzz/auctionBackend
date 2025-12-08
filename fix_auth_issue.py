#!/usr/bin/env python3
"""
Fix script to resolve authentication issues
This script will:
1. Check existing users in database
2. Create properly activated users
3. Test the complete authentication flow
"""
import sys
import os
import requests
import json

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal
from app import models
from app.auth import get_password_hash
from sqlalchemy import text

BASE_URL = "http://127.0.0.1:8000"

def setup_database():
    """Setup database with properly activated users"""
    print("Setting up database...")
    
    db = SessionLocal()
    try:
        # Check existing users
        result = db.execute(text('SELECT username, email, activated, is_admin FROM account'))
        users = result.fetchall()
        print(f"Found {len(users)} users in database:")
        for user in users:
            print(f"  Username: {user[0]}, Email: {user[1]}, Activated: {user[2]}, Admin: {user[3]}")
        
        # Create or update admin user
        admin_user = db.query(models.Account).filter(models.Account.username == 'admin').first()
        if not admin_user:
            print("Creating admin user...")
            admin_account = models.Account(
                username='admin',
                email='admin@example.com',
                password=get_password_hash('Admin123@'),
                first_name='Admin',
                last_name='User',
                activated=True,
                is_admin=True,
                is_authenticated=True,
                created_at='2023-01-01 00:00:00'
            )
            db.add(admin_account)
            print("Admin user created and activated")
        else:
            print("Admin user exists, ensuring activated...")
            admin_user.activated = True
            admin_user.is_authenticated = True
            admin_user.is_admin = True
            print("Admin user activated")
        
        # Create or update test user
        test_user = db.query(models.Account).filter(models.Account.username == 'testuser').first()
        if not test_user:
            print("Creating test user...")
            test_account = models.Account(
                username='testuser',
                email='test@example.com',
                password=get_password_hash('Test123@'),
                first_name='Test',
                last_name='User',
                activated=True,
                is_admin=False,
                is_authenticated=True,
                created_at='2023-01-01 00:00:00'
            )
            db.add(test_account)
            print("Test user created and activated")
        else:
            print("Test user exists, ensuring activated...")
            test_user.activated = True
            test_user.is_authenticated = True
            print("Test user activated")
        
        db.commit()
        print("Database setup complete!")
        
    except Exception as e:
        print(f"Database setup error: {e}")
        db.rollback()
    finally:
        db.close()

def test_login(user_type="testuser"):
    """Test login for a specific user"""
    print(f"\n=== Testing {user_type} Login ===")
    
    if user_type == "admin":
        login_data = {"username": "admin", "password": "Admin123@"}
    else:
        login_data = {"username": "testuser", "password": "Test123@"}
    
    try:
        response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            access_token = result.get("access_token")
            refresh_token = result.get("refresh_token")
            
            print(f"SUCCESS: {user_type} login successful")
            print(f"Access token: {access_token[:50]}...")
            return access_token, refresh_token
        else:
            print(f"FAILED: {user_type} login failed")
            return None, None
            
    except Exception as e:
        print(f"ERROR: {user_type} login error: {e}")
        return None, None

def test_auth_me(access_token, user_type="user"):
    """Test /auth/me endpoint"""
    print(f"\n=== Testing /auth/me for {user_type} ===")
    
    headers = {"Authorization": f"Bearer {access_token}"}
    
    try:
        response = requests.get(f"{BASE_URL}/auth/me", headers=headers)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"SUCCESS: /auth/me working for {user_type}")
            print(f"User: {result.get('username')} ({result.get('email')})")
            print(f"Role: {result.get('role')}")
            print(f"Activated: {result.get('activated')}")
            return True
        else:
            print(f"FAILED: /auth/me failed for {user_type}")
            return False
            
    except Exception as e:
        print(f"ERROR: /auth/me error for {user_type}: {e}")
        return False

def main():
    print("Authentication Issue Fix Script")
    print("=" * 40)
    
    # Step 1: Setup database
    setup_database()
    
    # Step 2: Test with testuser
    print("\n" + "="*40)
    print("TESTING WITH TESTUSER")
    print("="*40)
    
    access_token, refresh_token = test_login("testuser")
    if access_token:
        success = test_auth_me(access_token, "testuser")
        if not success:
            print("ISSUE: testuser /auth/me failed - this needs investigation")
        else:
            print("SUCCESS: testuser authentication working correctly")
    
    # Step 3: Test with admin
    print("\n" + "="*40)
    print("TESTING WITH ADMIN")
    print("="*40)
    
    access_token, refresh_token = test_login("admin")
    if access_token:
        success = test_auth_me(access_token, "admin")
        if not success:
            print("ISSUE: admin /auth/me failed - this needs investigation")
        else:
            print("SUCCESS: admin authentication working correctly")
    
    # Summary
    print("\n" + "="*40)
    print("SUMMARY")
    print("="*40)
    print("If both testuser and admin can login and access /auth/me successfully,")
    print("then the issue was database users not being activated.")
    print("Frontend should now be able to authenticate properly.")

if __name__ == "__main__":
    main()