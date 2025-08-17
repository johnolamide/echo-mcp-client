from agent import create_bedrock_agent
from utils.logger import get_logger
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get logger for main module
logger = get_logger(__name__)


def main():
    logger.info("Starting Echo MCP Client with Amazon Bedrock Nova Pro")
    
    # Debug: Check if environment variables are loaded
    aws_access_key = os.getenv('AWS_ACCESS_KEY_ID')
    aws_region = os.getenv('AWS_DEFAULT_REGION')
    
    if aws_access_key:
        logger.info(f"AWS credentials loaded successfully (Access Key: {aws_access_key[:8]}...)")
        logger.info(f"AWS region: {aws_region}")
    else:
        logger.error("AWS credentials not found in environment variables")
        logger.error("Make sure your .env file exists and contains AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY")
        return
    
    # Create Bedrock agent
    try:
        logger.debug("Initializing Bedrock agent...")
        agent = create_bedrock_agent()
        logger.info("Bedrock agent initialized successfully")
        
        # Test connection
        logger.debug("Testing Bedrock connection...")
        if agent.test_connection():
            logger.info("Connection to Bedrock successful")
            
            # Example usage
            prompt = "Explain what Amazon Nova Pro is in one sentence."
            logger.info(f"Sending prompt: {prompt}")
            response = agent.invoke(prompt)
            logger.info("Received response from Nova Pro")
            print(f"\nPrompt: {prompt}")
            print(f"Response: {response}")
            
        else:
            logger.error("Connection to Bedrock failed")
            
    except Exception as e:
        logger.error(f"Error initializing Bedrock agent: {e}")
        print(f"✗ Error initializing Bedrock agent: {e}")
        print("\nMake sure you have:")
        print("1. AWS credentials configured (AWS CLI, env vars, or IAM role)")
        print("2. Access to Amazon Bedrock in your AWS account")
        print("3. Nova Pro model enabled in Bedrock console")


if __name__ == "__main__":
    main()
