"""
Vercel serverless function entry point for FIST Content Moderation System.
"""
import sys
import os

# Add the parent directory to the Python path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app

# Export the FastAPI app directly for Vercel
# Vercel will automatically handle the ASGI interface
app = app
