"""
Vercel serverless function entry point for FIST Content Moderation System.
"""
import sys
import os

# Add the parent directory to the Python path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app

# Vercel expects a handler function
def handler(request, response):
    return app(request, response)

# For Vercel, we also need to export the app directly
# This is the main entry point that Vercel will use
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
