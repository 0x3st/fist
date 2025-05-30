#!/usr/bin/env python3
"""
Test script for invitation code functionality
"""
import requests
import random

BASE_URL = "http://localhost:8000"

def test_admin_login():
    """Test admin login"""
    print("Testing admin login...")

    login_data = {
        "username": "admin",
        "password": "admin123"
    }

    response = requests.post(f"{BASE_URL}/admin/login", data=login_data, allow_redirects=False)
    print(f"Admin login: {response.status_code}")

    if response.status_code == 302:  # Redirect after successful login
        # Extract session cookie
        cookies = response.cookies
        print("Admin login successful")
        return cookies
    else:
        print(f"Admin login failed: {response.status_code} - {response.text[:200]}")
        return None

def test_create_invitation_code(cookies):
    """Test creating invitation code through admin interface"""
    print("\nTesting invitation code creation...")

    invitation_data = {
        "max_uses": "5",
        "expires_days": "30"
    }

    response = requests.post(
        f"{BASE_URL}/admin/invitation-codes/create",
        data=invitation_data,
        cookies=cookies,
        allow_redirects=False
    )

    print(f"Invitation code creation: {response.status_code}")
    if response.status_code == 302:
        print("Invitation code created successfully")
        return True
    else:
        print(f"Invitation code creation failed: {response.text}")
        return False

def test_get_users_page(cookies):
    """Test getting users page to see invitation codes"""
    print("\nTesting users page...")

    response = requests.get(f"{BASE_URL}/admin/users", cookies=cookies)
    print(f"Users page: {response.status_code}")

    if response.status_code == 200:
        # Look for invitation codes in the HTML
        html = response.text
        if "invitation_codes" in html or "Invitation Code" in html:
            print("Users page loaded successfully with invitation codes")
            return True
        else:
            print("Users page loaded but no invitation codes found")
            return False
    else:
        print(f"Users page failed: {response.text}")
        return False

def test_registration_with_invitation_required():
    """Test user registration when invitation is required"""
    print("\nTesting registration with invitation requirement...")

    # Try to register without invitation code (should fail)
    username = f"testuser{random.randint(1000, 9999)}"
    user_data = {
        "username": username,
        "password": "testpass123"
    }

    response = requests.post(f"{BASE_URL}/user/register", json=user_data)
    print(f"Registration without invitation: {response.status_code}")

    if response.status_code == 400:
        error = response.json()
        if "invitation code" in error.get("detail", "").lower():
            print("✓ Registration correctly rejected without invitation code")
            return True
        else:
            print(f"✗ Unexpected error: {error}")
            return False
    else:
        print("✗ Registration should have failed without invitation code")
        return False

def main():
    """Run invitation code tests"""
    print("=== FIST Invitation Code Test Suite ===")

    # Test admin login
    cookies = test_admin_login()
    if not cookies:
        print("Admin login failed, stopping tests")
        return

    # Test creating invitation code
    if not test_create_invitation_code(cookies):
        print("Invitation code creation failed, stopping tests")
        return

    # Test users page
    if not test_get_users_page(cookies):
        print("Users page test failed")

    # Test registration with invitation requirement
    if not test_registration_with_invitation_required():
        print("Registration test failed")

    print("\n=== Invitation code tests completed ===")
    print("\nTo test with actual invitation codes:")
    print("1. Set REQUIRE_INVITATION_CODE=True")
    print("2. Restart the server")
    print("3. Create invitation codes through admin interface")
    print("4. Use the codes for user registration")

if __name__ == "__main__":
    main()
