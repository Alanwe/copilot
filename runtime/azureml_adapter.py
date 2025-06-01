"""
Azure ML adapter for the unified runtime system.
Handles both online and batch endpoints.
"""
import logging
from typing import Any, Dict, List
from runtime.dispatcher import predict

logger = logging.getLogger(__name__)


class AzureMLAdapter:
    """Adapter for Azure ML online and batch endpoints."""
    
    @staticmethod
    def init():
        """Initialize Azure ML environment."""
        logger.info("Initializing Azure ML adapter")
        # Any Azure ML specific initialization goes here
        
    @staticmethod
    def run(data: Any) -> Any:
        """
        Run component in Azure ML context.
        
        Args:
            data: Input data from Azure ML (dict for online, list for batch)
            
        Returns:
            Processed results in Azure ML compatible format
        """
        logger.info("Processing Azure ML request")
        
        try:
            # Handle both online (dict/single item) and batch (list) scenarios
            if isinstance(data, list):
                logger.info(f"Processing batch request with {len(data)} items")
                return predict(data)
            else:
                logger.info("Processing online request")
                return predict(data)
                
        except Exception as e:
            logger.error(f"Error in Azure ML adapter: {str(e)}")
            return {"error": str(e), "status": "failed"}


# Azure ML endpoint functions (required by AML runtime)
def init():
    """Azure ML initialization function."""
    AzureMLAdapter.init()


def run(data):
    """Azure ML run function."""
    return AzureMLAdapter.run(data)
