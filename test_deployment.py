#!/usr/bin/env python3
"""
FIST Content Moderation System - Deployment Test Script
Usage: python test_deployment.py https://your-app.vercel.app
"""

import sys
import requests
import json
import time
from datetime import datetime

class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    NC = '\033[0m'  # No Color

def print_status(message, status="info"):
    color = Colors.BLUE
    if status == "success":
        color = Colors.GREEN
        icon = "✅"
    elif status == "error":
        color = Colors.RED
        icon = "❌"
    elif status == "warning":
        color = Colors.YELLOW
        icon = "⚠️"
    else:
        color = Colors.YELLOW
        icon = "📋"
    
    print(f"{color}{icon} {message}{Colors.NC}")

def test_api_docs(base_url):
    """Test API documentation access"""
    print_status("Test 1: API Documentation Access")
    try:
        response = requests.get(f"{base_url}/docs", timeout=10)
        if response.status_code == 200:
            print_status("API docs accessible", "success")
            return True
        else:
            print_status(f"API docs returned status {response.status_code}", "error")
            return False
    except Exception as e:
        print_status(f"API docs access failed: {e}", "error")
        return False

def test_user_registration(base_url, username, password):
    """Test user registration"""
    print_status("Test 2: User Registration")
    try:
        data = {"username": username, "password": password}
        response = requests.post(f"{base_url}/api/user/register", json=data, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            if "user_id" in result:
                print_status("User registration successful", "success")
                return result["user_id"]
        
        print_status(f"User registration failed: {response.text}", "error")
        return None
    except Exception as e:
        print_status(f"User registration error: {e}", "error")
        return None

def test_user_login(base_url, username, password):
    """Test user login"""
    print_status("Test 3: User Login")
    try:
        data = {"username": username, "password": password}
        response = requests.post(f"{base_url}/api/user/login", json=data, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            if "access_token" in result:
                print_status("User login successful", "success")
                return result["access_token"]
        
        print_status(f"User login failed: {response.text}", "error")
        return None
    except Exception as e:
        print_status(f"User login error: {e}", "error")
        return None

def test_create_api_token(base_url, access_token):
    """Test API token creation"""
    print_status("Test 4: Create API Token")
    try:
        headers = {"Authorization": f"Bearer {access_token}"}
        data = {"name": "Test Token"}
        response = requests.post(f"{base_url}/api/user/tokens", json=data, headers=headers, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            if "token" in result and result["token"].startswith("fist_"):
                print_status("API token creation successful", "success")
                return result["token"]
        
        print_status(f"API token creation failed: {response.text}", "error")
        return None
    except Exception as e:
        print_status(f"API token creation error: {e}", "error")
        return None

def test_content_moderation(base_url, api_token):
    """Test content moderation"""
    print_status("Test 5: Content Moderation")
    try:
        headers = {"Authorization": f"Bearer {api_token}"}
        data = {"content": "This is a test content for AI moderation functionality."}
        response = requests.post(f"{base_url}/api/moderate", json=data, headers=headers, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            if "moderation_id" in result:
                print_status("Content moderation successful", "success")
                print_status(f"  Decision: {result.get('final_decision', 'N/A')}")
                print_status(f"  Probability: {result.get('ai_result', {}).get('inappropriate_probability', 'N/A')}%")
                return result["moderation_id"]
        
        print_status(f"Content moderation failed: {response.text}", "error")
        return None
    except Exception as e:
        print_status(f"Content moderation error: {e}", "error")
        return None

def test_get_moderation_result(base_url, api_token, moderation_id):
    """Test getting moderation result"""
    print_status("Test 6: Get Moderation Result")
    try:
        headers = {"Authorization": f"Bearer {api_token}"}
        response = requests.get(f"{base_url}/api/results/{moderation_id}", headers=headers, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            if "final_decision" in result:
                print_status("Moderation result retrieval successful", "success")
                return True
        
        print_status(f"Moderation result retrieval failed: {response.text}", "error")
        return False
    except Exception as e:
        print_status(f"Moderation result retrieval error: {e}", "error")
        return False

def test_admin_login(base_url, admin_password="admin123"):
    """Test admin login"""
    print_status("Test 7: Admin Login")
    try:
        data = {"username": "admin", "password": admin_password}
        response = requests.post(f"{base_url}/api/admin/login", json=data, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            if "access_token" in result:
                print_status("Admin login successful", "success")
                return result["access_token"]
        
        print_status(f"Admin login failed (check password): {response.text}", "warning")
        return None
    except Exception as e:
        print_status(f"Admin login error: {e}", "warning")
        return None

def test_admin_functionality(base_url, admin_token):
    """Test admin functionality"""
    print_status("Test 7.1: Admin Get Users")
    try:
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{base_url}/api/admin/users", headers=headers, timeout=10)
        
        if response.status_code == 200:
            users = response.json()
            print_status(f"Admin user list retrieval successful ({len(users)} users)", "success")
            return True
        
        print_status(f"Admin user list retrieval failed: {response.text}", "warning")
        return False
    except Exception as e:
        print_status(f"Admin functionality error: {e}", "warning")
        return False

def test_error_handling(base_url):
    """Test error handling"""
    print_status("Test 8: Error Handling")
    try:
        headers = {"Authorization": "Bearer invalid_token"}
        data = {"content": "test"}
        response = requests.post(f"{base_url}/api/moderate", json=data, headers=headers, timeout=10)
        
        if response.status_code == 401:
            print_status("Error handling working correctly", "success")
            return True
        
        print_status(f"Error handling unexpected response: {response.status_code}", "warning")
        return False
    except Exception as e:
        print_status(f"Error handling test error: {e}", "warning")
        return False

def main():
    if len(sys.argv) != 2:
        print_status("Usage: python test_deployment.py https://your-app.vercel.app", "error")
        sys.exit(1)
    
    base_url = sys.argv[1].rstrip('/')
    timestamp = int(time.time())
    test_username = f"testuser_{timestamp}"
    test_password = "TestPass123!"
    
    print(f"{Colors.BLUE}🚀 Testing FIST deployment at: {base_url}{Colors.NC}")
    print(f"{Colors.BLUE}📅 Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Colors.NC}")
    print()
    
    # Run tests
    tests_passed = 0
    total_tests = 8
    
    # Test 1: API Documentation
    if test_api_docs(base_url):
        tests_passed += 1
    
    # Test 2: User Registration
    user_id = test_user_registration(base_url, test_username, test_password)
    if user_id:
        tests_passed += 1
    else:
        print_status("Stopping tests due to registration failure", "error")
        sys.exit(1)
    
    # Test 3: User Login
    access_token = test_user_login(base_url, test_username, test_password)
    if access_token:
        tests_passed += 1
    else:
        print_status("Stopping tests due to login failure", "error")
        sys.exit(1)
    
    # Test 4: Create API Token
    api_token = test_create_api_token(base_url, access_token)
    if api_token:
        tests_passed += 1
    else:
        print_status("Stopping tests due to token creation failure", "error")
        sys.exit(1)
    
    # Test 5: Content Moderation
    moderation_id = test_content_moderation(base_url, api_token)
    if moderation_id:
        tests_passed += 1
    
    # Test 6: Get Moderation Result
    if moderation_id and test_get_moderation_result(base_url, api_token, moderation_id):
        tests_passed += 1
    
    # Test 7: Admin Login
    admin_token = test_admin_login(base_url)
    if admin_token:
        tests_passed += 1
        # Test 7.1: Admin functionality
        test_admin_functionality(base_url, admin_token)
    
    # Test 8: Error Handling
    if test_error_handling(base_url):
        tests_passed += 1
    
    print()
    if tests_passed >= 6:  # Core functionality working
        print_status(f"🎉 Deployment test completed! ({tests_passed}/{total_tests} tests passed)", "success")
        print_status("✅ Core functionality is working correctly", "success")
    else:
        print_status(f"❌ Deployment test failed! ({tests_passed}/{total_tests} tests passed)", "error")
        sys.exit(1)
    
    print()
    print_status("📝 Test Summary:", "info")
    print(f"  - User ID: {user_id}")
    print(f"  - API Token: {api_token[:20]}..." if api_token else "  - API Token: Failed")
    print(f"  - Moderation ID: {moderation_id}" if moderation_id else "  - Moderation ID: Failed")
    
    print()
    print_status("🔗 Useful URLs:", "info")
    print(f"  - API Documentation: {base_url}/docs")
    print(f"  - ReDoc: {base_url}/redoc")

if __name__ == "__main__":
    main()
