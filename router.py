"""
API routes for Echo MCP Client
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from utils.logger import get_logger
import os

# Get logger for router module
logger = get_logger(__name__)

# Global agent instance (will be set by main.py)
bedrock_agent = None


class PromptRequest(BaseModel):
    """Request model for prompt endpoint"""
    prompt: str
    temperature: float = 0.7
    max_tokens: int = 4096
    top_p: float = 0.9


class PromptResponse(BaseModel):
    """Response model for prompt endpoint"""
    response: str
    success: bool
    message: str = ""


# Create router
router = APIRouter()


def set_bedrock_agent(agent):
    """Set the global bedrock agent instance"""
    global bedrock_agent
    bedrock_agent = agent


@router.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "Echo MCP Client API is running",
        "status": "healthy",
        "model": "amazon.nova-pro-v1:0"
    }


@router.get("/health")
async def health_check():
    """Detailed health check endpoint"""
    global bedrock_agent
    
    if bedrock_agent is None:
        raise HTTPException(status_code=503, detail="Bedrock agent not initialized")
    
    try:
        # Quick connection test
        is_healthy = bedrock_agent.test_connection()
        
        return {
            "status": "healthy" if is_healthy else "unhealthy",
            "bedrock_connection": is_healthy,
            "model": "amazon.nova-pro-v1:0",
            "region": os.getenv('AWS_DEFAULT_REGION', 'us-east-1')
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail=f"Health check failed: {str(e)}")


@router.post("/prompt", response_model=PromptResponse)
async def process_prompt(request: PromptRequest):
    """
    Process a prompt using Amazon Nova Pro
    
    Args:
        request: PromptRequest containing the prompt and optional parameters
        
    Returns:
        PromptResponse with the model's response
    """
    global bedrock_agent
    
    if bedrock_agent is None:
        logger.error("Bedrock agent not initialized")
        raise HTTPException(status_code=503, detail="Bedrock agent not initialized")
    
    logger.info(f"Processing prompt: {request.prompt[:100]}...")
    
    try:
        # Invoke the model with optional parameters
        response = bedrock_agent.invoke(
            request.prompt,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            top_p=request.top_p
        )
        
        logger.info("Successfully processed prompt")
        
        return PromptResponse(
            response=response,
            success=True,
            message="Prompt processed successfully"
        )
        
    except Exception as e:
        logger.error(f"Error processing prompt: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing prompt: {str(e)}"
        )


@router.post("/stream")
async def stream_prompt(request: PromptRequest):
    """
    Stream a response from Amazon Nova Pro
    
    Args:
        request: PromptRequest containing the prompt and optional parameters
        
    Returns:
        Streaming response
    """
    global bedrock_agent
    
    if bedrock_agent is None:
        logger.error("Bedrock agent not initialized")
        raise HTTPException(status_code=503, detail="Bedrock agent not initialized")
    
    logger.info(f"Streaming prompt: {request.prompt[:100]}...")
    
    try:
        from fastapi.responses import StreamingResponse
        import json
        
        def generate_stream():
            try:
                for chunk in bedrock_agent.stream(
                    request.prompt,
                    temperature=request.temperature,
                    max_tokens=request.max_tokens,
                    top_p=request.top_p
                ):
                    if chunk:  # Only yield non-empty chunks
                        yield f"data: {json.dumps({'chunk': chunk})}\n\n"
                
                # Send completion signal
                yield f"data: {json.dumps({'done': True})}\n\n"
                
            except Exception as e:
                logger.error(f"Error in stream generation: {e}")
                yield f"data: {json.dumps({'error': str(e)})}\n\n"
        
        return StreamingResponse(
            generate_stream(),
            media_type="text/plain",
            headers={"Cache-Control": "no-cache"}
        )
        
    except Exception as e:
        logger.error(f"Error setting up stream: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error setting up stream: {str(e)}"
        )