"""
LibreWork v2.0 - Comprehensive Feature Testing Script
Tests all new features with the backend API
"""

import requests
import json
import sys
from datetime import datetime, timedelta

# Set UTF-8 encoding for Windows
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Configuration
API_BASE_URL = "http://127.0.0.1:8000/api/v1"
TEST_EMAIL = "test@librework.com"
TEST_PASSWORD = "TestPassword123!"

def print_test(name):
    print(f"\n{'='*60}")
    print(f"Testing: {name}")
    print(f"{'='*60}")

def print_success(message):
    print(f"[OK] {message}")

def print_error(message):
    print(f"[FAIL] {message}")

def print_info(message):
    print(f"[INFO] {message}")

# Global variable to store auth token
auth_token = None
user_id = None
establishment_id = None
space_id = None
reservation_id = None

def test_health_check():
    """Test basic health endpoint"""
    print_test("Health Check")
    try:
        response = requests.get(f"{API_BASE_URL.replace('/api/v1', '')}/health", timeout=5)
        if response.status_code == 200:
            print_success("Backend is healthy")
            return True
        else:
            print_error(f"Health check failed: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print_error(f"Could not connect to backend: {e}")
        print_info("Make sure backend is running on http://localhost:8000")
        return False

def test_authentication():
    """Test authentication and get token"""
    global auth_token, user_id
    print_test("Authentication System")
    
    # Try to register
    print_info("Attempting to register new user...")
    register_data = {
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD,
        "full_name": "Test User",
        "role": "customer"
    }
    
    try:
        response = requests.post(f"{API_BASE_URL}/auth/register", json=register_data)
        if response.status_code == 201:
            data = response.json()
            auth_token = data.get("access_token")
            print_success(f"Registration successful")
        else:
            # User might already exist, try login
            print_info("User exists, trying login...")
            login_data = {
                "email": TEST_EMAIL,
                "password": TEST_PASSWORD
            }
            response = requests.post(f"{API_BASE_URL}/auth/login", json=login_data)
            if response.status_code == 200:
                data = response.json()
                auth_token = data.get("access_token")
                print_success("Login successful")
            else:
                print_error(f"Login failed: {response.text}")
                return False
        
        # Get user info
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{API_BASE_URL}/auth/me", headers=headers)
        if response.status_code == 200:
            user_data = response.json()
            user_id = user_data.get("id")
            print_success(f"Got user ID: {user_id}")
            return True
        else:
            print_error("Could not get user info")
            return False
            
    except Exception as e:
        print_error(f"Authentication error: {e}")
        return False

def test_real_time_availability():
    """Test real-time availability display"""
    global space_id
    print_test("Real-Time Availability Display")
    
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    # First, get a space ID
    try:
        response = requests.get(f"{API_BASE_URL}/establishments", headers=headers)
        if response.status_code == 200 and response.json():
            establishments = response.json()
            if establishments:
                establishment_id = establishments[0]["id"]
                # Get spaces for this establishment
                response = requests.get(f"{API_BASE_URL}/spaces?establishment_id={establishment_id}", headers=headers)
                if response.status_code == 200 and response.json():
                    spaces = response.json()
                    if spaces:
                        space_id = spaces[0]["id"]
                        print_success(f"Found space: {space_id}")
                        
                        # Test availability endpoint
                        response = requests.get(
                            f"{API_BASE_URL}/spaces/{space_id}/availability/now",
                            headers=headers
                        )
                        if response.status_code == 200:
                            data = response.json()
                            print_success(f"Availability check successful")
                            print_info(f"Space is {'available' if data['is_available'] else 'occupied'}")
                            return True
                        else:
                            print_error(f"Availability check failed: {response.status_code}")
                            return False
        
        print_error("No spaces found to test")
        return False
    except Exception as e:
        print_error(f"Availability test error: {e}")
        return False

def test_favorites():
    """Test favorite establishments"""
    print_test("Favorite Establishments")
    
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    try:
        # Get establishments
        response = requests.get(f"{API_BASE_URL}/establishments", headers=headers)
        if response.status_code == 200 and response.json():
            establishments = response.json()
            if establishments:
                est_id = establishments[0]["id"]
                
                # Add to favorites
                response = requests.post(
                    f"{API_BASE_URL}/favorites/{est_id}",
                    headers=headers
                )
                if response.status_code in [200, 400]:  # 400 if already favorited
                    print_success("Added to favorites (or already exists)")
                    
                    # Get favorites
                    response = requests.get(f"{API_BASE_URL}/favorites", headers=headers)
                    if response.status_code == 200:
                        favorites = response.json()
                        print_success(f"Retrieved {len(favorites)} favorites")
                        
                        # Check if favorited
                        response = requests.get(
                            f"{API_BASE_URL}/favorites/check/{est_id}",
                            headers=headers
                        )
                        if response.status_code == 200:
                            data = response.json()
                            print_success(f"Favorite status check: {data['is_favorite']}")
                            return True
        
        print_error("Could not test favorites")
        return False
    except Exception as e:
        print_error(f"Favorites test error: {e}")
        return False

def test_advanced_search():
    """Test advanced search"""
    print_test("Advanced Search with Filters")
    
    try:
        # Test basic search
        response = requests.get(
            f"{API_BASE_URL}/establishments/search/advanced?q=cafe&min_rating=0"
        )
        if response.status_code == 200:
            results = response.json()
            print_success(f"Basic search returned {len(results)} results")
            
            # Test with filters
            response = requests.get(
                f"{API_BASE_URL}/establishments/search/advanced?category=cafe&min_rating=4.0"
            )
            if response.status_code == 200:
                results = response.json()
                print_success(f"Filtered search returned {len(results)} results")
                return True
        
        print_error("Advanced search failed")
        return False
    except Exception as e:
        print_error(f"Advanced search error: {e}")
        return False

def test_activity_tracking():
    """Test activity tracking and heatmap"""
    print_test("Activity Tracking & Heatmap")
    
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    try:
        # Test heatmap
        response = requests.get(f"{API_BASE_URL}/activity/heatmap", headers=headers)
        if response.status_code == 200:
            data = response.json()
            print_success(f"Heatmap retrieved: {data['total_hours']} total hours")
            
            # Test stats
            response = requests.get(f"{API_BASE_URL}/activity/stats", headers=headers)
            if response.status_code == 200:
                stats = response.json()
                print_success(f"Stats retrieved: {stats['total_reservations']} reservations")
                
                # Test streaks
                response = requests.get(f"{API_BASE_URL}/activity/streaks", headers=headers)
                if response.status_code == 200:
                    streaks = response.json()
                    print_success(f"Streaks: Current {streaks['current_streak']} days")
                    return True
        
        print_error("Activity tracking test failed")
        return False
    except Exception as e:
        print_error(f"Activity tracking error: {e}")
        return False

def test_loyalty_program():
    """Test loyalty and rewards"""
    print_test("Loyalty & Rewards Program")
    
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    try:
        # Get loyalty status
        response = requests.get(f"{API_BASE_URL}/loyalty/status", headers=headers)
        if response.status_code == 200:
            data = response.json()
            print_success(f"Loyalty status: {data['tier_name']} tier with {data['points']} points")
            
            # Get tiers
            response = requests.get(f"{API_BASE_URL}/loyalty/tiers", headers=headers)
            if response.status_code == 200:
                tiers = response.json()
                print_success(f"Retrieved {len(tiers)} loyalty tiers")
                
                # Get transactions
                response = requests.get(f"{API_BASE_URL}/loyalty/transactions", headers=headers)
                if response.status_code == 200:
                    transactions = response.json()
                    print_success(f"Retrieved {len(transactions)} loyalty transactions")
                    return True
        
        print_error("Loyalty program test failed")
        return False
    except Exception as e:
        print_error(f"Loyalty program error: {e}")
        return False

def test_push_notifications():
    """Test push notifications API"""
    print_test("Push Notifications")
    
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    try:
        # Get subscriptions
        response = requests.get(f"{API_BASE_URL}/notifications/subscriptions", headers=headers)
        if response.status_code == 200:
            subs = response.json()
            print_success(f"Retrieved {len(subs)} push subscriptions")
            
            # Get preferences
            response = requests.get(f"{API_BASE_URL}/notifications/preferences", headers=headers)
            if response.status_code == 200:
                prefs = response.json()
                print_success(f"Got notification preferences")
                
                # Get history
                response = requests.get(f"{API_BASE_URL}/notifications/history", headers=headers)
                if response.status_code == 200:
                    history = response.json()
                    print_success(f"Retrieved {len(history)} notifications from history")
                    return True
        
        print_error("Push notifications test failed")
        return False
    except Exception as e:
        print_error(f"Push notifications error: {e}")
        return False

def test_calendar_integration():
    """Test calendar integration"""
    print_test("Calendar Integration")
    
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    try:
        # Test feed URL
        response = requests.get(f"{API_BASE_URL}/calendar/feed", headers=headers)
        if response.status_code == 200:
            data = response.json()
            print_success(f"Got calendar feed URL")
            
            # Test iCal export (might be empty if no reservations)
            response = requests.get(f"{API_BASE_URL}/calendar/export/ical", headers=headers)
            if response.status_code == 200:
                print_success(f"iCal export works ({len(response.content)} bytes)")
                return True
        
        print_error("Calendar integration test failed")
        return False
    except Exception as e:
        print_error(f"Calendar integration error: {e}")
        return False

def test_group_reservations():
    """Test group reservations"""
    print_test("Group Reservations")
    
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    try:
        # Get user's groups
        response = requests.get(f"{API_BASE_URL}/groups/my-groups", headers=headers)
        if response.status_code == 200:
            groups = response.json()
            print_success(f"Retrieved {len(groups)} groups")
            return True
        
        print_error("Group reservations test failed")
        return False
    except Exception as e:
        print_error(f"Group reservations error: {e}")
        return False

def main():
    """Run all tests"""
    print(f"\n{'='*70}")
    print(f"LibreWork v2.0 - Comprehensive Feature Testing")
    print(f"{'='*70}\n")
    
    results = {}
    
    # Run tests
    results["Health Check"] = test_health_check()
    
    if results["Health Check"]:
        results["Authentication"] = test_authentication()
        
        if results["Authentication"]:
            results["Real-Time Availability"] = test_real_time_availability()
            results["Favorites"] = test_favorites()
            results["Advanced Search"] = test_advanced_search()
            results["Activity Tracking"] = test_activity_tracking()
            results["Loyalty Program"] = test_loyalty_program()
            results["Push Notifications"] = test_push_notifications()
            results["Calendar Integration"] = test_calendar_integration()
            results["Group Reservations"] = test_group_reservations()
    
    # Print summary
    print(f"\n{'='*70}")
    print(f"Test Summary")
    print(f"{'='*70}\n")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = "PASSED" if result else "FAILED"
        print(f"{test_name:.<50} {status}")
    
    print(f"\n{'='*70}")
    percentage = (passed / total * 100) if total > 0 else 0
    print(f"Total: {passed}/{total} tests passed ({percentage:.1f}%)")
    print(f"{'='*70}\n")
    
    return passed == total

if __name__ == "__main__":
    try:
        success = main()
        exit(0 if success else 1)
    except KeyboardInterrupt:
        print(f"\nTesting interrupted by user")
        exit(1)
    except Exception as e:
        print(f"\nFatal error: {e}")
        exit(1)

