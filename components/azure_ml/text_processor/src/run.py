"""
Entry point for Azure ML component.
"""

import os
import json
import logging
from .component import TextProcessingComponent

# Global component instance
component = None


def init():
    """Initialize the component for Azure ML."""
    global component
    import os
    
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    logging.info("Initializing Text Processing component")
    
    # Load configuration from environment variable or file
    config = {}
    config_path = os.environ.get("COMPONENT_CONFIG", "config.json")
    if os.path.exists(config_path):
        with open(config_path) as f:
            config = json.load(f)
    
    # Create component instance
    component = TextProcessingComponent(config)
    logging.info("Component initialized successfully")


def run(mini_batch):
    """
    Run method called by Azure ML.
    
    Args:
        mini_batch: A list of paths to files
        
    Returns:
        List of processed results
    """
    global component
    
    if not component:
        init()
    
    results = []
    
    # Process each file in the mini-batch
    for file_path in mini_batch:
        logging.info(f"Processing file: {file_path}")
        
        try:
            # Read input file
            with open(file_path, "r") as f:
                text = f.read()
            
            # Process text
            result = component.run({"text": text})
            results.append(result)
            
        except Exception as e:
            logging.error(f"Error processing file {file_path}: {str(e)}")
            results.append({"error": str(e), "file": file_path})
    
    return results