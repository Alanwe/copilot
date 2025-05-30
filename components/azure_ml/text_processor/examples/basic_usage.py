"""
Basic usage example for the Text Processor component.
"""

import os
import sys
import json

# Add parent directory to path to import from src
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.component import TextProcessingComponent


def main():
    """Example usage of the Text Processing Component."""
    print("Text Processor Component - Basic Usage Example")
    
    # Create component with default configuration
    component = TextProcessingComponent()
    
    # Process a single text
    text = "This is an example of the text processor component in action. It counts words and filters them by length."
    result = component.run({"text": text})
    
    # Print result
    print("\nSingle text processing result:")
    print(json.dumps(result, indent=2))
    
    # Create component with custom configuration
    custom_component = TextProcessingComponent({
        "min_length": 5,
        "max_length": 8
    })
    
    # Process the same text with custom settings
    custom_result = custom_component.run({"text": text})
    
    # Print custom result
    print("\nCustom configuration result (min_length=5, max_length=8):")
    print(json.dumps(custom_result, indent=2))


if __name__ == "__main__":
    main()