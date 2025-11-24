"""
Test script for Mock Bank API endpoints
Demonstrates deposit and payment functionality with QR codes
"""
import requests
import json
from datetime import datetime

# Base URL for the API
BASE_URL = "http://localhost:8000"

class BankAPITester:
    def __init__(self):
        self.access_token = None
        self.headers = {}
    
    def login(self, username="testuser", password="password"):
        """Login to get access token"""
        login_data = {
            "username": username,
            "password": password
        }
        
        response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
        
        if response.status_code == 200:
            result = response.json()
            self.access_token = result.get("access_token")
            self.headers = {"Authorization": f"Bearer {self.access_token}"}
            print("✓ Login successful")
            return True
        else:
            print(f"✗ Login failed: {response.text}")
            return False
    
    def test_bank_health(self):
        """Test bank API health check"""
        print("\n=== Testing Bank API Health ===")
        response = requests.get(f"{BASE_URL}/bank/health")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✓ Bank API is healthy: {result['data']['bank_name']}")
            print(f"  Status: {result['data']['status']}")
        else:
            print(f"✗ Bank API health check failed: {response.text}")
    
    def test_supported_banks(self):
        """Test getting supported banks"""
        print("\n=== Testing Supported Banks ===")
        response = requests.get(f"{BASE_URL}/bank/banks")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✓ Found {len(result['data'])} supported banks:")
            for bank in result['data']:
                print(f"  - {bank['bank_name']} ({bank['bank_code']})")
        else:
            print(f"✗ Failed to get supported banks: {response.text}")
    
    def test_create_deposit(self, auction_id=1):
        """Test creating deposit for auction participation"""
        print(f"\n=== Testing Deposit Creation for Auction {auction_id} ===")
        
        # Create deposit
        response = requests.get(f"{BASE_URL}/bank/deposit/create", 
                              headers=self.headers,
                              params={"auction_id": auction_id})
        
        if response.status_code == 200:
            result = response.json()
            print(f"✓ Deposit created successfully")
            print(f"  Transaction ID: {result['data']['transaction_id']}")
            print(f"  Amount: {result['data']['amount']:,} VND")
            print(f"  Status: {result['data']['status']}")
            print(f"  QR Code: {result['data']['qr_code']}")
            return result['data']['transaction_id']
        else:
            print(f"✗ Deposit creation failed: {response.text}")
            return None
    
    def test_deposit_status(self, transaction_id):
        """Test checking deposit status"""
        print(f"\n=== Testing Deposit Status for {transaction_id} ===")
        
        response = requests.get(f"{BASE_URL}/bank/deposit/status/{transaction_id}",
                              headers=self.headers)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✓ Deposit status: {result['data']['status']}")
            print(f"  Bank response: {result['data']['bank_response']['message']}")
        else:
            print(f"✗ Deposit status check failed: {response.text}")
    
    def test_create_payment(self, auction_id=1, payment_id=1):
        """Test creating payment for won auction"""
        print(f"\n=== Testing Payment Creation for Auction {auction_id} ===")
        
        payment_data = {
            "auction_id": auction_id,
            "payment_id": payment_id
        }
        
        response = requests.post(f"{BASE_URL}/bank/payment/create",
                               headers=self.headers,
                               json=payment_data)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✓ Payment created successfully")
            print(f"  Transaction ID: {result['data']['transaction_id']}")
            print(f"  Amount: {result['data']['amount']:,} VND")
            print(f"  Status: {result['data']['status']}")
            print(f"  QR Code: {result['data']['qr_code']}")
            print(f"  Instructions: {result['data']['payment_instructions']}")
            return result['data']['transaction_id']
        else:
            print(f"✗ Payment creation failed: {response.text}")
            return None
    
    def test_payment_confirmation(self, transaction_id, payment_id):
        """Test payment confirmation"""
        print(f"\n=== Testing Payment Confirmation for {transaction_id} ===")
        
        confirmation_data = {
            "transaction_id": transaction_id,
            "payment_id": payment_id
        }
        
        response = requests.post(f"{BASE_URL}/bank/payment/confirm",
                               headers=self.headers,
                               json=confirmation_data)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✓ Payment confirmed successfully")
            print(f"  Status: {result['data']['status']}")
            print(f"  Bank response: {result['data']['bank_response']['message']}")
            print(f"  Confirmed at: {result['data']['confirmed_at']}")
        else:
            print(f"✗ Payment confirmation failed: {response.text}")
    
    def test_payment_status(self, transaction_id):
        """Test checking payment status"""
        print(f"\n=== Testing Payment Status for {transaction_id} ===")
        
        response = requests.get(f"{BASE_URL}/bank/payment/status/{transaction_id}",
                              headers=self.headers)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✓ Payment status: {result['data']['status']}")
            print(f"  Bank response: {result['data']['bank_response']['message']}")
        else:
            print(f"✗ Payment status check failed: {response.text}")
    
    def run_full_test(self):
        """Run complete test flow"""
        print("🚀 Starting Mock Bank API Test Suite")
        print("=" * 50)
        
        # 1. Bank health check
        self.test_bank_health()
        
        # 2. Get supported banks
        self.test_supported_banks()
        
        # 3. Login (assuming test user exists)
        if not self.login():
            print("⚠️  Login failed. Make sure test user exists.")
            return
        
        # 4. Test deposit flow
        print("\n💰 Testing Deposit Flow (Đặt cọc)")
        deposit_tx_id = self.test_create_deposit(auction_id=1)
        if deposit_tx_id:
            self.test_deposit_status(deposit_tx_id)
        
        # 5. Test payment flow
        print("\n💳 Testing Payment Flow (Thanh toán)")
        payment_tx_id = self.test_create_payment(auction_id=1, payment_id=1)
        if payment_tx_id:
            self.test_payment_status(payment_tx_id)
            self.test_payment_confirmation(payment_tx_id, payment_id=1)
        
        print("\n✅ Test suite completed!")


def create_test_user():
    """Create a test user if it doesn't exist"""
    print("Creating test user...")
    
    user_data = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "password",
        "first_name": "Test",
        "last_name": "User"
    }
    
    response = requests.post(f"{BASE_URL}/accounts/create", json=user_data)
    
    if response.status_code == 200:
        print("✓ Test user created successfully")
        return True
    elif "already exists" in response.text.lower():
        print("✓ Test user already exists")
        return True
    else:
        print(f"✗ Failed to create test user: {response.text}")
        return False


def main():
    """Main test function"""
    # Create test user first
    create_test_user()
    
    # Run bank API tests
    tester = BankAPITester()
    tester.run_full_test()
    
    print("\n" + "=" * 50)
    print("📚 API Documentation:")
    print(f"  • FastAPI Docs: {BASE_URL}/docs")
    print(f"  • Bank API: {BASE_URL}/bank/*")
    print(f"  • Deposit endpoint: GET /bank/deposit/create?auction_id=1")
    print(f"  • Payment endpoint: POST /bank/payment/create")
    print(f"  • Payment confirmation: POST /bank/payment/confirm")


if __name__ == "__main__":
    main()