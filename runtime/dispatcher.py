"""
Runtime dispatcher for Azure Components Foundry.
Implements the environment variable-based component selection pattern.
"""
import importlib
import os
import logging
from typing import Union, Dict, List, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get component handler from environment variable
_target = os.getenv("HANDLER", "components.word_count.src.component:predict")
logger.info(f"Using handler: {_target}")

# Initialize predict_fn as None for lazy loading
predict_fn = None
_mod = None
_fn = None

def _load_handler():
    """Lazy load the handler function."""
    global predict_fn, _mod, _fn
    if predict_fn is None:
        try:
            _mod, _fn = _target.split(":")
            predict_fn = getattr(importlib.import_module(_mod), _fn)
            logger.info(f"Successfully loaded function: {_fn} from module: {_mod}")
        except Exception as e:
            logger.error(f"Failed to load handler {_target}: {str(e)}")
            raise
    return predict_fn


def predict(payload: Union[str, dict, list]) -> Union[dict, list]:
    """
    Universal predict function that handles single items or batches.
    
    Args:
        payload: Input data (string, dict, or list of items)
        
    Returns:
        Prediction result (dict for single items, list for batches)
    """
    try:
        # Lazy load the handler function
        handler_fn = _load_handler()
        
        if isinstance(payload, list):
            # Batch processing
            logger.info(f"Processing batch of {len(payload)} items")
            return [handler_fn(item) for item in payload]
        else:
            # Single item processing
            logger.info("Processing single item")
            return handler_fn(payload)
    except Exception as e:
        logger.error(f"Error in predict function: {str(e)}")
        raise


def health_check() -> Dict[str, Any]:
    """
    Health check endpoint to verify the dispatcher is working.
    
    Returns:
        Dictionary with health status and component information
    """
    # Try to load handler to verify it's available
    try:
        _load_handler()
        status = "healthy"
    except Exception:
        status = "unhealthy"
    
    # Get module and function names from target
    try:
        mod, fn = _target.split(":")
    except ValueError:
        mod, fn = "unknown", "unknown"
    
    return {
        "status": status,
        "handler": _target,
        "module": mod,
        "function": fn,
        "version": "1.0.0"
    }


if __name__ == "__main__":
    # Test the dispatcher
    test_payload = {"text": "Hello, world!"}
    result = predict(test_payload)
    print(f"Test result: {result}")
