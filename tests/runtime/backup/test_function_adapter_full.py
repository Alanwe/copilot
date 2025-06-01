"""
Test suite for function_adapter.py module to achieve 100% test coverage.
"""
import os
import sys
import json
import pytest
from unittest.mock import patch, MagicMock

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Mock classes
class MockHttpRequest:
    def __init__(self, body=None):
        self.body = body or b'{"text": "test data"}'
        
    def get_body(self):
        return self.body
        
    def get_json(self):
        return json.loads(self.body)

#-----------------------------------------------------------------------------
# Tests for runtime/function_adapter.py
#-----------------------------------------------------------------------------
@pytest.fixture(scope="module")
def mock_azure_functions():
    """Mock Azure Functions dependencies."""
    mock_func = MagicMock()
    
    # Mock HttpRequest
    mock_func.HttpRequest = MockHttpRequest
    
    # Mock HttpResponse
    def mock_http_response(body, status_code=200, headers=None, mimetype="application/json"):
        return {"body": body, "status_code": status_code, "headers": headers, "mimetype": mimetype}
    
    mock_func.HttpResponse = MagicMock(side_effect=mock_http_response)
    
    with patch.dict(sys.modules, {'azure.functions': mock_func}):
        yield mock_func

def test_function_adapter_init():
    """Test AzureFunctionAdapter.init()"""
    from runtime.function_adapter import AzureFunctionAdapter
    
    with patch('runtime.function_adapter.logger') as mock_logger:
        AzureFunctionAdapter.init()
        mock_logger.info.assert_called_with("Initializing Azure Functions adapter")

def test_function_adapter_main_success(mock_azure_functions):
    """Test AzureFunctionAdapter.main() with valid JSON."""
    from runtime.function_adapter import AzureFunctionAdapter
    
    # Create mock request
    mock_req = mock_azure_functions.HttpRequest(body=b'{"text": "test data"}')
    
    # Mock predict function
    with patch('runtime.function_adapter.predict', return_value={"result": "processed"}) as mock_predict:
        with patch('runtime.function_adapter.logger') as mock_logger:
            result = AzureFunctionAdapter.main(mock_req)
            
            # Verify logging and predict calls
            mock_logger.info.assert_called_with("Processing Azure Functions request")
            mock_predict.assert_called_once_with({"text": "test data"})
            
            # Check response
            assert result["status_code"] == 200
            assert json.loads(result["body"]) == {"result": "processed"}

def test_function_adapter_main_invalid_json(mock_azure_functions):
    """Test AzureFunctionAdapter.main() with invalid JSON."""
    from runtime.function_adapter import AzureFunctionAdapter
    
    # Create mock request with invalid JSON
    mock_req = MagicMock()
    mock_req.get_json = MagicMock(side_effect=ValueError("Invalid JSON"))
    
    # Mock predict function
    with patch('runtime.function_adapter.predict', return_value={"result": "processed"}) as mock_predict:
        with patch('runtime.function_adapter.logger') as mock_logger:
            result = AzureFunctionAdapter.main(mock_req)
            
            # Verify logging and predict calls
            mock_logger.warning.assert_called_with("Invalid JSON in request body, using empty dict")
            mock_predict.assert_called_once_with({})
            
            # Check response
            assert result["status_code"] == 200

def test_function_adapter_main_exception(mock_azure_functions):
    """Test AzureFunctionAdapter.main() when predict raises exception."""
    from runtime.function_adapter import AzureFunctionAdapter
    
    # Create mock request
    mock_req = mock_azure_functions.HttpRequest(body=b'{"text": "test data"}')
    
    # Mock predict function to raise exception
    with patch('runtime.function_adapter.predict', side_effect=ValueError("Test error")):
        with patch('runtime.function_adapter.logger') as mock_logger:
            result = AzureFunctionAdapter.main(mock_req)
            
            # Verify error logging and response
            mock_logger.error.assert_called_once()
            assert "Test error" in mock_logger.error.call_args[0][0]
            
            # Check error response
            assert result["status_code"] == 500
            response_body = json.loads(result["body"])
            assert response_body["error"] == "Test error"
            assert response_body["status"] == "failed"

def test_function_module_main(mock_azure_functions):
    """Test the main function in function_adapter."""
    from runtime.function_adapter import main, AzureFunctionAdapter
    
    # Create mock request
    mock_req = mock_azure_functions.HttpRequest()
    
    # Mock AzureFunctionAdapter.main
    with patch.object(AzureFunctionAdapter, 'main', return_value={"status": "ok"}) as mock_adapter_main:
        result = main(mock_req)
        mock_adapter_main.assert_called_once_with(mock_req)
        assert result == {"status": "ok"}

if __name__ == "__main__":
    # Run the tests manually
    pytest.main(["-v", "--cov=runtime.function_adapter", "--cov-report=term-missing", __file__])
