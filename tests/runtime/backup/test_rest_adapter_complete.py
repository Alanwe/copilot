"""
Comprehensive test coverage for the REST API adapter module.
Uses pytest-asyncio for async function testing.
"""
import sys
import os
import json
import logging
import pytest
import asyncio
from unittest.mock import patch, Mock, MagicMock, AsyncMock

# Configure logging
logging.basicConfig(level=logging.INFO)


def setup_function():
    """Set up mocks before each test."""
    # Clear module cache
    if 'runtime.rest_adapter' in sys.modules:
        del sys.modules['runtime.rest_adapter']
    
    # Create mock for FastAPI
    sys.modules['fastapi'] = Mock()
    sys.modules['fastapi.responses'] = Mock()
    
    # Setup mock FastAPI app
    mock_app = MagicMock()
    
    # Create a decorator factory for route handlers
    def route_decorator_factory(route_type):
        def decorator(path):
            def wrapper(func):
                # Store the function so we can retrieve and test it
                if not hasattr(mock_app, '_routes'):
                    mock_app._routes = {}
                mock_app._routes[(route_type, path)] = func
                return func
            return wrapper
        return decorator
    
    # Add decorator methods to the mock app
    mock_app.get = route_decorator_factory('GET')
    mock_app.post = route_decorator_factory('POST')
    
    sys.modules['fastapi'].FastAPI = MagicMock(return_value=mock_app)
    
    # Mock HTTPException that stores status_code and detail
    class MockHTTPException(Exception):
        def __init__(self, status_code, detail):
            self.status_code = status_code
            self.detail = detail
            super().__init__(f"{status_code}: {detail}")
    
    sys.modules['fastapi'].HTTPException = MockHTTPException
    
    # Mock Request class with async json method
    class MockRequest:
        def __init__(self, json_data=None, json_error=False):
            self._json_data = json_data
            self._json_error = json_error
        
        async def json(self):
            if self._json_error:
                raise json.JSONDecodeError("Invalid JSON", "{", 0)
            return self._json_data
    
    sys.modules['fastapi'].Request = MockRequest
    
    # Mock JSONResponse
    sys.modules['fastapi'].responses = Mock()
    sys.modules['fastapi'].responses.JSONResponse = MagicMock(side_effect=lambda content: {"content": content})
    
    # Mock dispatcher functions
    sys.modules['runtime.dispatcher'] = Mock()
    sys.modules['runtime.dispatcher'].predict = MagicMock(return_value={"result": "test_result"})
    sys.modules['runtime.dispatcher'].health_check = MagicMock(return_value={"status": "healthy"})
    
    # Mock uvicorn
    sys.modules['uvicorn'] = Mock()
    sys.modules['uvicorn'].run = MagicMock()


def test_container_app_adapter_init():
    """Test initialization of the ContainerAppAdapter class."""
    with patch('logging.getLogger') as mock_logger:
        # Create logger mock that properly stores calls
        mock_log_instance = MagicMock()
        mock_logger.return_value = mock_log_instance
        
        # Import the module - this will immediately call init() during module initialization
        import runtime.rest_adapter
        
        # Reset mock to clear initial call
        mock_log_instance.reset_mock()
        
        # Call init again
        runtime.rest_adapter.ContainerAppAdapter.init()
        
        # Verify the logger was called correctly
        mock_log_instance.info.assert_called_once_with("Initializing Container Apps adapter")


def test_app_initialization():
    """Test the FastAPI app initialization."""
    setup_function()
    
    # Import the module
    import runtime.rest_adapter
    
    # Check that FastAPI was initialized with the correct parameters
    sys.modules['fastapi'].FastAPI.assert_called_once()
    args, kwargs = sys.modules['fastapi'].FastAPI.call_args
    assert kwargs["title"] == "Azure Components Foundry"
    assert kwargs["description"] == "Unified runtime for Azure components" 
    assert kwargs["version"] == "1.0.0"
    
    # Verify routes were registered
    app = sys.modules['fastapi'].FastAPI.return_value
    assert hasattr(app, '_routes')
    routes = app._routes
    
    # Verify health endpoint is registered
    assert ('GET', '/health') in routes
    
    # Verify predict endpoints are registered
    assert ('POST', '/predict') in routes
    assert ('POST', '/batch') in routes


@pytest.mark.asyncio
async def test_health_endpoint():
    """Test the health check endpoint."""
    setup_function()
    
    # Mock health_check to return a specific value
    mock_health_check = MagicMock(return_value={"status": "test_healthy"})
    sys.modules['runtime.dispatcher'].health_check = mock_health_check
    
    # Import the module
    import runtime.rest_adapter
    
    # Get the health route handler function
    app = sys.modules['fastapi'].FastAPI.return_value
    health_handler = app._routes[('GET', '/health')]
    
    # Call the function directly
    result = await health_handler()
    
    # Verify health_check was called and the result is correct
    mock_health_check.assert_called_once()
    assert result == {"status": "test_healthy"}


@pytest.mark.asyncio
async def test_predict_endpoint_success():
    """Test the predict endpoint with valid input."""
    setup_function()
    
    # Mock predict to return a specific value
    mock_predict = MagicMock(return_value={"result": "test_prediction"})
    sys.modules['runtime.dispatcher'].predict = mock_predict
    
    # Import the module
    import runtime.rest_adapter
    
    # Get the predict route handler function
    app = sys.modules['fastapi'].FastAPI.return_value
    predict_handler = app._routes[('POST', '/predict')]
    
    # Create a mock request
    request = sys.modules['fastapi'].Request(json_data={"input": "test data"})
    
    # Call the function
    result = await predict_handler(request)
    
    # Verify predict was called with correct args
    mock_predict.assert_called_once_with({"input": "test data"})
    
    # Verify result is correct
    assert result == {"content": {"result": "test_prediction"}}


@pytest.mark.asyncio
async def test_predict_endpoint_json_error():
    """Test the predict endpoint with invalid JSON."""
    setup_function()
    
    # Import the module
    import runtime.rest_adapter
    
    # Get the predict route handler function
    app = sys.modules['fastapi'].FastAPI.return_value
    predict_handler = app._routes[('POST', '/predict')]
    
    # Create a mock request that raises JSONDecodeError
    request = sys.modules['fastapi'].Request(json_error=True)
    
    # Call the function and expect an exception
    with pytest.raises(Exception) as excinfo:
        await predict_handler(request)
    
    # Verify the exception details
    assert "Invalid JSON in request body" in str(excinfo.value)


@pytest.mark.asyncio
async def test_predict_endpoint_other_exception():
    """Test the predict endpoint with other exceptions."""
    setup_function()
    
    # Mock predict to raise an exception
    mock_predict = MagicMock(side_effect=ValueError("Test error"))
    sys.modules['runtime.dispatcher'].predict = mock_predict
    
    # Import the module
    import runtime.rest_adapter
    
    # Get the predict route handler function
    app = sys.modules['fastapi'].FastAPI.return_value
    predict_handler = app._routes[('POST', '/predict')]
    
    # Create a mock request
    request = sys.modules['fastapi'].Request(json_data={"input": "test data"})
    
    # Call the function and expect an exception
    with pytest.raises(Exception) as excinfo:
        await predict_handler(request)
    
    # Verify the exception details
    assert "Test error" in str(excinfo.value)


@pytest.mark.asyncio
async def test_batch_predict_endpoint_success():
    """Test the batch predict endpoint with valid input."""
    setup_function()
    
    # Mock predict to return a specific value
    mock_predict = MagicMock(return_value=[{"result": "batch_result1"}, {"result": "batch_result2"}])
    sys.modules['runtime.dispatcher'].predict = mock_predict
    
    # Import the module
    import runtime.rest_adapter
    
    # Get the batch predict route handler function
    app = sys.modules['fastapi'].FastAPI.return_value
    batch_handler = app._routes[('POST', '/batch')]
    
    # Create a mock request
    request = sys.modules['fastapi'].Request(json_data=[{"input": "data1"}, {"input": "data2"}])
    
    # Call the function
    result = await batch_handler(request)
    
    # Verify predict was called with correct args
    mock_predict.assert_called_once_with([{"input": "data1"}, {"input": "data2"}])
    
    # Verify result is correct
    assert result == {"content": [{"result": "batch_result1"}, {"result": "batch_result2"}]}


@pytest.mark.asyncio
async def test_batch_predict_endpoint_not_list():
    """Test the batch predict endpoint with non-list input."""
    setup_function()
    
    # Import the module
    import runtime.rest_adapter
    
    # Get the batch predict route handler function
    app = sys.modules['fastapi'].FastAPI.return_value
    batch_handler = app._routes[('POST', '/batch')]
    
    # Create a mock request with dict instead of list
    request = sys.modules['fastapi'].Request(json_data={"input": "data"})
    
    # Call the function and expect an exception
    with pytest.raises(Exception) as excinfo:
        await batch_handler(request)
    
    # Verify the exception details
    assert "Batch endpoint requires array input" in str(excinfo.value)


@pytest.mark.asyncio
async def test_batch_predict_endpoint_json_error():
    """Test the batch predict endpoint with invalid JSON."""
    setup_function()
    
    # Import the module
    import runtime.rest_adapter
    
    # Get the batch predict route handler function
    app = sys.modules['fastapi'].FastAPI.return_value
    batch_handler = app._routes[('POST', '/batch')]
    
    # Create a mock request that raises JSONDecodeError
    request = sys.modules['fastapi'].Request(json_error=True)
    
    # Call the function and expect an exception
    with pytest.raises(Exception) as excinfo:
        await batch_handler(request)
    
    # Verify the exception details
    assert "Invalid JSON in request body" in str(excinfo.value)


@pytest.mark.asyncio
async def test_batch_predict_endpoint_other_exception():
    """Test the batch predict endpoint with other exceptions."""
    setup_function()
    
    # Mock predict to raise an exception
    mock_predict = MagicMock(side_effect=ValueError("Batch test error"))
    sys.modules['runtime.dispatcher'].predict = mock_predict
    
    # Import the module
    import runtime.rest_adapter
    
    # Get the batch predict route handler function
    app = sys.modules['fastapi'].FastAPI.return_value
    batch_handler = app._routes[('POST', '/batch')]
    
    # Create a mock request
    request = sys.modules['fastapi'].Request(json_data=[{"input": "data1"}, {"input": "data2"}])
    
    # Call the function and expect an exception
    with pytest.raises(Exception) as excinfo:
        await batch_handler(request)
    
    # Verify the exception details
    assert "Batch test error" in str(excinfo.value)


def test_main_function():
    """Test the main block execution path."""
    setup_function()
    
    # Mock uvicorn.run
    mock_run = MagicMock()
    sys.modules['uvicorn'].run = mock_run
    
    # Mock __name__ to trigger the __main__ block
    with patch('__main__.__name__', '__main__'):
        # Import the module with __name__ == '__main__' to execute main block
        with patch.dict(os.environ, {"PYTHONPATH": "/workspaces/copilot"}):
            # Create a temporary script that imports the module
            with open('/tmp/test_import.py', 'w') as f:
                f.write("""
import sys
sys.path.append('/workspaces/copilot')
import runtime.rest_adapter
                """)
            
            # Execute the file with modified __name__
            exec_globals = {'__name__': '__main__', 'uvicorn': sys.modules['uvicorn']}
            with open('/workspaces/copilot/runtime/rest_adapter.py', 'r') as f:
                # Execute only the if __name__ == "__main__" block
                content = f.read()
                main_block = content.split('if __name__ == "__main__":')[1]
                exec(f"if True: {main_block}", exec_globals)
    
    # Verify uvicorn.run was called with the correct parameters
    mock_run.assert_called_once()
    kwargs = mock_run.call_args[1]
    assert kwargs["host"] == "0.0.0.0" 
    assert kwargs["port"] == 8000
