"""
Unit tests for the Text Processor component.
"""

import os
import sys
import unittest

# Add parent directory to path to import from src
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.component import TextProcessingComponent


class TextProcessorTests(unittest.TestCase):
    """Tests for the Text Processor component."""
    
    def setUp(self):
        """Set up test cases."""
        self.component = TextProcessingComponent()
        self.custom_component = TextProcessingComponent({
            "min_length": 5,
            "max_length": 8
        })
        
        self.test_text = "This is a test sentence with words of varying lengths."
        
    def test_initialization(self):
        """Test component initialization."""
        self.assertEqual(self.component.min_length, 3)
        self.assertEqual(self.component.max_length, 100)
        self.assertEqual(self.custom_component.min_length, 5)
        self.assertEqual(self.custom_component.max_length, 8)
    
    def test_single_text_processing(self):
        """Test processing a single text input."""
        result = self.component.run({"text": self.test_text})
        
        # Verify result structure
        self.assertIn("result", result)
        self.assertIn("original_text", result["result"])
        self.assertIn("word_count", result["result"])
        self.assertIn("filtered_word_count", result["result"])
        self.assertIn("filtered_text", result["result"])
        
        # Verify content
        self.assertEqual(result["result"]["original_text"], self.test_text)
        self.assertEqual(result["result"]["word_count"], 10)
    
    def test_word_filtering(self):
        """Test word filtering based on length."""
        # Test with default settings (min=3, max=100)
        result = self.component.run({"text": self.test_text})
        words = result["result"]["filtered_text"].split()
        for word in words:
            # Check that each word meets length criteria
            self.assertTrue(len(word) >= 3)
            self.assertTrue(len(word) <= 100)
        
        # Test with custom settings (min=5, max=8)
        result = self.custom_component.run({"text": self.test_text})
        words = result["result"]["filtered_text"].split()
        for word in words:
            # Check that each word meets custom length criteria
            self.assertTrue(len(word) >= 5)
            self.assertTrue(len(word) <= 8)
    
    def test_batch_processing(self):
        """Test batch processing of multiple texts."""
        batch = [
            {"text": "Text one"},
            {"text": "Text number two"},
            {"text": "Third text example"}
        ]
        
        result = self.component.run({"batch": batch})
        
        # Verify result structure
        self.assertIn("results", result)
        self.assertEqual(len(result["results"]), 3)
        
        # Verify each item was processed
        for i, item_result in enumerate(result["results"]):
            self.assertIn("original_text", item_result)
            self.assertEqual(item_result["original_text"], batch[i]["text"])
    
    def test_empty_input(self):
        """Test handling of empty input."""
        # Empty text
        result = self.component.run({"text": ""})
        self.assertEqual(result["result"]["word_count"], 0)
        self.assertEqual(result["result"]["filtered_word_count"], 0)
        
        # Empty batch
        result = self.component.run({"batch": []})
        self.assertEqual(len(result["results"]), 0)


if __name__ == "__main__":
    unittest.main()