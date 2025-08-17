"""
Centralized logging configuration for echo-mcp-client
"""

import logging
import sys
from pathlib import Path
from typing import Optional
import os


class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors for different log levels"""
    
    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
        'RESET': '\033[0m'      # Reset
    }
    
    def format(self, record):
        # Add color to levelname
        if record.levelname in self.COLORS:
            record.levelname = (
                f"{self.COLORS[record.levelname]}{record.levelname}"
                f"{self.COLORS['RESET']}"
            )
        return super().format(record)


def setup_logger(
    name: str = "echo-mcp-client",
    level: str = "INFO",
    log_file: Optional[str] = None,
    console_output: bool = True,
    colored_output: bool = True
) -> logging.Logger:
    """
    Set up a logger with console and optional file output
    
    Args:
        name: Logger name
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional file path for log output
        console_output: Whether to output to console
        colored_output: Whether to use colored console output
        
    Returns:
        Configured logger instance
    """
    
    # Create logger
    logger = logging.getLogger(name)
    
    # Clear any existing handlers to avoid duplicates
    logger.handlers.clear()
    
    # Set level
    log_level = getattr(logging, level.upper(), logging.INFO)
    logger.setLevel(log_level)
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        fmt='%(asctime)s | %(name)s | %(levelname)s | %(filename)s:%(lineno)d | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    simple_formatter = logging.Formatter(
        fmt='%(levelname)s | %(name)s | %(message)s'
    )
    
    # Console handler
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        
        if colored_output and sys.stdout.isatty():
            # Use colored formatter for terminal output
            colored_formatter = ColoredFormatter(
                fmt='%(levelname)s | %(name)s | %(message)s'
            )
            console_handler.setFormatter(colored_formatter)
        else:
            console_handler.setFormatter(simple_formatter)
            
        logger.addHandler(console_handler)
    
    # File handler
    if log_file:
        # Create log directory if it doesn't exist
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(detailed_formatter)
        logger.addHandler(file_handler)
    
    return logger


def get_logger(name: str = None) -> logging.Logger:
    """
    Get a logger instance with the project's configuration
    
    Args:
        name: Logger name (defaults to calling module name)
        
    Returns:
        Logger instance
    """
    if name is None:
        # Get the calling module name
        import inspect
        frame = inspect.currentframe().f_back
        name = frame.f_globals.get('__name__', 'echo-mcp-client')
    
    return logging.getLogger(name)


# Default project logger configuration
def configure_project_logging():
    """Configure logging for the entire project"""
    
    # Get log level from environment variable
    log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
    
    # Get log file from environment variable
    log_file = os.getenv('LOG_FILE')
    
    # Check if we're in development mode
    is_dev = os.getenv('ENVIRONMENT', 'development').lower() == 'development'
    
    # Set up root logger for the project
    setup_logger(
        name="echo-mcp-client",
        level=log_level,
        log_file=log_file,
        console_output=True,
        colored_output=is_dev
    )
    
    # Configure third-party loggers to be less verbose
    logging.getLogger('boto3').setLevel(logging.WARNING)
    logging.getLogger('botocore').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('langchain').setLevel(logging.INFO)


# Initialize project logging when module is imported
configure_project_logging()

# Export the main logger for the project
project_logger = get_logger("echo-mcp-client")