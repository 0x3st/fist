# FIST User Authentication & Token Management Guide

This guide explains how to use the new user authentication and token management system in the FIST Content Moderation API.

## Overview

The FIST system now includes comprehensive user authentication and token management features:

- **User Registration & Login**: Users can register and login to get access tokens
- **API Token Management**: Users can create, manage, and delete API tokens for programmatic access
- **Admin User Management**: Admins can manage users, invitation codes, and system settings
- **Usage Tracking**: Track API usage per user and token
- **Secure Authentication**: All moderation endpoints now require valid API tokens

## Configuration

### Environment Variables

```bash
# User Management Configuration
MAX_USERS=100                          # Maximum number of users allowed
REQUIRE_INVITATION_CODE=True            # Whether registration requires invitation codes
USER_TOKEN_EXPIRE_MINUTES=60           # User session token expiry (minutes)
API_TOKEN_PREFIX=fist_                 # Prefix for API tokens

# Existing Configuration
ADMIN_USERNAME=admin                   # Admin username
ADMIN_PASSWORD=admin123                # Admin password (change in production!)
SECRET_KEY=your-secret-key             # JWT secret key
```

## User Registration & Login

### 1. User Registration

**Endpoint**: `POST /user/register`

```json
{
    "username": "your_username",
    "password": "your_password",
    "invitation_code": "optional_invitation_code"
}
```

**Response**:
```json
{
    "user_id": "uuid",
    "username": "your_username",
    "created_at": "2025-05-28T19:28:38.701953",
    "is_active": true
}
```

### 2. User Login

**Endpoint**: `POST /user/login`

```json
{
    "username": "your_username",
    "password": "your_password"
}
```

**Response**:
```json
{
    "access_token": "jwt_token_here",
    "token_type": "bearer",
    "user": {
        "user_id": "uuid",
        "username": "your_username",
        "created_at": "2025-05-28T19:28:38.701953",
        "is_active": true
    }
}
```

## API Token Management

### 1. Create API Token

**Endpoint**: `POST /user/tokens`
**Headers**: `Authorization: Bearer <user_access_token>`

```json
{
    "name": "My API Token"
}
```

**Response**:
```json
{
    "token_id": "uuid",
    "name": "My API Token",
    "token": "fist_abc123...",
    "created_at": "2025-05-28T19:28:38.701953",
    "last_used": null,
    "is_active": true
}
```

### 2. List API Tokens

**Endpoint**: `GET /user/tokens`
**Headers**: `Authorization: Bearer <user_access_token>`

**Response**:
```json
[
    {
        "token_id": "uuid",
        "name": "My API Token",
        "token": null,
        "created_at": "2025-05-28T19:28:38.701953",
        "last_used": "2025-05-28T19:30:00.000000",
        "is_active": true
    }
]
```

### 3. Delete API Token

**Endpoint**: `DELETE /user/tokens/{token_id}`
**Headers**: `Authorization: Bearer <user_access_token>`

**Response**:
```json
{
    "message": "Token deleted successfully"
}
```

### 4. Usage Statistics

**Endpoint**: `GET /user/usage`
**Headers**: `Authorization: Bearer <user_access_token>`

**Response**:
```json
{
    "user_id": "uuid",
    "total_requests": 150,
    "requests_today": 25,
    "requests_this_month": 150,
    "tokens_count": 3
}
```

## Content Moderation with API Tokens

### Moderation Endpoint

**Endpoint**: `POST /moderate`
**Headers**: `Authorization: Bearer <api_token>`

```json
{
    "content": "Content to moderate",
    "percentages": [0.8, 0.6, 0.4, 0.2],
    "thresholds": [500, 1000, 3000],
    "probability_thresholds": {"low": 20, "high": 80}
}
```

**Response**:
```json
{
    "moderation_id": "uuid",
    "status": "completed",
    "result": {
        "moderation_id": "uuid",
        "original_content": "Content to moderate",
        "pierced_content": "Content to moderate",
        "ai_result": {
            "inappropriate_probability": 15,
            "reason": "Content appears appropriate"
        },
        "final_decision": "A",
        "reason": "Low risk (15%): Content appears appropriate",
        "created_at": "2025-05-28T19:28:38.701953",
        "word_count": 3,
        "percentage_used": 1.0
    }
}
```

## Admin Interface

### Accessing Admin Interface

1. Navigate to `http://localhost:8000/admin`
2. Login with admin credentials (default: admin/admin123)
3. Access the "Users" section from the navigation menu

### Admin Features

#### User Management
- **Create Users**: Add new users directly from admin interface
- **Deactivate Users**: Disable user accounts
- **Change Passwords**: Reset user passwords
- **View User Statistics**: See user count and limits

#### Invitation Code Management
- **Create Invitation Codes**: Generate codes for user registration
- **Set Expiration**: Configure code expiry dates
- **Usage Limits**: Set maximum number of uses per code
- **Deactivate Codes**: Disable invitation codes

#### System Configuration
- **User Limits**: Configure maximum number of users
- **Invitation Requirements**: Enable/disable invitation code requirement
- **Token Settings**: Configure API token prefixes and expiry

## Python Client Example

```python
import requests

# 1. Register a user
register_data = {
    "username": "myuser",
    "password": "mypassword123"
}
response = requests.post("http://localhost:8000/user/register", json=register_data)
user = response.json()

# 2. Login to get access token
login_data = {
    "username": "myuser",
    "password": "mypassword123"
}
response = requests.post("http://localhost:8000/user/login", json=login_data)
access_token = response.json()["access_token"]

# 3. Create API token
headers = {"Authorization": f"Bearer {access_token}"}
token_data = {"name": "My App Token"}
response = requests.post("http://localhost:8000/user/tokens", json=token_data, headers=headers)
api_token = response.json()["token"]

# 4. Use API token for moderation
api_headers = {"Authorization": f"Bearer {api_token}"}
moderation_data = {"content": "This is content to moderate"}
response = requests.post("http://localhost:8000/moderate", json=moderation_data, headers=api_headers)
result = response.json()

print(f"Moderation result: {result['result']['final_decision']}")
```

## Security Considerations

### Token Security
- **API Tokens**: Store securely, never expose in client-side code
- **Access Tokens**: Short-lived (60 minutes by default)
- **Password Hashing**: Uses bcrypt for secure password storage

### Best Practices
1. **Rotate API Tokens**: Regularly create new tokens and delete old ones
2. **Use HTTPS**: Always use HTTPS in production
3. **Monitor Usage**: Track API usage through the admin interface
4. **Limit User Access**: Use invitation codes to control registration

### Rate Limiting
- Consider implementing rate limiting based on user/token usage
- Monitor usage statistics to detect abuse

## Troubleshooting

### Common Issues

1. **"Valid API token required"**
   - Ensure you're using the correct API token
   - Check that the token hasn't been deactivated
   - Verify the Authorization header format: `Bearer <token>`

2. **"Invitation code is required"**
   - Set `REQUIRE_INVITATION_CODE=False` to disable requirement
   - Or create invitation codes through admin interface

3. **"Maximum number of users reached"**
   - Increase `MAX_USERS` environment variable
   - Or deactivate unused user accounts

4. **Database errors after upgrade**
   - Backup existing database: `cp fist.db fist.db.backup`
   - Delete old database: `rm fist.db`
   - Restart application to create new schema

## Migration from Previous Version

If upgrading from a previous version without user authentication:

1. **Backup Database**: `cp fist.db fist.db.backup`
2. **Update Environment**: Add new environment variables
3. **Recreate Database**: Delete old database to create new schema
4. **Update API Calls**: Add Authorization headers to moderation requests
5. **Create Users**: Register users and create API tokens

## API Reference Summary

| Endpoint | Method | Auth Required | Description |
|----------|--------|---------------|-------------|
| `/health` | GET | No | Health check |
| `/user/register` | POST | No | Register new user |
| `/user/login` | POST | No | User login |
| `/user/tokens` | POST | User Token | Create API token |
| `/user/tokens` | GET | User Token | List API tokens |
| `/user/tokens/{id}` | DELETE | User Token | Delete API token |
| `/user/usage` | GET | User Token | Get usage stats |
| `/moderate` | POST | API Token | Content moderation |
| `/results/{id}` | GET | No | Get moderation result |
| `/admin/*` | * | Admin Cookie | Admin interface |

## Support

For issues or questions:
1. Check the application logs
2. Verify configuration settings
3. Test with the provided test script: `python test_api.py`
4. Review this documentation for proper usage patterns
