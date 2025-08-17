import boto3
from langchain_aws import ChatBedrock
from typing import Optional, Dict, Any
import os
from utils.logger import get_logger

# Get logger for this module
logger = get_logger(__name__)


class BedrockAgent:
    """Agent for interacting with Amazon Bedrock Nova Pro LLM"""
    
    def __init__(
        self,
        region_name: str = "us-east-1",
        model_id: str = "amazon.nova-pro-v1:0",
        aws_access_key_id: Optional[str] = None,
        aws_secret_access_key: Optional[str] = None,
        aws_session_token: Optional[str] = None,
        **model_kwargs
    ):
        """
        Initialize Bedrock agent with Nova Pro model
        
        Args:
            region_name: AWS region for Bedrock service
            model_id: Bedrock model ID for Nova Pro
            aws_access_key_id: AWS access key (optional, can use env vars)
            aws_secret_access_key: AWS secret key (optional, can use env vars)
            aws_session_token: AWS session token (optional, for temporary credentials)
            **model_kwargs: Additional model parameters
        """
        self.region_name = region_name
        self.model_id = model_id
        
        # Set up AWS credentials
        self.credentials = {}
        if aws_access_key_id:
            self.credentials['aws_access_key_id'] = aws_access_key_id
        if aws_secret_access_key:
            self.credentials['aws_secret_access_key'] = aws_secret_access_key
        if aws_session_token:
            self.credentials['aws_session_token'] = aws_session_token
            
        # Default model parameters for Nova Pro
        self.model_kwargs = {
            "temperature": 0.7,
            "max_tokens": 4096,
            "top_p": 0.9,
            **model_kwargs
        }
        
        self._llm = None
        self._bedrock_client = None
    
    @property
    def bedrock_client(self):
        """Lazy initialization of Bedrock client"""
        if self._bedrock_client is None:
            try:
                self._bedrock_client = boto3.client(
                    'bedrock-runtime',
                    region_name=self.region_name,
                    **self.credentials
                )
                logger.info(f"Connected to Bedrock in region: {self.region_name}")
            except Exception as e:
                logger.error(f"Failed to create Bedrock client: {e}")
                raise
        return self._bedrock_client
    
    @property
    def llm(self):
        """Lazy initialization of LangChain Bedrock Chat Model"""
        if self._llm is None:
            try:
                self._llm = ChatBedrock(
                    client=self.bedrock_client,
                    model_id=self.model_id,
                    model_kwargs=self.model_kwargs
                )
                logger.info(f"Initialized Nova Pro Chat Model: {self.model_id}")
            except Exception as e:
                logger.error(f"Failed to initialize LLM: {e}")
                raise
        return self._llm
    
    def invoke(self, prompt: str, **kwargs) -> str:
        """
        Invoke the Nova Pro model with a prompt
        
        Args:
            prompt: Input prompt for the model
            **kwargs: Additional parameters to override defaults
            
        Returns:
            Model response as string
        """
        try:
            # Update model kwargs if provided
            if kwargs:
                self.llm.model_kwargs.update(kwargs)
            
            # For chat models, we need to format as messages
            from langchain_core.messages import HumanMessage
            messages = [HumanMessage(content=prompt)]
            
            response = self.llm.invoke(messages)
            logger.info(f"Successfully invoked Nova Pro model")
            
            # Extract content from the response
            return response.content
            
        except Exception as e:
            logger.error(f"Error invoking model: {e}")
            raise
    
    def stream(self, prompt: str, **kwargs):
        """
        Stream response from Nova Pro model
        
        Args:
            prompt: Input prompt for the model
            **kwargs: Additional parameters to override defaults
            
        Yields:
            Streaming response chunks
        """
        try:
            # Update model kwargs if provided
            if kwargs:
                self.llm.model_kwargs.update(kwargs)
            
            # For chat models, we need to format as messages
            from langchain_core.messages import HumanMessage
            messages = [HumanMessage(content=prompt)]
                
            for chunk in self.llm.stream(messages):
                yield chunk.content if hasattr(chunk, 'content') else chunk
                
        except Exception as e:
            logger.error(f"Error streaming from model: {e}")
            raise
    
    def test_connection(self) -> bool:
        """
        Test connection to Bedrock and model availability
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            # Test with a simple prompt
            test_prompt = "Hello, this is a connection test."
            response = self.invoke(test_prompt)
            logger.info("Connection test successful")
            return True
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False


def create_bedrock_agent(**kwargs) -> BedrockAgent:
    """
    Factory function to create a Bedrock agent with environment variable support
    
    Args:
        **kwargs: Override parameters for BedrockAgent
        
    Returns:
        Configured BedrockAgent instance
    """
    # Get credentials from environment if not provided
    env_credentials = {
        'aws_access_key_id': os.getenv('AWS_ACCESS_KEY_ID'),
        'aws_secret_access_key': os.getenv('AWS_SECRET_ACCESS_KEY'),
        'aws_session_token': os.getenv('AWS_SESSION_TOKEN'),
        'region_name': os.getenv('AWS_DEFAULT_REGION', 'us-east-1')
    }
    
    # Remove None values
    env_credentials = {k: v for k, v in env_credentials.items() if v is not None}
    
    # Merge with provided kwargs (kwargs take precedence)
    config = {**env_credentials, **kwargs}
    
    return BedrockAgent(**config)