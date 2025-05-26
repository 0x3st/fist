# FIST Content Moderation System

A production-ready FastAPI-based content moderation system that uses AI to assess content appropriateness with intelligent content piercing.

## Introduction

The F.I.S.T. stands for "Fast, Intuitive and Sensitive Test" - a philosophy for efficient content supervision. The system automatically analyzes content using AI to determine appropriateness.

## Features

- **AI-Powered Moderation**: Uses DeepSeek AI for content analysis
- **Intelligent Content Piercing**: Automatically selects content portions based on length to optimize AI token usage
- **Decision Engine**: Returns Approved (A), Rejected (R), or Manual Review (M) decisions
- **SQLite Database**: Stores all moderation results with complete audit trail
- **REST API**: Clean, documented endpoints with automatic OpenAPI documentation
- **Admin Web Interface**: Bootstrap-based admin panel with authentication
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

### Core Endpoints

#### `POST /moderate`
Submit content for moderation.

**Request:**
```json
{
  "content": "Your content to moderate"
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

#### Other Endpoints
- `GET /results/{moderation_id}` - Get moderation result by ID
- `GET /health` - Health check endpoint
- `GET /admin/stats` - Get moderation statistics
- `GET /admin/records` - Get all moderation records

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

### Security Features
- **Authentication Required**: All admin functions require login
- **Session Timeout**: Automatic logout after inactivity
- **Input Validation**: All configuration changes are validated
- **Error Handling**: Comprehensive error messages and recovery

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
```

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

## File Structure

```
├── app.py              # Main FastAPI application (all-in-one)
├── ai_connector.py     # AI model integration
├── text_class.py       # Text processing utilities
├── main.py             # Legacy CLI interface
├── pyproject.toml      # Dependencies
└── README.md           # This file
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
