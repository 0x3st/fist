"""
Vercel serverless function entry point for FIST Content Moderation System.
"""
import sys
import os

# Add the parent directory to the Python path so we can import our modules
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

try:
    from app import app
    # Export the FastAPI app directly for Vercel
    # Vercel will automatically handle the ASGI interface
except ImportError as e:
    # Fallback for debugging
    from fastapi import FastAPI
    app = FastAPI(title="FIST Debug", description="Debug mode - import failed")

    @app.get("/")
    def debug_root():
        return {
            "status": "debug_mode",
            "error": str(e),
            "python_path": sys.path,
            "current_dir": current_dir,
            "parent_dir": parent_dir,
            "files_in_parent": os.listdir(parent_dir) if os.path.exists(parent_dir) else "parent_dir_not_found"
        }
