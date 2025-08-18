from fastapi import FastAPI
from agent import create_bedrock_agent
from utils.logger import get_logger
import os
from dotenv import load_dotenv
from contextlib import asynccontextmanager
from router import router, set_bedrock_agent

# Load environment variables from .env file
load_dotenv()

# Get logger for main module
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize and cleanup resources"""
    logger.info("Starting Echo MCP Client API with Amazon Bedrock Nova Pro")
    
    # Check AWS credentials
    aws_access_key = os.getenv('AWS_ACCESS_KEY_ID')
    aws_region = os.getenv('AWS_DEFAULT_REGION')
    
    if not aws_access_key:
        logger.error("AWS credentials not found in environment variables")
        raise RuntimeError("AWS credentials not configured")
    
    logger.info(f"AWS credentials loaded successfully (Access Key: {aws_access_key[:8]}...)")
    logger.info(f"AWS region: {aws_region}")
    
    # Initialize Bedrock agent
    try:
        logger.debug("Initializing Bedrock agent...")
        bedrock_agent = create_bedrock_agent()
        logger.info("Bedrock agent initialized successfully")
        
        # Set the agent in the router
        set_bedrock_agent(bedrock_agent)
        
        # Test connection
        logger.debug("Testing Bedrock connection...")
        if bedrock_agent.test_connection():
            logger.info("Connection to Bedrock successful")
        else:
            logger.error("Connection to Bedrock failed")
            raise RuntimeError("Failed to connect to Bedrock")
            
    except Exception as e:
        logger.error(f"Error initializing Bedrock agent: {e}")
        raise RuntimeError(f"Failed to initialize Bedrock agent: {e}")
    
    yield
    
    # Cleanup
    logger.info("Shutting down Echo MCP Client API")


# Create FastAPI app
app = FastAPI(
    title="Echo MCP Client API",
    description="API for interacting with Amazon Bedrock Nova Pro via MCP",
    version="0.1.0",
    lifespan=lifespan
)

# Include the router
app.include_router(router)


if __name__ == "__main__":
    import uvicorn
    
    # Run the FastAPI server
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
