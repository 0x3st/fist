"""
FIST Content Moderation System - Pure API Service

This is the main application file for the FIST system providing a FastAPI-based content moderation service.

The system provides:
- Pure REST API endpoints for content moderation
- AI model integration for content assessment
- PostgreSQL database for storing moderation results (with SQLite fallback for local development)
- Intelligent content piercing based on length
- Configurable decision thresholds
- User and token management via API

Architecture:
- AI component returns only probability scores (0-100%) with brief reasons
- analyze_result() function handles final decision-making logic based on configurable thresholds
- Clear separation between AI assessment and business logic decisions
- Simplified risk levels: LOW (≤20%) → APPROVED, MEDIUM (21-80%) → MANUAL_REVIEW, HIGH (>80%) → REJECTED
- No web UI - pure API service for frontend integration
- Vercel deployment ready with PostgreSQL support
"""
import os
from contextlib import asynccontextmanager
from datetime import datetime
from fastapi import FastAPI, Request, status
from fastapi.responses import HTMLResponse, JSONResponse

from config import Config
from models import ErrorResponse
from database import create_tables, load_config_from_database
from api_routes import router as api_router
from user_routes import router as user_router
from admin_routes import router as admin_router

# Lifespan event handler
@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Lifespan event handler for startup and shutdown."""
    # Startup
    try:
        create_tables()
        load_config_from_database()
    except Exception as e:
        print(f"Database initialization error: {e}")
        # For Vercel deployment, we might need to handle database connection issues gracefully
        # The app will still start but database operations might fail
    yield
    # Shutdown (if needed)


# Create FastAPI app
app = FastAPI(
    title="FIST Content Moderation API",
    description="Fast, Intuitive and Sensitive Test - Content Moderation System",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)


def markdown_to_html(markdown_text: str) -> str:
    """Convert markdown to HTML with basic formatting."""
    import re

    html = markdown_text

    # Code blocks
    html = re.sub(r'```(\w+)?\n(.*?)\n```', r'<pre><code class="\1">\2</code></pre>', html, flags=re.DOTALL)
    html = re.sub(r'```\n(.*?)\n```', r'<pre><code>\1</code></pre>', html, flags=re.DOTALL)

    # Headers
    html = re.sub(r'^### (.*$)', r'<h3>\1</h3>', html, flags=re.MULTILINE)
    html = re.sub(r'^## (.*$)', r'<h2>\1</h2>', html, flags=re.MULTILINE)
    html = re.sub(r'^# (.*$)', r'<h1>\1</h1>', html, flags=re.MULTILINE)

    # Bold and italic
    html = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', html)
    html = re.sub(r'\*(.*?)\*', r'<em>\1</em>', html)

    # Links
    html = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2" target="_blank">\1</a>', html)

    # Lists
    html = re.sub(r'^- (.*$)', r'<li>\1</li>', html, flags=re.MULTILINE)
    html = re.sub(r'(<li>.*</li>)', r'<ul>\1</ul>', html, flags=re.DOTALL)
    html = re.sub(r'</ul>\s*<ul>', '', html)

    # Line breaks
    html = html.replace('\n\n', '</p><p>')
    html = html.replace('\n', '<br>')
    html = f'<p>{html}</p>'

    # Clean up empty paragraphs
    html = re.sub(r'<p>\s*</p>', '', html)
    html = re.sub(r'<p>(<h[1-6]>)', r'\1', html)
    html = re.sub(r'(</h[1-6]>)</p>', r'\1', html)
    html = re.sub(r'<p>(<ul>)', r'\1', html)
    html = re.sub(r'(</ul>)</p>', r'\1', html)
    html = re.sub(r'<p>(<pre>)', r'\1', html)
    html = re.sub(r'(</pre>)</p>', r'\1', html)

    return html


def read_readme() -> str:
    """Read README.md file and convert to HTML."""
    try:
        readme_path = os.path.join(os.path.dirname(__file__), "README.md")
        with open(readme_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Convert markdown to HTML
        html_content = markdown_to_html(content)

        return f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>FIST Content Moderation System</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: #f8f9fa;
            color: #333;
        }}
        .container {{
            background: white;
            padding: 40px;
            border-radius: 12px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.1);
        }}
        .status-banner {{
            background: linear-gradient(135deg, #28a745, #20c997);
            color: white;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 30px;
            text-align: center;
            box-shadow: 0 2px 10px rgba(40, 167, 69, 0.3);
        }}
        .status-banner h2 {{
            margin: 0;
            font-size: 1.5rem;
        }}
        .quick-nav {{
            display: flex;
            gap: 15px;
            margin-bottom: 30px;
            flex-wrap: wrap;
        }}
        .nav-btn {{
            display: inline-flex;
            align-items: center;
            padding: 12px 20px;
            background: #007bff;
            color: white;
            text-decoration: none;
            border-radius: 6px;
            font-weight: 500;
            transition: all 0.3s ease;
            box-shadow: 0 2px 8px rgba(0, 123, 255, 0.3);
        }}
        .nav-btn:hover {{
            background: #0056b3;
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0, 123, 255, 0.4);
            text-decoration: none;
            color: white;
        }}
        .nav-btn .icon {{
            margin-right: 8px;
            font-size: 1.1em;
        }}
        .readme-content {{
            border-top: 2px solid #e9ecef;
            padding-top: 30px;
        }}
        h1 {{
            color: #2c3e50;
            border-bottom: 3px solid #007bff;
            padding-bottom: 10px;
            margin-bottom: 20px;
        }}
        h2 {{
            color: #495057;
            border-bottom: 1px solid #dee2e6;
            padding-bottom: 8px;
            margin-top: 30px;
            margin-bottom: 15px;
        }}
        h3 {{
            color: #6c757d;
            margin-top: 25px;
            margin-bottom: 12px;
        }}
        pre {{
            background: #f8f9fa;
            border: 1px solid #e9ecef;
            padding: 16px;
            border-radius: 6px;
            overflow-x: auto;
            border-left: 4px solid #007bff;
            margin: 15px 0;
        }}
        code {{
            background: #f8f9fa;
            padding: 2px 6px;
            border-radius: 4px;
            font-family: 'SFMono-Regular', 'Monaco', 'Consolas', monospace;
            font-size: 0.9em;
            border: 1px solid #e9ecef;
        }}
        pre code {{
            background: none;
            padding: 0;
            border: none;
        }}
        ul {{
            padding-left: 20px;
        }}
        li {{
            margin-bottom: 5px;
        }}
        a {{
            color: #007bff;
            text-decoration: none;
        }}
        a:hover {{
            color: #0056b3;
            text-decoration: underline;
        }}
        .footer {{
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #e9ecef;
            text-align: center;
            color: #6c757d;
            font-size: 0.9em;
        }}
        @media (max-width: 768px) {{
            body {{ padding: 10px; }}
            .container {{ padding: 20px; }}
            .quick-nav {{ flex-direction: column; }}
            .nav-btn {{ justify-content: center; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="status-banner">
            <h2>🛡️ FIST Content Moderation System</h2>
            <p style="margin: 5px 0 0 0; opacity: 0.9;">系统运行正常 | Fast, Intuitive and Sensitive Test</p>
        </div>

        <div class="quick-nav">
            <a href="/docs" class="nav-btn" target="_blank">
                <span class="icon">📚</span>
                API 文档 (Swagger)
            </a>
            <a href="/redoc" class="nav-btn" target="_blank">
                <span class="icon">📖</span>
                API 文档 (ReDoc)
            </a>
        </div>

        <div class="readme-content">
            {html_content}
        </div>

        <div class="footer">
            <p>© 2024 FIST Content Moderation System | 基于 FastAPI 构建</p>
        </div>
    </div>
</body>
</html>"""
    except Exception as e:
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>FIST Content Moderation System</title>
            <meta charset="utf-8">
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; }}
                .error {{ background: #f8d7da; border: 1px solid #f5c6cb; color: #721c24; padding: 15px; border-radius: 5px; }}
                .links {{ margin: 20px 0; }}
                .links a {{ margin-right: 20px; }}
            </style>
        </head>
        <body>
            <h1>FIST Content Moderation System</h1>
            <div class="error">
                ⚠️ Could not load README.md: {str(e)}
            </div>
            <div class="links">
                <a href="/docs">📚 API Documentation</a>
                <a href="/redoc">📖 ReDoc</a>
            </div>
            <p>The FIST Content Moderation System is running successfully!</p>
        </body>
        </html>
        """


@app.get("/", response_class=HTMLResponse)
async def read_root():
    """Display README content at root path."""
    return read_readme()


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(_request: Request, exc: Exception):
    """Global exception handler."""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            error="Internal server error",
            detail=str(exc),
            timestamp=datetime.now()
        ).model_dump()
    )


# Include routers
app.include_router(api_router)
app.include_router(user_router)
app.include_router(admin_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app:app",
        host=Config.API_HOST,
        port=Config.API_PORT,
        reload=Config.DEBUG
    )
