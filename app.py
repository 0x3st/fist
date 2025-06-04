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
from typing import Callable, Awaitable, Union, Any
from fastapi import FastAPI, Request, status
from fastapi.responses import HTMLResponse, JSONResponse, Response
from fastapi.middleware.cors import CORSMiddleware
import time

from core.config import Config
from core.models import ErrorResponse
from core.database import create_tables, load_config_from_database
from routes.api_routes import router as api_router
from routes.user_routes import router as user_router
from routes.admin_routes import router as admin_router
from utils.monitoring import metrics_collector

# Lifespan event handler
@asynccontextmanager
async def lifespan(app_instance: FastAPI):  # noqa: ARG001
    """Lifespan event handler for startup and shutdown."""
    # Startup
    try:
        create_tables()
        load_config_from_database()
    except Exception as e:
        print(f"Database initialization error: {e}")
        # Continue startup even if database initialization fails
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

# Add CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Performance monitoring middleware
@app.middleware("http")
async def performance_monitoring_middleware(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    """Middleware to monitor API performance and collect metrics."""
    start_time = time.time()

    # Process request
    response: Response = await call_next(request)

    # Calculate processing time
    process_time = time.time() - start_time

    # Record metrics
    if hasattr(metrics_collector, 'record_request'):
        metrics_collector.record_request(
            endpoint=request.url.path,
            method=request.method,
            status_code=response.status_code,
            duration=process_time
        )

    # Add performance headers
    response.headers["X-Process-Time"] = str(process_time)

    return response


def markdown_to_html(markdown_text: str) -> str:
    """Convert markdown to HTML using mistune library."""
    try:
        import mistune

        # Create markdown parser with GitHub-flavored markdown features
        markdown = mistune.create_markdown(
            escape=False,  # Don't escape HTML
            plugins=['strikethrough', 'footnotes', 'table']
        )

        result = markdown(markdown_text)
        # Ensure we return a string
        return str(result) if not isinstance(result, str) else result
    except ImportError:
        # Fallback to basic conversion if mistune is not available
        import re
        html = markdown_text

        # Basic markdown conversion as fallback
        html = re.sub(r'```(\w+)?\n(.*?)\n```', r'<pre><code class="\1">\2</code></pre>', html, flags=re.DOTALL)
        html = re.sub(r'^### (.*$)', r'<h3>\1</h3>', html, flags=re.MULTILINE)
        html = re.sub(r'^## (.*$)', r'<h2>\1</h2>', html, flags=re.MULTILINE)
        html = re.sub(r'^# (.*$)', r'<h1>\1</h1>', html, flags=re.MULTILINE)
        html = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', html)
        html = re.sub(r'\*(.*?)\*', r'<em>\1</em>', html)
        html = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2" target="_blank">\1</a>', html)
        html = re.sub(r'^- (.*$)', r'<li>\1</li>', html, flags=re.MULTILINE)
        html = re.sub(r'(<li>.*</li>)', r'<ul>\1</ul>', html, flags=re.DOTALL)
        html = html.replace('\n\n', '</p><p>')
        html = html.replace('\n', '<br>')
        html = f'<p>{html}</p>'

        return html


def read_readme() -> str:
    """Read README.md file and convert to HTML like GitHub."""
    try:
        # Try multiple possible paths for README.md
        possible_paths = [
            os.path.join(os.path.dirname(__file__), "README.md"),  # Same directory as app.py
            os.path.join(os.path.dirname(os.path.dirname(__file__)), "README.md"),  # Parent directory
            "README.md",  # Current working directory
        ]

        content = None
        for readme_path in possible_paths:
            if os.path.exists(readme_path):
                with open(readme_path, "r", encoding="utf-8") as f:
                    content = f.read()
                break

        if content is None:
            raise FileNotFoundError("README.md not found in any expected location")

        # Convert markdown to HTML
        html_content = markdown_to_html(content)

        return f"""<!DOCTYPE html>
<html>
<head>
    <title>FIST Content Moderation API</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Noto Sans', Helvetica, Arial, sans-serif;
            line-height: 1.5;
            color: #1f2328;
            background-color: #ffffff;
            margin: 0;
            padding: 16px;
            max-width: 1012px;
            margin: 0 auto;
        }}
        h1 {{
            font-size: 2em;
            font-weight: 600;
            padding-bottom: 0.3em;
            border-bottom: 1px solid #d1d9e0;
            margin-bottom: 16px;
        }}
        h2 {{
            font-size: 1.5em;
            font-weight: 600;
            padding-bottom: 0.3em;
            border-bottom: 1px solid #d1d9e0;
            margin-top: 24px;
            margin-bottom: 16px;
        }}
        h3 {{
            font-size: 1.25em;
            font-weight: 600;
            margin-top: 24px;
            margin-bottom: 16px;
        }}
        h4 {{
            font-size: 1em;
            font-weight: 600;
            margin-top: 24px;
            margin-bottom: 16px;
        }}
        p {{
            margin-top: 0;
            margin-bottom: 16px;
        }}
        pre {{
            background-color: #f6f8fa;
            border-radius: 6px;
            font-size: 85%;
            line-height: 1.45;
            overflow: auto;
            padding: 16px;
            margin-bottom: 16px;
        }}
        code {{
            background-color: rgba(175,184,193,0.2);
            border-radius: 6px;
            font-size: 85%;
            margin: 0;
            padding: 0.2em 0.4em;
            font-family: ui-monospace, SFMono-Regular, "SF Mono", Consolas, "Liberation Mono", Menlo, monospace;
        }}
        pre code {{
            background-color: transparent;
            border: 0;
            display: inline;
            line-height: inherit;
            margin: 0;
            overflow: visible;
            padding: 0;
            word-wrap: normal;
        }}
        ul, ol {{
            margin-top: 0;
            margin-bottom: 16px;
            padding-left: 2em;
        }}
        li {{
            margin-top: 0.25em;
        }}
        a {{
            color: #0969da;
            text-decoration: none;
        }}
        a:hover {{
            text-decoration: underline;
        }}
        strong {{
            font-weight: 600;
        }}
        em {{
            font-style: italic;
        }}
        blockquote {{
            margin: 0;
            padding: 0 1em;
            color: #656d76;
            border-left: 0.25em solid #d1d9e0;
        }}
        table {{
            border-spacing: 0;
            border-collapse: collapse;
            margin-top: 0;
            margin-bottom: 16px;
        }}
        table th, table td {{
            padding: 6px 13px;
            border: 1px solid #d1d9e0;
        }}
        table th {{
            font-weight: 600;
            background-color: #f6f8fa;
        }}
        hr {{
            height: 0.25em;
            padding: 0;
            margin: 24px 0;
            background-color: #d1d9e0;
            border: 0;
        }}
    </style>
</head>
<body>
    {html_content}
</body>
</html>"""
    except Exception as e:
        return f"""<!DOCTYPE html>
<html>
<head>
    <title>FIST Content Moderation API</title>
    <meta charset="utf-8">
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            margin: 40px;
            color: #1f2328;
        }}
        .error {{
            background: #fff8f0;
            border: 1px solid #d1242f;
            color: #d1242f;
            padding: 16px;
            border-radius: 6px;
            margin: 16px 0;
        }}
        .links {{ margin: 20px 0; }}
        .links a {{
            color: #0969da;
            text-decoration: none;
            margin-right: 20px;
        }}
        .links a:hover {{ text-decoration: underline; }}
    </style>
</head>
<body>
    <h1>FIST Content Moderation API</h1>
    <div class="error">
        ⚠️ Could not load README.md: {str(e)}
    </div>
    <div class="links">
        <a href="/docs">📚 API Documentation</a>
        <a href="/redoc">📖 ReDoc</a>
    </div>
    <p>The FIST Content Moderation System is running successfully!</p>
</body>
</html>"""


@app.get("/", response_class=HTMLResponse)
async def read_root():
    """Display README content at root path."""
    return read_readme()


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):  # noqa: ARG001
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
