#!/usr/bin/env python3
"""
Test script for FIST API with user authentication
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_health():
    """Test health endpoint"""
    print("Testing health endpoint...")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Health check: {response.status_code} - {response.json()}")
    return response.status_code == 200

def test_user_registration():
    """Test user registration"""
    print("\nTesting user registration...")

    # First, try without invitation code (should work if REQUIRE_INVITATION_CODE is False)
    import random
    username = f"testuser{random.randint(1000, 9999)}"
    user_data = {
        "username": username,
        "password": "testpass123"
    }

    response = requests.post(f"{BASE_URL}/user/register", json=user_data)
    print(f"User registration: {response.status_code}")
    if response.status_code == 200:
        user_info = response.json()
        print(f"User created: {user_info}")
        return user_info, username
    else:
        print(f"Registration failed: {response.text}")
        return None, None

def test_user_login(username, password):
    """Test user login"""
    print(f"\nTesting user login for {username}...")

    login_data = {
        "username": username,
        "password": password
    }

    response = requests.post(f"{BASE_URL}/user/login", json=login_data)
    print(f"User login: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"Login successful: {result['user']['username']}")
        return result['access_token']
    else:
        print(f"Login failed: {response.text}")
        return None

def test_token_creation(access_token):
    """Test API token creation"""
    print("\nTesting API token creation...")

    headers = {"Authorization": f"Bearer {access_token}"}
    token_data = {"name": "Test Token"}

    response = requests.post(f"{BASE_URL}/user/tokens", json=token_data, headers=headers)
    print(f"Token creation: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"Token created: {result['name']}")
        return result['token']
    else:
        print(f"Token creation failed: {response.text}")
        return None

def test_moderation_with_token(api_token):
    """Test content moderation with API token"""
    print("\nTesting content moderation with API token...")

    headers = {"Authorization": f"Bearer {api_token}"}
    moderation_data = {
        "content": "This is a test content for moderation. It should be processed by the AI system."
    }

    response = requests.post(f"{BASE_URL}/moderate", json=moderation_data, headers=headers)
    print(f"Moderation: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"Moderation result: {result['result']['final_decision']}")
        return result
    else:
        print(f"Moderation failed: {response.text}")
        return None

def test_usage_stats(access_token):
    """Test usage statistics"""
    print("\nTesting usage statistics...")

    headers = {"Authorization": f"Bearer {access_token}"}

    response = requests.get(f"{BASE_URL}/user/usage", headers=headers)
    print(f"Usage stats: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"Usage stats: {result}")
        return result
    else:
        print(f"Usage stats failed: {response.text}")
        return None

def main():
    """Run all tests"""
    print("=== FIST API Test Suite ===")

    # Test health
    if not test_health():
        print("Health check failed, stopping tests")
        return

    # Test user registration
    result = test_user_registration()
    if not result[0]:
        print("User registration failed, stopping tests")
        return

    user, username = result

    # Test user login
    access_token = test_user_login(username, "testpass123")
    if not access_token:
        print("User login failed, stopping tests")
        return

    # Test token creation
    api_token = test_token_creation(access_token)
    if not api_token:
        print("Token creation failed, stopping tests")
        return

    # Test moderation with token
    moderation_result = test_moderation_with_token(api_token)
    if not moderation_result:
        print("Moderation failed, stopping tests")
        return

    # Test usage stats
    usage_stats = test_usage_stats(access_token)

    print("\n=== All tests completed ===")

if __name__ == "__main__":
    main()
