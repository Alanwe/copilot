"""
Test coverage for Azure Functions adapter module.
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
            if self.body is None:
                return None
            return json.loads(self.body)
    
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


def test_function_adapter_initialization():
    """Test initialization of the Azure Function adapter."""
    # Import locally to get a fresh instance
    if 'runtime.function_adapter' in sys.modules:
        del sys.modules['runtime.function_adapter']
    
    # Set up mocks
    setup_module()
    
    # Import the module
    from runtime.function_adapter import AzureFunctionAdapter
    
    # Mock the logger
    logger_mock = MagicMock()
    
    with patch('runtime.function_adapter.logger', logger_mock):
        # Call the init method
        AzureFunctionAdapter.init()
        # Verify logger was called correctly
        logger_mock.info.assert_called_once_with("Initializing Azure Functions adapter")


def test_function_adapter_main_with_valid_json():
    """Test the main method with valid JSON input."""
    # Import locally to get a fresh instance
    if 'runtime.function_adapter' in sys.modules:
        del sys.modules['runtime.function_adapter']
    
    # Set up mocks
    setup_module()
    mock_predict = MagicMock(return_value={"result": "mocked_result"})
    sys.modules['runtime.dispatcher'].predict = mock_predict
    
    # Import the module
    from runtime.function_adapter import AzureFunctionAdapter
    
    # Create a mock request with JSON body
    mock_req = sys.modules['azure.functions'].HttpRequest(body='{"text": "test"}')
    
    # Mock the logger
    logger_mock = MagicMock()
    
    with patch('runtime.function_adapter.logger', logger_mock):
        # Call the main method
        response = AzureFunctionAdapter.main(mock_req)
        
        # Verify predict was called with the correct data
        mock_predict.assert_called_with({"text": "test"})
        
        # Verify response properties
        assert response.status_code == 200
        assert response.mimetype == "application/json"
        
        # Check the response body content
        expected_response = {"result": "mocked_result"}
        assert json.loads(response.body) == expected_response
        
        # Verify logging occurred
        logger_mock.info.assert_called_once_with("Processing Azure Functions request")


def test_function_adapter_main_with_invalid_json():
    """Test the main method with invalid JSON input."""
    # Import locally to get a fresh instance
    if 'runtime.function_adapter' in sys.modules:
        del sys.modules['runtime.function_adapter']
    
    # Set up mocks
    setup_module()
    
    # Import the module
    from runtime.function_adapter import AzureFunctionAdapter
    
    # Create a mock request that raises ValueError for get_json
    mock_req = sys.modules['azure.functions'].HttpRequest(body=None)
    mock_req.get_json = MagicMock(side_effect=ValueError("Invalid JSON"))
    
    # Mock the logger
    logger_mock = MagicMock()
    
    with patch('runtime.function_adapter.logger', logger_mock):
        # Call the main method
        response = AzureFunctionAdapter.main(mock_req)
        
        # Verify predict was called with empty dict
        sys.modules['runtime.dispatcher'].predict.assert_called_with({})
        
        # Verify response
        assert response.status_code == 200
        
        # Verify logging
        logger_mock.warning.assert_called_once_with("Invalid JSON in request body, using empty dict")


def test_function_adapter_main_with_exception():
    """Test the main method when an exception occurs."""
    # Import locally to get a fresh instance
    if 'runtime.function_adapter' in sys.modules:
        del sys.modules['runtime.function_adapter']
    
    # Set up mocks
    setup_module()
    mock_predict = MagicMock(side_effect=ValueError("Test error"))
    sys.modules['runtime.dispatcher'].predict = mock_predict
    
    # Import the module
    from runtime.function_adapter import AzureFunctionAdapter
    
    # Create a mock request
    mock_req = sys.modules['azure.functions'].HttpRequest(body='{"text": "test"}')
    
    # Mock the logger
    logger_mock = MagicMock()
    
    with patch('runtime.function_adapter.logger', logger_mock):
        # Call the main method
        response = AzureFunctionAdapter.main(mock_req)
        
        # Verify response
        assert response.status_code == 500
        expected_response = {"error": "Test error", "status": "failed"}
        assert json.loads(response.body) == expected_response
        
        # Verify logging
        logger_mock.error.assert_called_once_with("Error in Azure Functions adapter: Test error")


def test_main_wrapper_function():
    """Test the main wrapper function."""
    # Import locally to get a fresh instance
    if 'runtime.function_adapter' in sys.modules:
        del sys.modules['runtime.function_adapter']
    
    # Set up mocks
    setup_module()
    
    # Import the module
    from runtime.function_adapter import main, AzureFunctionAdapter
    
    # Mock the adapter main method
    with patch.object(AzureFunctionAdapter, 'main') as mock_main:
        mock_main.return_value = "test_response"
        
        # Create a mock request
        mock_req = sys.modules['azure.functions'].HttpRequest(body='{"text": "test"}')
        
        # Call the wrapper function
        result = main(mock_req)
        
        # Verify adapter main was called with the request
        mock_main.assert_called_once_with(mock_req)
        
        # Verify correct result was returned
        assert result == "test_response"
