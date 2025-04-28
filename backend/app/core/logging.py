import logging
import sys
from app.core.config import get_app_config

config = get_app_config()

# Configure logging
def setup_logging():
    log_level = getattr(logging, config.server.log_level.upper(), logging.INFO)
    
    logger = logging.getLogger("vpn_service")
    logger.setLevel(log_level)
    
    # Create console handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(log_level)
    
    # Create formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    
    # Add handler to logger
    logger.addHandler(handler)
    
    return logger

logger = setup_logging()
