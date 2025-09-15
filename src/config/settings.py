"""
Echo MCP Client - Configuration Settings
"""
import os
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Client application settings."""

    # Server Configuration
    server_host: str = os.getenv("SERVER_HOST", "http://localhost:8000")
    server_api_prefix: str = ""
    
    # Agent API Port
    agent_port: int = int(os.getenv("AGENT_PORT", "8002"))

    # Authentication
    jwt_token: Optional[str] = os.getenv("JWT_TOKEN")
    user_id: Optional[int] = None

    # Agent Configuration
    agent_name: str = os.getenv("AGENT_NAME", "Echo Assistant")
    agent_description: str = os.getenv("AGENT_DESCRIPTION", "Your personal AI assistant for service management")

    # HTTP Configuration
    request_timeout: float = float(os.getenv("REQUEST_TIMEOUT", "30.0"))
    retry_attempts: int = int(os.getenv("RETRY_ATTEMPTS", "3"))

    # OpenAI Configuration (legacy)
    openai_api_key: Optional[str] = os.getenv("OPENAI_API_KEY")

    # AWS Configuration (for Bedrock)
    aws_access_key_id: Optional[str] = os.getenv("AWS_ACCESS_KEY_ID")
    aws_secret_access_key: Optional[str] = os.getenv("AWS_SECRET_ACCESS_KEY")
    aws_region: str = os.getenv("AWS_REGION", "us-east-1")
    bedrock_model_id: str = os.getenv("BEDROCK_MODEL_ID", "amazon.nova-pro-v1:0")

    # Development Configuration
    development_mode: bool = os.getenv("DEVELOPMENT_MODE", "false").lower() == "true"
    auto_generate_test_data: bool = os.getenv("AUTO_GENERATE_TEST_DATA", "false").lower() == "true"
    verbose_logging: bool = os.getenv("VERBOSE_LOGGING", "false").lower() == "true"

    # Logging Configuration
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    log_file: Optional[str] = os.getenv("LOG_FILE")

    # Legacy compatibility
    api_base_url: str = server_host  # For backward compatibility

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"  # Ignore extra environment variables


# Global settings instance
settings = Settings()
