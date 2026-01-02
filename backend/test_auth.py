"""
Complete Authentication System Test
Run this after applying the REBUILD_AUTH.sql migration
"""

import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

def test_registration():
    """Test user registration"""
    print("\n" + "="*60)
    print("TEST 1: User Registration")
    print("="*60)
    
    user_data = {
        "email": "test.user@gmail.com",
        "password": "test123456",
        "full_name": "Test User",
        "role": "owner"
    }
    
    response = requests.post(f"{BASE_URL}/auth/register", json=user_data)
    
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    if response.status_code == 201:
        print("✅ Registration successful!")
        return response.json()
    else:
        print("❌ Registration failed!")
        return None


def test_login(email, password):
    """Test user login"""
    print("\n" + "="*60)
    print("TEST 2: User Login")
    print("="*60)
    
    login_data = {
        "email": email,
        "password": password
    }
    
    response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
    
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    if response.status_code == 200:
        print("✅ Login successful!")
        return response.json()
    else:
        print("❌ Login failed!")
        return None


def test_get_current_user(access_token):
    """Test getting current user info"""
    print("\n" + "="*60)
    print("TEST 3: Get Current User")
    print("="*60)
    
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    
    response = requests.get(f"{BASE_URL}/auth/me", headers=headers)
    
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    if response.status_code == 200:
        print("✅ Get current user successful!")
        return True
    else:
        print("❌ Get current user failed!")
        return False


def run_all_tests():
    """Run all authentication tests"""
    print("\n" + "="*60)
    print("🚀 AUTHENTICATION SYSTEM TEST SUITE")
    print("="*60)
    
    # Test 1: Registration
    user = test_registration()
    if not user:
        print("\n❌ Test suite failed at registration")
        return
    
    # Test 2: Login
    tokens = test_login("test.user@gmail.com", "test123456")
    if not tokens:
        print("\n❌ Test suite failed at login")
        return
    
    # Test 3: Get current user
    success = test_get_current_user(tokens["access_token"])
    if not success:
        print("\n❌ Test suite failed at get current user")
        return
    
    print("\n" + "="*60)
    print("🎉 ALL TESTS PASSED!")
    print("="*60)
    print("\n✅ Authentication system is working perfectly!")
    print(f"\n📝 Test user credentials:")
    print(f"   Email: test.user@gmail.com")
    print(f"   Password: test123456")
    print(f"\n🔑 Access Token: {tokens['access_token'][:50]}...")


if __name__ == "__main__":
    try:
        run_all_tests()
    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Cannot connect to backend server!")
        print("Make sure the backend is running at http://localhost:8000")
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

