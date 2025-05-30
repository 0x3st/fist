# FIST Content Moderation System

A production-ready FastAPI-based content moderation system that uses AI to assess content appropriateness with intelligent content piercing.

## Introduction

The F.I.S.T. stands for "Fast, Intuitive and Sensitive Test" - a philosophy for efficient content supervision. The system automatically analyzes content using AI to determine appropriateness.

## Features

- **AI-Powered Moderation**: Uses DeepSeek AI for content analysis
- **Intelligent Content Piercing**: Automatically selects content portions based on length to optimize AI token usage
- **Decision Engine**: Returns Approved (A), Rejected (R), or Manual Review (M) decisions
- **User Authentication & Management**: Complete user registration, login, and API token management
- **Invitation Code System**: Control user registration with optional invitation codes
- **Usage Tracking**: Monitor API usage per user and token with detailed statistics
- **SQLite Database**: Stores all moderation results with complete audit trail
- **REST API**: Clean, documented endpoints with automatic OpenAPI documentation
- **Admin Web Interface**: Bootstrap-based admin panel with user management
- **Configuration Management**: Real-time configuration updates through web UI
- **Production Ready**: Error handling, validation, and proper HTTP status codes

## Quick Start

### 1. Install Dependencies
```bash
uv sync
```

### 2. Start the API Server
```bash
python app.py
```

### 3. Access the System
- **Admin Interface**: http://localhost:8000/admin (admin / admin123)
- **API Documentation**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## API Endpoints

### Authentication Required

**⚠️ IMPORTANT: All moderation endpoints now require API token authentication.**

### Quick Start

1. **Register a user:**
```bash
# Without invitation code (if REQUIRE_INVITATION_CODE=False)
curl -X POST http://localhost:8000/user/register \
  -H "Content-Type: application/json" \
  -d '{"username": "myuser", "password": "mypassword123"}'

# With invitation code (if REQUIRE_INVITATION_CODE=True)
curl -X POST http://localhost:8000/user/register \
  -H "Content-Type: application/json" \
  -d '{"username": "myuser", "password": "mypassword123", "invitation_code": "your_invitation_code"}'
```

2. **Login to get access token:**
```bash
curl -X POST http://localhost:8000/user/login \
  -H "Content-Type: application/json" \
  -d '{"username": "myuser", "password": "mypassword123"}'
```

3. **Create API token:**
```bash
curl -X POST http://localhost:8000/user/tokens \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{"name": "My API Token"}'
```

4. **Use API token for moderation:**
```bash
curl -X POST http://localhost:8000/moderate \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_API_TOKEN" \
  -d '{"content": "Content to moderate"}'
```

## Invitation Code System

When `REQUIRE_INVITATION_CODE=True`, users need invitation codes to register. Here's the complete workflow:

### For Administrators

1. **Access Admin Interface:**
   - Navigate to: http://localhost:8000/admin
   - Login with admin credentials (default: `admin`/`admin123`)

2. **Create Invitation Code:**
   - Go to "Users" section in the admin interface
   - Find the "Create Invitation Code" form
   - Configure the invitation code:
     - **Max Uses** (optional): Limit how many users can use this code
     - **Expires in Days** (optional): Set when the code expires
   - Click "Create Code"

3. **Manage Invitation Codes:**
   - View all invitation codes in the "Invitation Codes" table
   - See usage statistics (current uses vs. max uses)
   - Deactivate codes when needed
   - Monitor expiration dates

### For Users

1. **Get Invitation Code:**
   - Obtain an invitation code from the system administrator
   - Example code format: `abc123def456ghi789`

2. **Register with Invitation Code:**
   ```bash
   curl -X POST http://localhost:8000/user/register \
     -H "Content-Type: application/json" \
     -d '{
       "username": "newuser",
       "password": "securepass123",
       "invitation_code": "abc123def456ghi789"
     }'
   ```

3. **Registration Validation:**
   The system will validate:
   - ✅ Code exists and is active
   - ✅ Code hasn't expired
   - ✅ Code hasn't reached maximum uses
   - ✅ Username is available
   - ✅ System hasn't reached user limit

### Error Messages

Common invitation code errors:
- `"Invitation code is required for registration"` - Include invitation_code in request
- `"Invalid invitation code"` - Code doesn't exist
- `"Invitation code is inactive"` - Code has been deactivated
- `"Invitation code has expired"` - Code is past expiration date
- `"Invitation code has reached maximum uses"` - Code usage limit exceeded
- `"Maximum number of users reached"` - System user limit reached

### Configuration Options

```bash
# Enable/disable invitation requirement
export REQUIRE_INVITATION_CODE="True"   # or "False"

# Set maximum users allowed
export MAX_USERS="100"

# Configure invitation code prefix
export API_TOKEN_PREFIX="fist_"
```

### Core Endpoints

#### `POST /moderate`
Submit content for moderation. **Requires API token authentication.**

**Headers:**
```
Authorization: Bearer fist_your_api_token_here
Content-Type: application/json
```

**Request:**
```json
{
  "content": "Your content to moderate",
  "percentages": [0.8, 0.6, 0.4, 0.2],
  "thresholds": [500, 1000, 3000],
  "probability_thresholds": {"low": 20, "high": 80}
}
```

**Response:**
```json
{
  "moderation_id": "uuid-string",
  "status": "completed",
  "result": {
    "final_decision": "A",
    "reason": "Low risk (15%): Content appears appropriate...",
    "ai_result": {
      "inappropriate_probability": 15,
      "reason": "Content appears appropriate..."
    }
  }
}
```

### User Management Endpoints
- `POST /user/register` - Register new user
- `POST /user/login` - User login
- `POST /user/tokens` - Create API token (requires user auth)
- `GET /user/tokens` - List API tokens (requires user auth)
- `DELETE /user/tokens/{token_id}` - Delete API token (requires user auth)
- `GET /user/usage` - Get usage statistics (requires user auth)

#### Other Endpoints
- `GET /results/{moderation_id}` - Get moderation result by ID
- `GET /health` - Health check endpoint
- `GET /admin/stats` - Get moderation statistics (admin only)
- `GET /admin/records` - Get all moderation records (admin only)

## Admin Interface

The system includes a comprehensive web-based admin interface with the following features:

### Authentication
- **Login URL**: http://localhost:8000/admin
- **Default Credentials**: admin / admin123
- **Session Management**: JWT-based authentication with secure cookies

### Dashboard
- **System Statistics**: Total moderations, approval rates, rejection rates
- **Performance Metrics**: Average inappropriateness probability
- **Recent Records**: Latest moderation results with quick overview

### Configuration Management
- **Content Piercing Settings**: Adjust percentages and word count thresholds
- **Decision Thresholds**: Configure low/high probability thresholds for automated decisions
- **AI Model Selection**: Choose between different AI models
- **Real-time Updates**: Configuration changes take effect immediately

### Records Management
- **Complete Audit Trail**: View all moderation records with full details
- **Search and Filter**: Find specific records quickly
- **Detailed View**: Click any record to see complete information
- **Export Capability**: Access to all moderation data

### User Management
- **User Administration**: Create, deactivate, and manage user accounts
- **Password Management**: Reset user passwords from admin interface
- **Invitation Codes**: Generate and manage invitation codes for registration
- **Usage Statistics**: Monitor user activity and API usage
- **User Limits**: Configure maximum number of users

### Security Features
- **Authentication Required**: All admin functions require login
- **Session Timeout**: Automatic logout after inactivity
- **Input Validation**: All configuration changes are validated
- **Error Handling**: Comprehensive error messages and recovery
- **Token-based API Access**: Secure API authentication with user tokens

## Configuration

Configure via environment variables:

```bash
# AI Configuration
export AI_API_KEY="your-deepseek-api-key"
export AI_BASE_URL="https://api.deepseek.com"
export AI_MODEL="deepseek-chat"

# API Configuration
export API_HOST="0.0.0.0"
export API_PORT="8000"
export DEBUG="false"

# Admin Authentication
export ADMIN_USERNAME="admin"
export ADMIN_PASSWORD="your-secure-password"
export SECRET_KEY="your-secret-key"

# User Management Configuration
export MAX_USERS="100"                          # Maximum number of users allowed
export REQUIRE_INVITATION_CODE="True"           # Whether registration requires invitation codes
export USER_TOKEN_EXPIRE_MINUTES="60"           # User session token expiry (minutes)
export API_TOKEN_PREFIX="fist_"                 # Prefix for API tokens
```

## User Authentication & Management

The system includes comprehensive user authentication and token management with role-based access control.

### Complete User Workflow

#### 1. **User Registration**
```python
import requests

# Register new user (with invitation code if required)
response = requests.post("http://localhost:8000/user/register", json={
    "username": "myuser",
    "password": "securepass123",
    "invitation_code": "abc123def456"  # Include if REQUIRE_INVITATION_CODE=True
})
```

#### 2. **User Login & Session Management**
```python
# Login to get access token
response = requests.post("http://localhost:8000/user/login", json={
    "username": "myuser",
    "password": "securepass123"
})
access_token = response.json()["access_token"]
```

#### 3. **API Token Management**
```python
headers = {"Authorization": f"Bearer {access_token}"}

# Create API token for applications
response = requests.post("http://localhost:8000/user/tokens",
    json={"name": "My App Token"}, headers=headers)
api_token = response.json()["token"]

# List all tokens
response = requests.get("http://localhost:8000/user/tokens", headers=headers)

# Delete a token
response = requests.delete(f"http://localhost:8000/user/tokens/{token_id}", headers=headers)
```

#### 4. **Content Moderation**
```python
# Use API token for moderation requests
api_headers = {"Authorization": f"Bearer {api_token}"}
response = requests.post("http://localhost:8000/moderate",
    json={"content": "Content to moderate"}, headers=api_headers)
```

#### 5. **Usage Monitoring**
```python
# Check usage statistics
response = requests.get("http://localhost:8000/user/usage", headers=headers)
stats = response.json()
print(f"Total requests: {stats['total_requests']}")
print(f"Requests today: {stats['requests_today']}")
```

### Admin User Management

Administrators can manage users through the web interface:

1. **User Administration:**
   - Create users directly (bypassing invitation codes)
   - Deactivate/reactivate user accounts
   - Reset user passwords
   - View user activity and statistics

2. **Invitation Code Management:**
   - Generate invitation codes with custom settings
   - Set expiration dates and usage limits
   - Monitor code usage and deactivate when needed

3. **System Configuration:**
   - Set maximum user limits
   - Configure invitation code requirements
   - Monitor system-wide usage statistics

### Key Features
- **Secure Authentication**: JWT-based session management with bcrypt password hashing
- **API Token Management**: Create and manage multiple API tokens per user
- **Usage Tracking**: Detailed statistics per user and token with daily/monthly breakdowns
- **Invitation Codes**: Optional registration control with expiry and usage limits
- **Admin Controls**: Complete user lifecycle management through web interface
- **Audit Trail**: All moderation requests are linked to users for accountability

### Security Features
- **Password Security**: Bcrypt hashing with salt for secure password storage
- **Token Validation**: Bearer token authentication for all API endpoints
- **Session Management**: Configurable JWT token expiry times
- **Access Control**: Role-based permissions (admin vs. user)
- **Usage Monitoring**: Track and audit all API usage per user

For detailed API documentation and examples, see [USER_AUTHENTICATION_GUIDE.md](USER_AUTHENTICATION_GUIDE.md).

## Content Processing Logic

### 1. Content Piercing
Based on word count, different percentages of content are analyzed:
- **< 500 words**: 80% of content
- **500-1000 words**: 60% of content
- **1000-3000 words**: 40% of content
- **> 3000 words**: 20% of content

### 2. AI Analysis
The selected content portion is sent to the AI model for analysis.

### 3. Decision Making
Based on probability thresholds:
- **≤ 20%**: Approved (A)
- **21-80%**: Manual Review (M)
- **> 80%**: Rejected (R)

## Production Deployment

### Using Uvicorn
```bash
uvicorn app:app --host 0.0.0.0 --port 8000 --workers 4
```

### Using Gunicorn
```bash
pip install gunicorn
gunicorn app:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

## Testing

The system includes comprehensive test suites to verify functionality:

### 1. **Basic API Test**
```bash
python test_api.py
```
Tests user registration, login, token creation, content moderation, and usage statistics.

### 2. **Invitation Code Test**
```bash
python test_invitation.py
```
Tests admin login, invitation code creation, and registration validation.

### 3. **Manual Testing**
```bash
# Test health endpoint
curl http://localhost:8000/health

# Test admin interface
open http://localhost:8000/admin

# Test API documentation
open http://localhost:8000/docs
```

### Expected Test Results
```
=== FIST API Test Suite ===
✅ Health check: 200
✅ User registration: 200
✅ User login: 200
✅ API token creation: 200
✅ Content moderation: 200
✅ Usage statistics: 200
=== All tests completed ===
```

## File Structure

```
├── app.py                          # Main FastAPI application
├── models.py                       # Database models and Pydantic schemas
├── database.py                     # Database operations and connection
├── auth.py                         # Authentication and authorization
├── api_routes.py                   # API endpoints for content moderation
├── admin_routes.py                 # Admin web interface routes
├── user_routes.py                  # User management API endpoints
├── services.py                     # Business logic and AI integration
├── config.py                       # Configuration management
├── ai_connector.py                 # AI model integration
├── text_class.py                   # Text processing utilities
├── templates/                      # HTML templates for admin interface
│   ├── base.html                   # Base template
│   ├── dashboard.html              # Admin dashboard
│   ├── config.html                 # Configuration page
│   ├── records.html                # Moderation records
│   ├── users.html                  # User management
│   └── login.html                  # Admin login
├── test_api.py                     # API functionality tests
├── test_invitation.py              # Invitation code tests
├── USER_AUTHENTICATION_GUIDE.md   # Detailed authentication guide
├── pyproject.toml                  # Dependencies
└── README.md                       # This file
```

## FIST Terms of Service

1. We will never send sensitive data to any third-party without acquired permission.
2. Only content will come into the system for AI checking. No user information will be involved.
3. The system will only be used for content supervision.
4. The content supervision follows the TOS of the website/provided by website admin.
5. We only support regions where FIST is safe to use.
6. Users have the right to appeal any content flagged as inappropriate by the system.
7. We maintain logs of all content checks for audit purposes only.
8. The system may be updated periodically to improve accuracy and compliance.