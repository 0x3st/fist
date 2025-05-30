# FIST Content Moderation API

A production-ready FastAPI-based content moderation service that uses AI to assess content appropriateness with intelligent content piercing.

## Introduction

The F.I.S.T. stands for "Fast, Intuitive and Sensitive Test" - a philosophy for efficient content supervision. This is a pure API service designed for frontend integration, providing comprehensive content moderation capabilities without any web UI.

## Features

- **Pure REST API**: Clean, documented endpoints with automatic OpenAPI documentation
- **AI-Powered Moderation**: Uses DeepSeek AI for content analysis
- **Intelligent Content Piercing**: Automatically selects content portions based on length to optimize AI token usage
- **Decision Engine**: Returns Approved (A), Rejected (R), or Manual Review (M) decisions
- **User Authentication & Management**: Complete user registration, login, and API token management via API
- **Invitation Code System**: Control user registration with optional invitation codes
- **Privacy-Focused Usage Tracking**: Monitor only token usage counts, no historical data
- **Privacy-Focused Database**: Stores only content hashes and essential metadata
- **Frontend-Ready**: Designed for integration with any frontend framework
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

### 3. Access the API
- **API Documentation**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/api/health

## API Endpoints

### Authentication Required

**⚠️ IMPORTANT: All moderation endpoints now require API token authentication.**

### Quick Start

1. **Register a user:**
```bash
# Without invitation code (if REQUIRE_INVITATION_CODE=False)
curl -X POST http://localhost:8000/api/user/register \
  -H "Content-Type: application/json" \
  -d '{"username": "myuser", "password": "mypassword123"}'

# With invitation code (if REQUIRE_INVITATION_CODE=True)
curl -X POST http://localhost:8000/api/user/register \
  -H "Content-Type: application/json" \
  -d '{"username": "myuser", "password": "mypassword123", "invitation_code": "your_invitation_code"}'
```

2. **Login to get access token:**
```bash
curl -X POST http://localhost:8000/api/user/login \
  -H "Content-Type: application/json" \
  -d '{"username": "myuser", "password": "mypassword123"}'
```

3. **Create API token:**
```bash
curl -X POST http://localhost:8000/api/user/tokens \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{"name": "My API Token"}'
```

4. **Use API token for moderation:**
```bash
curl -X POST http://localhost:8000/api/moderate \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_API_TOKEN" \
  -d '{"content": "Content to moderate"}'
```

## Invitation Code System

When `REQUIRE_INVITATION_CODE=True`, users need invitation codes to register. Invitation codes must be created via direct database access or by implementing your own admin interface.

### Registration with Invitation Code

```bash
curl -X POST http://localhost:8000/api/user/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "newuser",
    "password": "securepass123",
    "invitation_code": "abc123def456ghi789"
  }'
```

### Registration Validation

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

#### `POST /api/moderate`
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

## Complete API Reference

### Core Moderation Endpoints
- `POST /api/moderate` - Submit content for moderation (requires API token)
- `GET /api/results/{moderation_id}` - Get moderation result by ID
- `GET /api/health` - Health check endpoint

### User Management Endpoints
- `POST /api/user/register` - Register new user
- `POST /api/user/login` - User login
- `POST /api/user/tokens` - Create API token (requires user auth)
- `GET /api/user/tokens` - List API tokens (requires user auth)
- `DELETE /api/user/tokens/{token_id}` - Delete API token (requires user auth)
- `GET /api/user/usage` - Get usage statistics (requires user auth)

### Privacy Protection
- No admin statistics or records endpoints
- Content stored as SHA-256 hash only
- No historical data tracking
- Token usage tracking only

## Frontend Integration

This is a pure API service designed for integration with any frontend framework. You can build your own admin interface and user management UI using the provided API endpoints.

### Building Your Own Frontend

The API provides all necessary endpoints for:
- **User Management**: Registration, login, token management
- **Content Moderation**: Submit content and retrieve results
- **Admin Functions**: Statistics, records, user administration
- **Configuration**: All settings can be managed via environment variables

### Example Frontend Integrations

**React/Vue/Angular**: Use the API endpoints to build modern web applications
**Mobile Apps**: Integrate with iOS/Android applications
**Desktop Applications**: Build desktop clients using the REST API
**Other Services**: Integrate with existing systems via HTTP requests

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

# Authentication
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
response = requests.post("http://localhost:8000/api/user/register", json={
    "username": "myuser",
    "password": "securepass123",
    "invitation_code": "abc123def456"  # Include if REQUIRE_INVITATION_CODE=True
})
```

#### 2. **User Login & Session Management**
```python
# Login to get access token
response = requests.post("http://localhost:8000/api/user/login", json={
    "username": "myuser",
    "password": "securepass123"
})
access_token = response.json()["access_token"]
```

#### 3. **API Token Management**
```python
headers = {"Authorization": f"Bearer {access_token}"}

# Create API token for applications
response = requests.post("http://localhost:8000/api/user/tokens",
    json={"name": "My App Token"}, headers=headers)
api_token = response.json()["token"]

# List all tokens
response = requests.get("http://localhost:8000/api/user/tokens", headers=headers)

# Delete a token
response = requests.delete(f"http://localhost:8000/api/user/tokens/{token_id}", headers=headers)
```

#### 4. **Content Moderation**
```python
# Use API token for moderation requests
api_headers = {"Authorization": f"Bearer {api_token}"}
response = requests.post("http://localhost:8000/api/moderate",
    json={"content": "Content to moderate"}, headers=api_headers)
```

#### 5. **Usage Monitoring**
```python
# Check usage statistics
response = requests.get("http://localhost:8000/api/user/usage", headers=headers)
stats = response.json()
print(f"Total requests: {stats['total_requests']}")
print(f"Requests today: {stats['requests_today']}")
```

### Admin Functions

Administrators can manage the system through API endpoints and environment variables:

1. **User Administration:**
   - Monitor user activity via `/api/admin/stats`
   - View all moderation records via `/api/admin/records`
   - Manage invitation codes via direct database access

2. **System Configuration:**
   - Set maximum user limits via `MAX_USERS` environment variable
   - Configure invitation code requirements via `REQUIRE_INVITATION_CODE`
   - Configure AI settings via environment variables

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

For detailed API documentation and examples, visit the interactive API docs at `/docs` when the server is running.

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

## Testing

Test the API functionality:

### Manual Testing
```bash
# Test health endpoint
curl http://localhost:8000/api/health

# Test API documentation
open http://localhost:8000/docs

# Test user registration
curl -X POST http://localhost:8000/api/user/register \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "password": "testpass123"}'

# Test user login
curl -X POST http://localhost:8000/api/user/login \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "password": "testpass123"}'
```

### Expected Results
```
✅ Health check: {"status": "healthy", ...}
✅ User registration: {"user_id": "...", "username": "testuser", ...}
✅ User login: {"access_token": "...", "user": {...}}
✅ API documentation: Available at /docs
```

## File Structure

```
├── app.py                          # Main FastAPI application (pure API)
├── models.py                       # Database models and Pydantic schemas
├── database.py                     # Database operations and connection
├── auth.py                         # Authentication and authorization
├── api_routes.py                   # Core API endpoints for content moderation
├── user_routes.py                  # User management API endpoints
├── services.py                     # Business logic and AI integration
├── config.py                       # Configuration management
├── ai_connector.py                 # AI model integration
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