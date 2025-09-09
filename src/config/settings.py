"""
Echo MCP Client - Configuration Settings
"""
import os
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Client application settings."""

    # Server Configuration
    server_host: str = os.getenv("SERVER_HOST", "https://api.echo-mcp-server.qkiu.tech")
    server_api_prefix: str = ""

    # Authentication
    jwt_token: Optional[str] = os.getenv("JWT_TOKEN")
    user_id: Optional[int] = None

    # Agent Configuration
    agent_name: str = os.getenv("AGENT_NAME", "Echo Assistant")
    agent_description: str = os.getenv("AGENT_DESCRIPTION", "Your personal AI assistant for service management")

    # MCP Configuration
    mcp_server_url: str = os.getenv("MCP_SERVER_URL", "https://api.echo-mcp-server.qkiu.tech/mcp")
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")

    # Service Configuration
    max_concurrent_requests: int = int(os.getenv("MAX_CONCURRENT_REQUESTS", "5"))
    request_timeout: int = int(os.getenv("REQUEST_TIMEOUT", "30"))
    retry_attempts: int = int(os.getenv("RETRY_ATTEMPTS", "3"))

    # Logging
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    log_file: Optional[str] = os.getenv("LOG_FILE")

    # AWS Configuration (for Bedrock)
    bedrock_region: str = os.getenv("BEDROCK_REGION", "us-east-1")

    # Development Configuration
    development_mode: bool = os.getenv("DEVELOPMENT_MODE", "false").lower() == "true"
    auto_generate_test_data: bool = os.getenv("AUTO_GENERATE_TEST_DATA", "false").lower() == "true"
    verbose_logging: bool = os.getenv("VERBOSE_LOGGING", "false").lower() == "true"

    # Legacy compatibility
    api_base_url: str = server_host  # For backward compatibility

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()
