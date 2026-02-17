"""
Vercel Serverless Function Wrapper for FastAPI
This allows the FastAPI backend to run on Vercel as serverless functions
"""
import sys
import os
import traceback

# Add backend to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../backend'))

from mangum import Mangum
from backend.app.main import app

# Mangum converts ASGI apps (FastAPI) to AWS Lambda event format
# We disable lifespan to prevent startup/shutdown issues in serverless
handler = Mangum(app, lifespan="off")

# Add logging for debugging
import logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Wrap handler to catch and log errors
def lambda_handler(event, context):
    try:
        logger.info(f"Received event: {event.get('path', 'unknown')}")
        response = handler(event, context)
        logger.info(f"Response status: {response.get('statusCode', 'unknown')}")
        return response
    except Exception as e:
        logger.error(f"Error in lambda_handler: {str(e)}")
        logger.error(traceback.format_exc())
        return {
            'statusCode': 500,
            'body': f'Internal Server Error: {str(e)}',
            'headers': {'Content-Type': 'application/json'}
        }

# Export both handler names for compatibility
handler = lambda_handler
app_handler = lambda_handler