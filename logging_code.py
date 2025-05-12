"""
Logging configuration for JobZoeker application.

This module sets up the logging configuration for the entire application.
"""

import logging

def setup_logger(name=None):
    """
    Configure and return a logger instance.
    
    Args:
        name: Optional name for the logger (defaults to root logger if None)
        
    Returns:
        Configured logger instance
    """
    # Configure root logger if no name is provided
    if name is None:
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s",
            handlers=[logging.StreamHandler()]
        )
        return logging.getLogger()
    
    # Otherwise, return a named logger
    logger = logging.getLogger(name)
    
    # Only configure this logger if it hasn't been configured yet
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        
    return logger