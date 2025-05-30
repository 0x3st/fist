"""
Simple test endpoint for Vercel deployment
"""
from fastapi import FastAPI

app = FastAPI(title="FIST Test", description="Simple test endpoint")

@app.get("/")
def read_root():
    return {"message": "FIST API is working!", "status": "ok"}

@app.get("/test")
def test_endpoint():
    return {"test": "success", "deployment": "vercel"}
