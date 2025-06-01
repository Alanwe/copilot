"""
Test suite for dispatcher.py module to achieve 100% test coverage.
"""
import os
import sys
import importlib
import pytest
from unittest.mock import patch, MagicMock

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

#-----------------------------------------------------------------------------
# Tests for runtime/dispatcher.py
#-----------------------------------------------------------------------------
@pytest.mark.parametrize("target_module", ["components.word_count.src.component:predict", "module.does:not_exist"])
def test_load_handler(target_module):
    """Test the _load_handler function."""
    # Mock environment variables
    with patch.dict(os.environ, {"HANDLER": target_module}):
        # Import so environment gets read
        from runtime import dispatcher
        importlib.reload(dispatcher)
        
        # Reset the predict_fn
        dispatcher.predict_fn = None
        
        # Mock the importlib.import_module
        mock_module = MagicMock()
        mock_module.predict = MagicMock(return_value={"result": "test"})
        
        if "not_exist" in target_module:
            # Test the exception path
            with patch('importlib.import_module', side_effect=ImportError("Module not found")):
                with pytest.raises(ImportError):
                    dispatcher._load_handler()
        else:
            # Test the success path
            with patch('importlib.import_module', return_value=mock_module):
                handler = dispatcher._load_handler()
                
                # Check that predict_fn is set
                assert dispatcher.predict_fn == mock_module.predict
                assert handler == mock_module.predict

def test_predict_single_item():
    """Test the predict function with a single item."""
    # Import module
    from runtime import dispatcher
    
    # Mock _load_handler
    mock_handler = MagicMock(return_value={"result": "processed"})
    
    # Test with a single item
    with patch.object(dispatcher, '_load_handler', return_value=mock_handler):
        result = dispatcher.predict({"text": "test"})
        
        # Verify handler was called correctly
        mock_handler.assert_called_once_with({"text": "test"})
        assert result == {"result": "processed"}

def test_predict_batch():
    """Test the predict function with a batch of items."""
    # Import module
    from runtime import dispatcher
    
    # Mock _load_handler
    mock_handler = MagicMock(side_effect=lambda x: {"result": f"processed_{x['id']}"})
    
    # Test with a batch of items
    with patch.object(dispatcher, '_load_handler', return_value=mock_handler):
        items = [{"id": 1}, {"id": 2}, {"id": 3}]
        result = dispatcher.predict(items)
        
        # Verify handler was called for each item
        assert mock_handler.call_count == 3
        assert len(result) == 3
        assert result == [
            {"result": "processed_1"},
            {"result": "processed_2"},
            {"result": "processed_3"}
        ]

def test_predict_exception():
    """Test the predict function when an exception occurs."""
    # Import module
    from runtime import dispatcher
    
    # Mock _load_handler to raise exception
    with patch.object(dispatcher, '_load_handler', side_effect=ValueError("Test error")):
        with pytest.raises(ValueError, match="Test error"):
            dispatcher.predict({"text": "test"})

def test_health_check_healthy():
    """Test the health_check function when handler can be loaded."""
    # Import module
    from runtime import dispatcher
    
    # Mock _load_handler
    mock_handler = MagicMock()
    
    # Test health check with working handler
    with patch.object(dispatcher, '_load_handler', return_value=mock_handler):
        with patch.dict(os.environ, {"HANDLER": "module:function"}):
            result = dispatcher.health_check()
            
            # Verify health status
            assert result["status"] == "healthy"
            assert result["handler"] == "module:function"
            assert result["module"] == "module"
            assert result["function"] == "function"
            assert result["version"] == "1.0.0"

def test_health_check_unhealthy():
    """Test the health_check function when handler cannot be loaded."""
    # Import module
    from runtime import dispatcher
    
    # Mock _load_handler to raise exception
    with patch.object(dispatcher, '_load_handler', side_effect=ImportError("Module not found")):
        with patch.dict(os.environ, {"HANDLER": "bad_module:function"}):
            result = dispatcher.health_check()
            
            # Verify unhealthy status
            assert result["status"] == "unhealthy"
            assert result["handler"] == "bad_module:function"
            assert result["module"] == "bad_module"
            assert result["function"] == "function"
            assert result["version"] == "1.0.0"

def test_health_check_invalid_handler():
    """Test the health_check function with invalid handler format."""
    # Import module
    from runtime import dispatcher
    
    # Test with invalid handler format
    with patch.dict(os.environ, {"HANDLER": "invalid_handler_format"}):
        result = dispatcher.health_check()
        
        # Verify handler info
        assert result["status"] == "unhealthy"
        assert result["handler"] == "invalid_handler_format"
        assert result["module"] == "unknown"
        assert result["function"] == "unknown"

def test_dispatcher_main():
    """Test the __main__ block in dispatcher.py."""
    # Import module
    from runtime import dispatcher
    
    # Save the original __name__
    original_name = dispatcher.__name__
    
    try:
        # Mock print function
        with patch('builtins.print') as mock_print:
            # Mock predict function
            with patch.object(dispatcher, 'predict', return_value={"word_count": 2}):
                # Execute the __main__ block
                dispatcher.__name__ = "__main__"
                
                # Re-execute the module code
                exec(open(dispatcher.__file__).read())
                
                # Verify print was called with test result
                mock_print.assert_called_with("Test result: {'word_count': 2}")
    finally:
        # Restore original name
        dispatcher.__name__ = original_name

if __name__ == "__main__":
    # Run the tests manually
    pytest.main(["-v", "--cov=runtime.dispatcher", "--cov-report=term-missing", __file__])
