"""
Test for specific missing coverage in Function Adapter.
"""
import sys
import os
import json
import logging
from unittest.mock import patch, Mock, MagicMock

# Configure logging
logging.basicConfig(level=logging.INFO)


def setup_module():
    """Set up mocks before importing the module."""
    # Mock azure.functions
    sys.modules['azure.functions'] = Mock()
    
    # Create mock HttpResponse class that has the appropriate attributes
    class MockHttpResponse:
        def __init__(self, body=None, status_code=200, mimetype="application/json"):
            self.body = body
            self.status_code = status_code
            self.mimetype = mimetype
    
    # Create mock HttpRequest class
    class MockHttpRequest:
        def __init__(self, body=None):
            self.body = body
            
        def get_json(self):
            return None  # This is the key change - get_json returns None but doesn't raise ValueError
    
    # Set up the mocks
    sys.modules['azure.functions'].HttpRequest = MockHttpRequest
    sys.modules['azure.functions'].HttpResponse = MockHttpResponse
    
    # Mock the dispatcher functions
    sys.modules['runtime.dispatcher'] = Mock()
    sys.modules['runtime.dispatcher'].predict = Mock(return_value={"result": "test_result"})


def teardown_module():
    """Clean up mocks after tests."""
    if 'runtime.function_adapter' in sys.modules:
        del sys.modules['runtime.function_adapter']
    if 'azure.functions' in sys.modules:
        del sys.modules['azure.functions']


def test_function_adapter_main_with_none_json():
    """Test the main method with get_json returning None."""
    # Import locally to get a fresh instance
    if 'runtime.function_adapter' in sys.modules:
        del sys.modules['runtime.function_adapter']
    
    # Set up mocks
    setup_module()
    
    # Import the module
    from runtime.function_adapter import AzureFunctionAdapter
    
    # Create a mock request that returns None for get_json
    mock_req = sys.modules['azure.functions'].HttpRequest(body=None)
    
    # Mock the logger
    logger_mock = MagicMock()
    
    with patch('runtime.function_adapter.logger', logger_mock):
        # Call the main method
        response = AzureFunctionAdapter.main(mock_req)
        
        # Verify predict was called with empty dict
        sys.modules['runtime.dispatcher'].predict.assert_called_with({})
        
        # Verify response
        assert response.status_code == 200
