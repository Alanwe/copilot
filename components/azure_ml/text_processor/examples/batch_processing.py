"""
Batch processing example for the Text Processor component.
"""

import os
import sys
import json

# Add parent directory to path to import from src
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.component import TextProcessingComponent


def main():
    """Example of batch processing with Text Processing Component."""
    print("Text Processor Component - Batch Processing Example")
    
    # Create component
    component = TextProcessingComponent({
        "min_length": 4,
        "max_length": 12
    })
    
    # Create batch of texts
    batch = [
        {
            "text": "This is the first sample text in the batch.",
            "id": "text-001"
        },
        {
            "text": "The second text has some longer words like extraordinary and incomprehensible.",
            "id": "text-002"
        },
        {
            "text": "Short text.",
            "id": "text-003"
        },
        {
            "text": "This final example demonstrates batch processing capabilities of our component.",
            "id": "text-004"
        }
    ]
    
    # Process batch
    result = component.run({"batch": batch})
    
    # Print result summary
    print("\nBatch processing results:")
    print(f"Total items processed: {len(result['results'])}")
    
    # Print details for each processed item
    for i, item_result in enumerate(result['results']):
        original_id = batch[i].get("id", f"item-{i}")
        word_count = item_result.get("word_count", 0)
        filtered_count = item_result.get("filtered_word_count", 0)
        
        print(f"\nItem {i+1} (ID: {original_id}):")
        print(f"  Total words: {word_count}")
        print(f"  Filtered words: {filtered_count}")
        print(f"  Filtered text: {item_result.get('filtered_text', '')}")


if __name__ == "__main__":
    main()