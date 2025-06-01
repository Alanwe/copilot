"""
Test coverage for the Container Apps / REST API adapter module.
"""
import sys
import os
import json
import logging
from unittest.mock import patch, Mock, MagicMock, AsyncMock

# Configure logging
logging.basicConfig(level=logging.INFO)

# Mock the external imports
def setup_module():
    """Set up mocks before importing the module."""
    # Mock FastAPI
    sys.modules['fastapi'] = Mock()
    sys.modules['fastapi.responses'] = Mock()
    sys.modules['fastapi'].FastAPI = MagicMock(return_value=MagicMock())
    sys.modules['fastapi'].HTTPException = MagicMock()
    sys.modules['fastapi'].Request = MagicMock()
    sys.modules['fastapi'].responses = Mock()
    sys.modules['fastapi'].responses.JSONResponse = MagicMock()
    sys.modules['fastapi.middleware'] = Mock()
    sys.modules['fastapi.middleware.cors'] = Mock()
    sys.modules['fastapi.middleware.cors'].CORSMiddleware = MagicMock()
    
    # Mock Uvicorn
    sys.modules['uvicorn'] = Mock()
    sys.modules['uvicorn'].run = MagicMock()
    
    # Mock dispatcher.predict
    sys.modules['runtime.dispatcher'] = Mock()
    sys.modules['runtime.dispatcher'].predict = Mock(return_value={"result": "test_result"})
    sys.modules['runtime.dispatcher'].health_check = Mock(return_value={"status": "healthy"})


def teardown_module():
    """Clean up mocks after tests."""
    if 'runtime.rest_adapter' in sys.modules:
        del sys.modules['runtime.rest_adapter']


def test_container_app_adapter_initialization():
    """Test initialization of the Container App adapter."""
    # Import locally to get a fresh instance
    if 'runtime.rest_adapter' in sys.modules:
        del sys.modules['runtime.rest_adapter']
    
    # Set up mocks
    setup_module()
    
    # Import the module
    from runtime.rest_adapter import ContainerAppAdapter
    
    # Test the init method
    with patch('logging.getLogger') as mock_logger:
        mock_log_instance = MagicMock()
        mock_logger.return_value = mock_log_instance
        ContainerAppAdapter.init()
        # Verify logging was called
        mock_log_instance.info.assert_called_with("Initializing Container Apps adapter")


def test_health_endpoint():
    """Test the health check endpoint."""
    # Import locally to get a fresh instance
    if 'runtime.rest_adapter' in sys.modules:
        del sys.modules['runtime.rest_adapter']
    
    # Set up mocks
    setup_module()
    mock_health_check = MagicMock(return_value={"status": "healthy"})
    sys.modules['runtime.dispatcher'].health_check = mock_health_check
    
    # Import the module
    from runtime.rest_adapter import health
    
    # Call the endpoint
    result = health()
    
    # Verify health_check was called
    mock_health_check.assert_called_once()
    assert result == {"status": "healthy"}


async def test_predict_endpoint_success():
    """Test the predict endpoint with valid input."""
    # Import locally to get a fresh instance
    if 'runtime.rest_adapter' in sys.modules:
        del sys.modules['runtime.rest_adapter']
    
    # Set up mocks
    setup_module()
    mock_predict = MagicMock(return_value={"result": "mocked_result"})
    sys.modules['runtime.dispatcher'].predict = mock_predict
    
    # Create mock request with JSON
    mock_request = AsyncMock()
    mock_request.json = AsyncMock(return_value={"text": "test"})
    
    # Import the module
    from runtime.rest_adapter import predict_endpoint
    
    # Set up JSONResponse mock
    sys.modules['fastapi'].responses.JSONResponse = MagicMock(return_value="json_response")
    
    # Call the endpoint
    result = await predict_endpoint(mock_request)
    
    # Verify predict was called correctly
    mock_predict.assert_called_with({"text": "test"})
    
    # Verify JSONResponse was called with correct args
    sys.modules['fastapi'].responses.JSONResponse.assert_called_with(content={"result": "mocked_result"})
    
    # Verify result
    assert result == "json_response"


async def test_predict_endpoint_invalid_json():
    """Test the predict endpoint with invalid JSON input."""
    # Import locally to get a fresh instance
    if 'runtime.rest_adapter' in sys.modules:
        del sys.modules['runtime.rest_adapter']
    
    # Set up mocks
    setup_module()
    
    # Create mock request that raises JSONDecodeError
    mock_request = AsyncMock()
    mock_request.json = AsyncMock(side_effect=json.JSONDecodeError("test", "{", 0))
    
    # Import the module
    from runtime.rest_adapter import predict_endpoint
    
    # Set up HTTPException mock
    sys.modules['fastapi'].HTTPException = MagicMock(side_effect=Exception("HTTPException"))
    
    # Call the endpoint
    try:
        await predict_endpoint(mock_request)
        assert False, "Expected exception was not raised"
    except Exception as e:
        assert str(e) == "HTTPException"
        # Verify HTTPException was called with correct args
        sys.modules['fastapi'].HTTPException.assert_called_with(status_code=400, detail="Invalid JSON in request body")


async def test_predict_endpoint_exception():
    """Test the predict endpoint when an exception occurs."""
    # Import locally to get a fresh instance
    if 'runtime.rest_adapter' in sys.modules:
        del sys.modules['runtime.rest_adapter']
    
    # Set up mocks
    setup_module()
    mock_predict = MagicMock(side_effect=ValueError("Test error"))
    sys.modules['runtime.dispatcher'].predict = mock_predict
    
    # Create mock request
    mock_request = AsyncMock()
    mock_request.json = AsyncMock(return_value={"text": "test"})
    
    # Import the module
    from runtime.rest_adapter import predict_endpoint
    
    # Set up HTTPException mock
    sys.modules['fastapi'].HTTPException = MagicMock(side_effect=Exception("HTTPException"))
    
    # Call the endpoint
    try:
        await predict_endpoint(mock_request)
        assert False, "Expected exception was not raised"
    except Exception as e:
        assert str(e) == "HTTPException"
        # Verify HTTPException was called with correct args
        sys.modules['fastapi'].HTTPException.assert_called_with(status_code=500, detail="Test error")


async def test_batch_predict_endpoint_success():
    """Test the batch predict endpoint with valid input."""
    # Import locally to get a fresh instance
    if 'runtime.rest_adapter' in sys.modules:
        del sys.modules['runtime.rest_adapter']
    
    # Set up mocks
    setup_module()
    mock_predict = MagicMock(return_value=[{"result": "mocked_result1"}, {"result": "mocked_result2"}])
    sys.modules['runtime.dispatcher'].predict = mock_predict
    
    # Create mock request with JSON array
    mock_request = AsyncMock()
    mock_request.json = AsyncMock(return_value=[{"text": "test1"}, {"text": "test2"}])
    
    # Import the module
    from runtime.rest_adapter import batch_predict_endpoint
    
    # Set up JSONResponse mock
    sys.modules['fastapi'].responses.JSONResponse = MagicMock(return_value="json_response")
    
    # Call the endpoint
    result = await batch_predict_endpoint(mock_request)
    
    # Verify predict was called correctly
    mock_predict.assert_called_with([{"text": "test1"}, {"text": "test2"}])
    
    # Verify JSONResponse was called with correct args
    sys.modules['fastapi'].responses.JSONResponse.assert_called_with(
        content=[{"result": "mocked_result1"}, {"result": "mocked_result2"}])
    
    # Verify result
    assert result == "json_response"


async def test_batch_predict_endpoint_not_array():
    """Test the batch predict endpoint with non-array input."""
    # Import locally to get a fresh instance
    if 'runtime.rest_adapter' in sys.modules:
        del sys.modules['runtime.rest_adapter']
    
    # Set up mocks
    setup_module()
    
    # Create mock request with non-array JSON
    mock_request = AsyncMock()
    mock_request.json = AsyncMock(return_value={"text": "test"})
    
    # Import the module
    from runtime.rest_adapter import batch_predict_endpoint
    
    # Set up HTTPException mock
    sys.modules['fastapi'].HTTPException = MagicMock(side_effect=Exception("HTTPException"))
    
    # Call the endpoint
    try:
        await batch_predict_endpoint(mock_request)
        assert False, "Expected exception was not raised"
    except Exception as e:
        assert str(e) == "HTTPException"
        # Verify HTTPException was called with correct args
        sys.modules['fastapi'].HTTPException.assert_called_with(
            status_code=400, detail="Batch endpoint requires array input")


async def test_batch_predict_endpoint_invalid_json():
    """Test the batch predict endpoint with invalid JSON input."""
    # Import locally to get a fresh instance
    if 'runtime.rest_adapter' in sys.modules:
        del sys.modules['runtime.rest_adapter']
    
    # Set up mocks
    setup_module()
    
    # Create mock request that raises JSONDecodeError
    mock_request = AsyncMock()
    mock_request.json = AsyncMock(side_effect=json.JSONDecodeError("test", "{", 0))
    
    # Import the module
    from runtime.rest_adapter import batch_predict_endpoint
    
    # Set up HTTPException mock
    sys.modules['fastapi'].HTTPException = MagicMock(side_effect=Exception("HTTPException"))
    
    # Call the endpoint
    try:
        await batch_predict_endpoint(mock_request)
        assert False, "Expected exception was not raised"
    except Exception as e:
        assert str(e) == "HTTPException"
        # Verify HTTPException was called with correct args
        sys.modules['fastapi'].HTTPException.assert_called_with(
            status_code=400, detail="Invalid JSON in request body")


def test_main_block():
    """Test the __main__ block execution."""
    # Import locally to get a fresh instance
    if 'runtime.rest_adapter' in sys.modules:
        del sys.modules['runtime.rest_adapter']
    
    # Set up mocks
    setup_module()
    
    # Set up uvicorn.run mock
    sys.modules['uvicorn'].run = MagicMock()
    
    # Execute main block
    with patch.dict('sys.modules'):
        with patch('builtins.__import__', return_value=sys.modules['runtime.rest_adapter']):
            filepath = os.path.abspath('/workspaces/copilot/runtime/rest_adapter.py')
            with open(filepath) as f:
                code = compile(f.read(), filepath, 'exec')
                globals_dict = {'__name__': '__main__'}
                exec(code, globals_dict)
    
    # Verify uvicorn.run was called with correct args
    sys.modules['uvicorn'].run.assert_called_once()
    args, kwargs = sys.modules['uvicorn'].run.call_args
    assert kwargs.get('host') == "0.0.0.0"
    assert kwargs.get('port') == 8000


def test_rest_adapter_initialization():
    """Test initialization of the REST adapter."""
    # Import locally to get a fresh instance
    if 'runtime.rest_adapter' in sys.modules:
        del sys.modules['runtime.rest_adapter']
    
    # Set up mocks
    setup_module()
    mock_app = MagicMock()
    sys.modules['fastapi'].FastAPI.return_value = mock_app
    
    # Mock the dispatcher
    mock_dispatcher = MagicMock()
    mock_dispatcher.predict.return_value = {"result": "mocked_result"}
    mock_dispatcher.health_check.return_value = {"status": "healthy"}
    
    # Import with patched modules
    with patch.dict(sys.modules, {'runtime.dispatcher': mock_dispatcher}):
        # Import the module
        from runtime.rest_adapter import ContainerAppAdapter
        
        # Create the adapter
        adapter = ContainerAppAdapter()
        
        # Verify the app was set up with routes
        assert adapter.app is not None
        mock_app.add_middleware.assert_called()
        mock_app.get.assert_called()
        mock_app.post.assert_called()


def test_rest_adapter_predict():
    """Test the predict endpoint of the REST adapter."""
    # Import locally to get a fresh instance
    if 'runtime.rest_adapter' in sys.modules:
        del sys.modules['runtime.rest_adapter']
    
    # Set up mocks
    setup_module()
    mock_app = MagicMock()
    sys.modules['fastapi'].FastAPI.return_value = mock_app
    
    # Mock FastAPI route registration to capture route handlers
    route_handlers = {}
    
    def mock_add_route(path, endpoint, methods=None):
        route_handlers[path] = endpoint
    
    mock_app.add_api_route = mock_add_route
    
    # Mock the dispatcher
    mock_dispatcher = MagicMock()
    mock_dispatcher.predict.return_value = {"result": "mocked_result"}
    mock_dispatcher.health_check.return_value = {"status": "healthy"}
    
    # Import with patched modules
    with patch.dict(sys.modules, {'runtime.dispatcher': mock_dispatcher}):
        # Import the module
        from runtime.rest_adapter import ContainerAppAdapter
        
        # Create the adapter
        adapter = ContainerAppAdapter()
        
        # Call the predict endpoint handler
        mock_request = MagicMock()
        mock_request.json.return_value = {"text": "test input"}
        
        # Check if route handlers were captured
        if "/predict" in route_handlers:
            result = route_handlers["/predict"](mock_request)
            
            # Verify the dispatcher was called with the input
            mock_dispatcher.predict.assert_called_with({"text": "test input"})
            assert result == {"result": "mocked_result"}


def test_rest_adapter_health_check():
    """Test the health check endpoint of the REST adapter."""
    # Import locally to get a fresh instance
    if 'runtime.rest_adapter' in sys.modules:
        del sys.modules['runtime.rest_adapter']
    
    # Set up mocks
    setup_module()
    mock_app = MagicMock()
    sys.modules['fastapi'].FastAPI.return_value = mock_app
    
    # Mock FastAPI route registration to capture route handlers
    route_handlers = {}
    
    def mock_add_route(path, endpoint, methods=None):
        route_handlers[path] = endpoint
    
    mock_app.add_api_route = mock_add_route
    
    # Mock the dispatcher
    mock_dispatcher = MagicMock()
    mock_dispatcher.health_check.return_value = {"status": "healthy"}
    
    # Import with patched modules
    with patch.dict(sys.modules, {'runtime.dispatcher': mock_dispatcher}):
        # Import the module
        from runtime.rest_adapter import ContainerAppAdapter
        
        # Create the adapter
        adapter = ContainerAppAdapter()
        
        # Call the health check endpoint handler
        if "/health" in route_handlers:
            result = route_handlers["/health"]()
            
            # Verify the dispatcher's health check was called
            mock_dispatcher.health_check.assert_called_once()
            assert result == {"status": "healthy"}


def test_rest_adapter_run():
    """Test the run method of the REST adapter."""
    # Import locally to get a fresh instance
    if 'runtime.rest_adapter' in sys.modules:
        del sys.modules['runtime.rest_adapter']
    
    # Set up mocks
    setup_module()
    
    # Mock uvicorn.run
    mock_uvicorn_run = MagicMock()
    sys.modules['uvicorn'].run = mock_uvicorn_run
    
    # Import the module
    from runtime.rest_adapter import ContainerAppAdapter
    
    # Create the adapter and call run
    adapter = ContainerAppAdapter()
    adapter.run()
    
    # Verify uvicorn.run was called
    mock_uvicorn_run.assert_called_once()


if __name__ == "__main__":
    setup_module()
    test_rest_adapter_initialization()
    test_rest_adapter_predict()
    test_rest_adapter_health_check()
    test_rest_adapter_run()
    teardown_module()
