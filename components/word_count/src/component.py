"""
Simple Word Count Component for Azure Components Foundry.
Uses the unified architecture pattern with the dispatcher.
"""

import logging
from typing import Dict, Any, Union, List

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def predict(input_data: Union[Dict[str, Any], List[Dict[str, Any]], str]) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
    """
    Count words in the provided text.
    
    Args:
        input_data: Can be:
            - A dictionary with a "text" key
            - A list of dictionaries for batch processing
            - A raw string
            
    Returns:
        - Dictionary with word count results, or
        - List of dictionaries for batch processing results
    """
    logger.info(f"Processing input of type {type(input_data)}")
    
    # Handle batch processing
    if isinstance(input_data, list):
        logger.info(f"Processing batch of {len(input_data)} items")
        results = []
        for item in input_data:
            text = item.get("text", "") if isinstance(item, dict) else str(item)
            results.append(process_single_text(text))
        return results
    
    # Handle single item (dict or string)
    elif isinstance(input_data, dict):
        text = input_data.get("text", "")
        return process_single_text(text)
    
    # Handle raw string input
    else:
        text = str(input_data)
        return process_single_text(text)
    
def process_single_text(text: str) -> Dict[str, Any]:
    """Count words in a single text input."""
    # Split text into words
    words = text.split()
    
    # Count words by length
    length_distribution = {}
    for word in words:
        word_len = len(word)
        if word_len in length_distribution:
            length_distribution[word_len] += 1
        else:
            length_distribution[word_len] = 1
    
    return {
        "text": text,
        "word_count": len(words),
        "character_count": len(text),
        "average_word_length": sum(len(w) for w in words) / max(len(words), 1),
        "length_distribution": length_distribution
    }
