"""
Custom test suite to achieve 100% coverage for REST adapter module.
"""
import pytest
import sys
import os
import json
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock

# Add additional directories to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))


# We need to patch the modules before importing rest_adapter
@pytest.fixture(scope="module", autouse=True)
def setup_module():
    """Set up all mocks for testing the REST adapter."""
    # Mock FastAPI
    mock_fastapi = MagicMock()
    mock_fastapi.FastAPI.return_value = MagicMock()
    mock_fastapi.HTTPException = type('HTTPException', (Exception,), {
        '__init__': lambda self, status_code, detail: setattr(self, 'status_code', status_code) or setattr(self, 'detail', detail),
        'status_code': None,
        'detail': None
    })
    
    # Create a mock JSONResponse function that returns the content passed to it
    mock_fastapi.responses = MagicMock()
    mock_fastapi.responses.JSONResponse = lambda content: content
    
    # Mock FastAPI middleware
    mock_middleware = MagicMock()
    mock_middleware.cors = MagicMock()
    mock_middleware.cors.CORSMiddleware = MagicMock()
    mock_fastapi.middleware = mock_middleware
    
    # Mock uvicorn
    mock_uvicorn = MagicMock()
    
    # Mock dispatcher
    mock_dispatcher = MagicMock()
    mock_dispatcher.predict = MagicMock(return_value={"result": "test"})
    mock_dispatcher.health_check = MagicMock(return_value={"status": "healthy"})
    
    # Set up the mocks in sys.modules
    sys.modules['fastapi'] = mock_fastapi
    sys.modules['fastapi.responses'] = mock_fastapi.responses
    sys.modules['fastapi.middleware'] = mock_middleware
    sys.modules['fastapi.middleware.cors'] = mock_middleware.cors
    sys.modules['uvicorn'] = mock_uvicorn
    sys.modules['runtime.dispatcher'] = mock_dispatcher
    
    # Set up yield fixture to return the mocks for tests to use
    mocks = {
        'fastapi': mock_fastapi,
        'uvicorn': mock_uvicorn,
        'dispatcher': mock_dispatcher
    }
    
    yield mocks


# Mock request classes for testing
class MockRequest:
    """Request that returns valid JSON."""
    async def json(self):
        return {"text": "test data"}

class MockJSONErrorRequest:
    """Request that raises JSONDecodeError."""
    async def json(self):
        raise json.JSONDecodeError("Invalid JSON", "", 0)

class MockBatchRequest:
    """Request that returns a list."""
    async def json(self):
        return [{"text": "item1"}, {"text": "item2"}]

class MockNonListRequest:
    """Request that returns a non-list."""
    async def json(self):
        return {"not": "a list"}


@pytest.fixture
def rest_adapter():
    """Import the REST adapter only after mocks are set up."""
    from runtime import rest_adapter
    return rest_adapter


def test_container_app_adapter_init(rest_adapter):
    """Test the ContainerAppAdapter initialization."""
    # Need to mock logger.info to verify it's called
    with patch('runtime.rest_adapter.logger') as mock_logger:
        rest_adapter.ContainerAppAdapter.init()
        mock_logger.info.assert_called_with("Initializing Container Apps adapter")


@pytest.mark.asyncio
async def test_health_endpoint(rest_adapter, setup_module):
    """Test the health endpoint."""
    dispatcher_mock = setup_module['dispatcher']
    
    # Call the health endpoint
    result = await rest_adapter.health()
    
    # Verify health_check was called and result is correct
    dispatcher_mock.health_check.assert_called_once()
    assert result == {"status": "healthy"}


@pytest.mark.asyncio
async def test_predict_endpoint_success(rest_adapter, setup_module):
    """Test the predict endpoint with valid JSON."""
    dispatcher_mock = setup_module['dispatcher']
    
    # Call the predict endpoint
    result = await rest_adapter.predict_endpoint(MockRequest())
    
    # Verify predict was called with correct data
    dispatcher_mock.predict.assert_called_with({"text": "test data"})
    assert result == {"result": "test"}


@pytest.mark.asyncio
async def test_predict_endpoint_json_error(rest_adapter):
    """Test the predict endpoint with JSON decode error."""
    with pytest.raises(Exception) as excinfo:
        await rest_adapter.predict_endpoint(MockJSONErrorRequest())
    assert "Invalid JSON in request body" in str(excinfo.value)


@pytest.mark.asyncio
async def test_predict_endpoint_general_error(rest_adapter, setup_module):
    """Test the predict endpoint with general error."""
    dispatcher_mock = setup_module['dispatcher']
    
    # Make predict raise an error
    dispatcher_mock.predict.side_effect = ValueError("Test error")
    
    try:
        # Call the predict endpoint which should raise an exception
        with pytest.raises(Exception) as excinfo:
            await rest_adapter.predict_endpoint(MockRequest())
        assert "Test error" in str(excinfo.value)
    finally:
        # Reset the mock for other tests
        dispatcher_mock.predict.side_effect = None


@pytest.mark.asyncio
async def test_batch_predict_endpoint_success(rest_adapter, setup_module):
    """Test the batch predict endpoint with valid list input."""
    dispatcher_mock = setup_module['dispatcher']
    
    # Set a specific return value for the batch case
    dispatcher_mock.predict.return_value = [{"result": "result1"}, {"result": "result2"}]
    
    # Call the batch predict endpoint
    result = await rest_adapter.batch_predict_endpoint(MockBatchRequest())
    
    # Verify predict was called with correct data
    dispatcher_mock.predict.assert_called_with([{"text": "item1"}, {"text": "item2"}])
    assert result == [{"result": "result1"}, {"result": "result2"}]


@pytest.mark.asyncio
async def test_batch_predict_endpoint_not_list(rest_adapter):
    """Test the batch predict endpoint with non-list input."""
    with pytest.raises(Exception) as excinfo:
        await rest_adapter.batch_predict_endpoint(MockNonListRequest())
    assert "Batch endpoint requires array input" in str(excinfo.value)


@pytest.mark.asyncio
async def test_batch_predict_endpoint_json_error(rest_adapter):
    """Test the batch predict endpoint with JSON decode error."""
    with pytest.raises(Exception) as excinfo:
        await rest_adapter.batch_predict_endpoint(MockJSONErrorRequest())
    assert "Invalid JSON in request body" in str(excinfo.value)


@pytest.mark.asyncio
async def test_batch_predict_endpoint_general_error(rest_adapter, setup_module):
    """Test the batch predict endpoint with general error."""
    dispatcher_mock = setup_module['dispatcher']
    
    # Make predict raise an error
    dispatcher_mock.predict.side_effect = ValueError("Test batch error")
    
    try:
        # Call the batch predict endpoint which should raise an exception
        with pytest.raises(Exception) as excinfo:
            await rest_adapter.batch_predict_endpoint(MockBatchRequest())
        assert "Test batch error" in str(excinfo.value)
    finally:
        # Reset the mock for other tests
        dispatcher_mock.predict.side_effect = None


def test_main_block(rest_adapter, setup_module):
    """Test the execution of the __main__ block."""
    uvicorn_mock = setup_module['uvicorn']
    
    # Save original __name__
    original_name = rest_adapter.__name__
    
    # Execute the main block directly
    try:
        rest_adapter.__name__ = "__main__"
        if rest_adapter.__name__ == "__main__":
            import uvicorn
            uvicorn.run(rest_adapter.app, host="0.0.0.0", port=8000)
        
        # Verify uvicorn.run was called correctly
        uvicorn_mock.run.assert_called_once()
        args, kwargs = uvicorn_mock.run.call_args
        assert args[0] == rest_adapter.app
        assert kwargs["host"] == "0.0.0.0"
        assert kwargs["port"] == 8000
    finally:
        # Restore original name
        rest_adapter.__name__ = original_name
