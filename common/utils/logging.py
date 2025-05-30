"""
Logging utilities for Azure Components Foundry.
This module provides standardized logging configuration.
"""

import os
import logging
import json
from datetime import datetime


def configure_logging(component_name: str, level=logging.INFO, log_to_file=False, log_dir=None):
    """
    Configure logging for a component.
    
    Args:
        component_name: Name of the component (used in log formatting)
        level: Logging level (default: INFO)
        log_to_file: Whether to log to a file in addition to console
        log_dir: Directory for log files (default: ./logs)
    """
    # Create log formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Clear any existing handlers to avoid duplicate logs
    if root_logger.handlers:
        for handler in root_logger.handlers:
            root_logger.removeHandler(handler)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # File handler (if requested)
    if log_to_file:
        if not log_dir:
            log_dir = os.path.join(os.getcwd(), 'logs')
        
        os.makedirs(log_dir, exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        log_file = os.path.join(log_dir, f"{component_name}_{timestamp}.log")
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
        
    logging.info(f"Logging configured for component: {component_name}")


class StructuredLogFormatter(logging.Formatter):
    """Formatter for structured JSON logs"""
    
    def format(self, record):
        log_data = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "name": record.name,
            "message": record.getMessage(),
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # Add custom fields if present
        if hasattr(record, "custom_fields"):
            log_data.update(record.custom_fields)
            
        return json.dumps(log_data)


def configure_structured_logging(component_name: str, level=logging.INFO):
    """
    Configure structured JSON logging for a component.
    
    Args:
        component_name: Name of the component
        level: Logging level (default: INFO)
    """
    formatter = StructuredLogFormatter()
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Clear any existing handlers
    if root_logger.handlers:
        for handler in root_logger.handlers:
            root_logger.removeHandler(handler)
    
    # Console handler with structured formatter
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    root_logger.addHandler(handler)
    
    logging.info(f"Structured logging configured for component: {component_name}")


def log_with_context(logger, level, message, **context):
    """
    Log a message with additional context fields.
    
    Args:
        logger: Logger instance
        level: Log level (e.g., logging.INFO)
        message: Log message
        **context: Additional context fields to include in the log
    """
    if hasattr(logger, "makeRecord"):
        record = logger.makeRecord(
            logger.name, level, None, None, message, None, None
        )
        record.custom_fields = context
        logger.handle(record)
    else:
        # Fallback if custom record creation is not supported
        context_str = " ".join(f"{k}={v}" for k, v in context.items())
        logger.log(level, f"{message} {context_str}")