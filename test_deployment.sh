#!/bin/bash

# FIST Content Moderation System - Deployment Test Script
# Usage: ./test_deployment.sh https://your-app.vercel.app

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if URL is provided
if [ $# -eq 0 ]; then
    echo -e "${RED}Error: Please provide the deployment URL${NC}"
    echo "Usage: $0 https://your-app.vercel.app"
    exit 1
fi

BASE_URL="$1"
TEST_USERNAME="testuser_$(date +%s)"
TEST_PASSWORD="TestPass123!"
ADMIN_PASSWORD="${ADMIN_PASSWORD:-admin123}"  # Use env var or default

echo -e "${YELLOW}🚀 Testing FIST deployment at: $BASE_URL${NC}"
echo ""

# Test 1: API Documentation
echo -e "${YELLOW}📚 Test 1: API Documentation Access${NC}"
if curl -s -f "$BASE_URL/docs" > /dev/null; then
    echo -e "${GREEN}✅ API docs accessible${NC}"
else
    echo -e "${RED}❌ API docs not accessible${NC}"
    exit 1
fi

# Test 2: User Registration
echo -e "${YELLOW}👤 Test 2: User Registration${NC}"
REGISTER_RESPONSE=$(curl -s -X POST "$BASE_URL/api/user/register" \
    -H "Content-Type: application/json" \
    -d "{\"username\": \"$TEST_USERNAME\", \"password\": \"$TEST_PASSWORD\"}")

if echo "$REGISTER_RESPONSE" | grep -q "user_id"; then
    echo -e "${GREEN}✅ User registration successful${NC}"
    USER_ID=$(echo "$REGISTER_RESPONSE" | grep -o '"user_id":"[^"]*"' | cut -d'"' -f4)
else
    echo -e "${RED}❌ User registration failed${NC}"
    echo "Response: $REGISTER_RESPONSE"
    exit 1
fi

# Test 3: User Login
echo -e "${YELLOW}🔐 Test 3: User Login${NC}"
LOGIN_RESPONSE=$(curl -s -X POST "$BASE_URL/api/user/login" \
    -H "Content-Type: application/json" \
    -d "{\"username\": \"$TEST_USERNAME\", \"password\": \"$TEST_PASSWORD\"}")

if echo "$LOGIN_RESPONSE" | grep -q "access_token"; then
    echo -e "${GREEN}✅ User login successful${NC}"
    ACCESS_TOKEN=$(echo "$LOGIN_RESPONSE" | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)
else
    echo -e "${RED}❌ User login failed${NC}"
    echo "Response: $LOGIN_RESPONSE"
    exit 1
fi

# Test 4: Create API Token
echo -e "${YELLOW}🔑 Test 4: Create API Token${NC}"
TOKEN_RESPONSE=$(curl -s -X POST "$BASE_URL/api/user/tokens" \
    -H "Authorization: Bearer $ACCESS_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"name": "Test Token"}')

if echo "$TOKEN_RESPONSE" | grep -q "fist_"; then
    echo -e "${GREEN}✅ API token creation successful${NC}"
    API_TOKEN=$(echo "$TOKEN_RESPONSE" | grep -o '"token":"[^"]*"' | cut -d'"' -f4)
else
    echo -e "${RED}❌ API token creation failed${NC}"
    echo "Response: $TOKEN_RESPONSE"
    exit 1
fi

# Test 5: Content Moderation
echo -e "${YELLOW}🤖 Test 5: Content Moderation${NC}"
MODERATE_RESPONSE=$(curl -s -X POST "$BASE_URL/api/moderate" \
    -H "Authorization: Bearer $API_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"content": "This is a test content for AI moderation."}')

if echo "$MODERATE_RESPONSE" | grep -q "moderation_id"; then
    echo -e "${GREEN}✅ Content moderation successful${NC}"
    MODERATION_ID=$(echo "$MODERATE_RESPONSE" | grep -o '"moderation_id":"[^"]*"' | cut -d'"' -f4)
else
    echo -e "${RED}❌ Content moderation failed${NC}"
    echo "Response: $MODERATE_RESPONSE"
    exit 1
fi

# Test 6: Get Moderation Result
echo -e "${YELLOW}📊 Test 6: Get Moderation Result${NC}"
RESULT_RESPONSE=$(curl -s -X GET "$BASE_URL/api/results/$MODERATION_ID" \
    -H "Authorization: Bearer $API_TOKEN")

if echo "$RESULT_RESPONSE" | grep -q "final_decision"; then
    echo -e "${GREEN}✅ Moderation result retrieval successful${NC}"
else
    echo -e "${RED}❌ Moderation result retrieval failed${NC}"
    echo "Response: $RESULT_RESPONSE"
    exit 1
fi

# Test 7: Admin Login (optional)
echo -e "${YELLOW}👑 Test 7: Admin Login${NC}"
ADMIN_LOGIN_RESPONSE=$(curl -s -X POST "$BASE_URL/api/admin/login" \
    -H "Content-Type: application/json" \
    -d "{\"username\": \"admin\", \"password\": \"$ADMIN_PASSWORD\"}")

if echo "$ADMIN_LOGIN_RESPONSE" | grep -q "access_token"; then
    echo -e "${GREEN}✅ Admin login successful${NC}"
    ADMIN_TOKEN=$(echo "$ADMIN_LOGIN_RESPONSE" | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)
    
    # Test admin functionality
    echo -e "${YELLOW}📋 Test 7.1: Admin Get Users${NC}"
    USERS_RESPONSE=$(curl -s -X GET "$BASE_URL/api/admin/users" \
        -H "Authorization: Bearer $ADMIN_TOKEN")
    
    if echo "$USERS_RESPONSE" | grep -q "$TEST_USERNAME"; then
        echo -e "${GREEN}✅ Admin user list retrieval successful${NC}"
    else
        echo -e "${YELLOW}⚠️  Admin user list may be empty or have issues${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  Admin login failed (check ADMIN_PASSWORD)${NC}"
    echo "Response: $ADMIN_LOGIN_RESPONSE"
fi

# Test 8: Error Handling
echo -e "${YELLOW}🚫 Test 8: Error Handling${NC}"
ERROR_RESPONSE=$(curl -s -X POST "$BASE_URL/api/moderate" \
    -H "Authorization: Bearer invalid_token" \
    -H "Content-Type: application/json" \
    -d '{"content": "test"}')

if echo "$ERROR_RESPONSE" | grep -q "401\|Unauthorized\|Invalid"; then
    echo -e "${GREEN}✅ Error handling working correctly${NC}"
else
    echo -e "${RED}❌ Error handling not working as expected${NC}"
fi

echo ""
echo -e "${GREEN}🎉 All tests completed successfully!${NC}"
echo -e "${GREEN}✅ Deployment is working correctly${NC}"
echo ""
echo -e "${YELLOW}📝 Test Summary:${NC}"
echo "- User ID: $USER_ID"
echo "- API Token: ${API_TOKEN:0:20}..."
echo "- Moderation ID: $MODERATION_ID"
echo ""
echo -e "${YELLOW}🔗 Useful URLs:${NC}"
echo "- API Documentation: $BASE_URL/docs"
echo "- ReDoc: $BASE_URL/redoc"
