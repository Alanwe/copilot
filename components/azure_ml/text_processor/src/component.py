"""
Text Processing Component for Azure Components Foundry.
"""

from typing import Dict, Any
import logging
from common.base import BaseComponent


class TextProcessingComponent(BaseComponent):
    """Component that processes text data."""
    
    def initialize(self):
        """Set up resources needed by the component."""
        logging.info("Initializing TextProcessingComponent")
        self.min_length = self.config.get("min_length", 3)
        self.max_length = self.config.get("max_length", 100)
        logging.info(f"Config: min_length={self.min_length}, max_length={self.max_length}")
    
    def run(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Process text inputs."""
        logging.info("Running TextProcessingComponent")
        
        if "batch" in inputs and isinstance(inputs["batch"], list):
            # Batch processing mode
            logging.info(f"Processing batch of {len(inputs['batch'])} items")
            results = []
            for item in inputs["batch"]:
                text = item.get("text", "")
                results.append(self._process_text(text))
            return {"results": results}
        else:
            # Single item processing mode
            logging.info("Processing single text item")
            text = inputs.get("text", "")
            return {"result": self._process_text(text)}
    
    def _process_text(self, text: str) -> Dict[str, Any]:
        """Process a single text input."""
        # Count words
        words = text.split()
        word_count = len(words)
        
        # Filter words by length
        filtered_words = [w for w in words if self.min_length <= len(w) <= self.max_length]
        
        return {
            "original_text": text,
            "word_count": word_count,
            "filtered_word_count": len(filtered_words),
            "filtered_text": " ".join(filtered_words)
        }
    
    def cleanup(self):
        """Clean up resources."""
        logging.info("Cleaning up TextProcessingComponent")
        # Release any resources if needed