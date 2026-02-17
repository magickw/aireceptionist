"""
Vercel Serverless Function Wrapper for FastAPI
This allows the FastAPI backend to run on Vercel as serverless functions
"""
import sys
import os

# Add backend to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../backend'))

from mangum import Mangum
from backend.app.main import app

# Mangum converts ASGI apps (FastAPI) to AWS Lambda event format
handler = Mangum(app, lifespan="off")