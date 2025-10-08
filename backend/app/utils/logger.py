import logging
import sys
from datetime import datetime

def setup_logging():
    """Setup enhanced logging configuration"""
    
    # Create custom formatter
    class CustomFormatter(logging.Formatter):
        def format(self, record):
            record.timestamp = datetime.utcnow().isoformat()
            return super().format(record)
    
    # Configure root logger
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    # Remove existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_formatter = CustomFormatter(
        '%(timestamp)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # File handler for errors
    file_handler = logging.FileHandler('app.log')
    file_formatter = CustomFormatter(
        '%(timestamp)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
    )
    file_handler.setFormatter(file_formatter)
    file_handler.setLevel(logging.ERROR)
    logger.addHandler(file_handler)
    
    return logger
