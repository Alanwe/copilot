"""
Tests for the word_count component.
"""
from components.word_count.src.component import predict

def test_predict_with_dict():
    """Test the predict function with a dictionary input."""
    result = predict({"text": "This is a test sentence."})
    
    assert result["word_count"] == 5
    assert result["character_count"] == 24
    assert result["average_word_length"] == 4.0
    assert result["length_distribution"] == {4: 2, 2: 1, 1: 1, 9: 1}

def test_predict_with_string():
    """Test the predict function with a string input."""
    result = predict("Hello world")
    
    assert result["word_count"] == 2
    assert result["character_count"] == 11
    assert result["average_word_length"] == 5.0
    assert result["length_distribution"] == {5: 2}

def test_predict_with_batch():
    """Test the predict function with batch input."""
    batch_input = [
        {"text": "First test."},
        {"text": "Second longer test."}
    ]
    
    results = predict(batch_input)
    
    assert len(results) == 2
    assert results[0]["word_count"] == 2
    assert results[1]["word_count"] == 3

def test_predict_with_empty_string():
    """Test the predict function with an empty string."""
    result = predict("")
    
    assert result["word_count"] == 0
    assert result["character_count"] == 0
    assert result["average_word_length"] == 0
    assert result["length_distribution"] == {}

def test_predict_with_special_characters():
    """Test the predict function with text containing special characters."""
    result = predict({"text": "Hello, world! This is a test."})
    
    assert result["word_count"] == 6
    assert "character_count" in result
    assert "average_word_length" in result
    assert "length_distribution" in result
