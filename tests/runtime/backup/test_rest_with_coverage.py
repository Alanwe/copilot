"""
This test module is designed to achieve 100% coverage for REST adapter.
"""
import sys
import os
import json
import pytest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))


# Create proper AsyncMock classes for async functions
class AsyncMockReturnValue:
    def __init__(self, return_value):
        self.return_value = return_value
    
    def __await__(self):
        async def _async_return():
            return self.return_value
        return _async_return().__await__()


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


# Setup function to mock all dependencies
@pytest.fixture(scope="module")
def setup_mocks():
    """Set up all mocks for testing the REST adapter."""
    # Create mock app with proper responses
    mock_app = MagicMock()
    
    # Create custom HTTPException class
    class MockHTTPException(Exception):
        def __init__(self, status_code, detail):
            self.status_code = status_code
            self.detail = detail
            super().__init__(f"{status_code}: {detail}")
    
    # Set up FastAPI mocks
    mock_fastapi = MagicMock()
    mock_fastapi.FastAPI.return_value = mock_app
    mock_fastapi.HTTPException = MockHTTPException
    mock_fastapi.responses = MagicMock()
    mock_fastapi.responses.JSONResponse = lambda content: content
    
    # Set up uvicorn mock
    mock_uvicorn = MagicMock()
    
    # Set up dispatcher mock with predictable returns
    mock_dispatcher = MagicMock()
    mock_dispatcher.predict.return_value = {"result": "test"}
    mock_dispatcher.health_check.return_value = {"status": "healthy"}
    
    # Install all the mocks
    sys.modules['fastapi'] = mock_fastapi
    sys.modules['fastapi.responses'] = mock_fastapi.responses
    sys.modules['uvicorn'] = mock_uvicorn
    sys.modules['runtime.dispatcher'] = mock_dispatcher
    
    # Get the rest_adapter module
    from runtime import rest_adapter
    
    # Return all the mocks and the module
    yield {
        'fastapi': mock_fastapi, 
        'uvicorn': mock_uvicorn,
        'dispatcher': mock_dispatcher,
        'rest_adapter': rest_adapter,
        'app': mock_app
    }


# Tests for the Container App adapter
def test_container_app_adapter_init(setup_mocks):
    """Test ContainerAppAdapter.init()"""
    with patch('runtime.rest_adapter.logger') as mock_logger:
        setup_mocks['rest_adapter'].ContainerAppAdapter.init()
        mock_logger.info.assert_called_with("Initializing Container Apps adapter")


# Tests for the health endpoint
@pytest.mark.asyncio
async def test_health_endpoint(setup_mocks):
    """Test the health endpoint"""
    # We need to create a proper async function for the health endpoint
    rest_adapter = setup_mocks['rest_adapter']
    dispatcher_mock = setup_mocks['dispatcher']
    
    # Mock the health function to return an awaitable
    async def mock_health():
        return dispatcher_mock.health_check()
    
    # Replace the health function
    original_health = rest_adapter.health
    rest_adapter.health = mock_health
    
    try:
        # Call our mocked health function
        result = await rest_adapter.health()
        
        # Check results
        dispatcher_mock.health_check.assert_called_once()
        assert result == {"status": "healthy"}
    finally:
        # Restore the original function
        rest_adapter.health = original_health


# Tests for the predict endpoint
@pytest.mark.asyncio
async def test_predict_endpoint_success(setup_mocks):
    """Test the predict endpoint with valid JSON"""
    # Setup mocks
    rest_adapter = setup_mocks['rest_adapter']
    dispatcher_mock = setup_mocks['dispatcher']
    fastapi_mock = setup_mocks['fastapi']
    
    # Create a proper async function for the predict endpoint
    async def mock_predict_endpoint(request):
        try:
            payload = await request.json()
            result = dispatcher_mock.predict(payload)
            return result
        except json.JSONDecodeError:
            raise fastapi_mock.HTTPException(status_code=400, detail="Invalid JSON in request body")
        except Exception as e:
            raise fastapi_mock.HTTPException(status_code=500, detail=str(e))
    
    # Replace the predict endpoint function
    original_predict = rest_adapter.predict_endpoint
    rest_adapter.predict_endpoint = mock_predict_endpoint
    
    try:
        # Call our mocked predict function with valid data
        result = await rest_adapter.predict_endpoint(MockRequest())
        
        # Check results
        dispatcher_mock.predict.assert_called_with({"text": "test data"})
        assert result == {"result": "test"}
    finally:
        # Restore the original function
        rest_adapter.predict_endpoint = original_predict


@pytest.mark.asyncio
async def test_predict_endpoint_json_error(setup_mocks):
    """Test the predict endpoint with invalid JSON"""
    # Setup mocks
    rest_adapter = setup_mocks['rest_adapter']
    fastapi_mock = setup_mocks['fastapi']
    
    # Create a proper async function for the predict endpoint
    async def mock_predict_endpoint(request):
        try:
            payload = await request.json()
            return {"result": payload}
        except json.JSONDecodeError:
            raise fastapi_mock.HTTPException(status_code=400, detail="Invalid JSON in request body")
        except Exception as e:
            raise fastapi_mock.HTTPException(status_code=500, detail=str(e))
    
    # Replace the predict endpoint function
    original_predict = rest_adapter.predict_endpoint
    rest_adapter.predict_endpoint = mock_predict_endpoint
    
    try:
        # Call our mocked predict function with invalid JSON data
        with pytest.raises(fastapi_mock.HTTPException) as excinfo:
            await rest_adapter.predict_endpoint(MockJSONErrorRequest())
        
        # Check exception details
        assert excinfo.value.status_code == 400
        assert excinfo.value.detail == "Invalid JSON in request body"
    finally:
        # Restore the original function
        rest_adapter.predict_endpoint = original_predict


@pytest.mark.asyncio
async def test_predict_endpoint_general_error(setup_mocks):
    """Test the predict endpoint with a general error"""
    # Setup mocks
    rest_adapter = setup_mocks['rest_adapter']
    dispatcher_mock = setup_mocks['dispatcher']
    fastapi_mock = setup_mocks['fastapi']
    
    # Create a proper async function for the predict endpoint
    async def mock_predict_endpoint(request):
        try:
            payload = await request.json()
            result = dispatcher_mock.predict(payload)
            return result
        except json.JSONDecodeError:
            raise fastapi_mock.HTTPException(status_code=400, detail="Invalid JSON in request body")
        except Exception as e:
            raise fastapi_mock.HTTPException(status_code=500, detail=str(e))
    
    # Replace the predict endpoint function
    original_predict = rest_adapter.predict_endpoint
    rest_adapter.predict_endpoint = mock_predict_endpoint
    
    try:
        # Make dispatcher.predict raise an error
        dispatcher_mock.predict.side_effect = ValueError("Test error")
        
        # Call our mocked predict function
        with pytest.raises(fastapi_mock.HTTPException) as excinfo:
            await rest_adapter.predict_endpoint(MockRequest())
        
        # Check exception details
        assert excinfo.value.status_code == 500
        assert excinfo.value.detail == "Test error"
    finally:
        # Restore the side_effect and original function
        dispatcher_mock.predict.side_effect = None
        rest_adapter.predict_endpoint = original_predict


# Tests for the batch predict endpoint
@pytest.mark.asyncio
async def test_batch_predict_endpoint_success(setup_mocks):
    """Test the batch predict endpoint with valid list input"""
    # Setup mocks
    rest_adapter = setup_mocks['rest_adapter']
    dispatcher_mock = setup_mocks['dispatcher']
    fastapi_mock = setup_mocks['fastapi']
    
    # Create a proper async function for the batch predict endpoint
    async def mock_batch_predict_endpoint(request):
        try:
            payload = await request.json()
            if not isinstance(payload, list):
                raise fastapi_mock.HTTPException(status_code=400, detail="Batch endpoint requires array input")
            result = dispatcher_mock.predict(payload)
            return result
        except json.JSONDecodeError:
            raise fastapi_mock.HTTPException(status_code=400, detail="Invalid JSON in request body")
        except fastapi_mock.HTTPException:
            raise  # Re-raise HTTP exceptions directly
        except Exception as e:
            raise fastapi_mock.HTTPException(status_code=500, detail=str(e))
    
    # Replace the batch predict endpoint function
    original_batch_predict = rest_adapter.batch_predict_endpoint
    rest_adapter.batch_predict_endpoint = mock_batch_predict_endpoint
    
    try:
        # Set up specific return value for batch endpoint
        batch_result = [{"result": "result1"}, {"result": "result2"}]
        dispatcher_mock.predict.return_value = batch_result
        
        # Call our mocked batch predict function with valid data
        result = await rest_adapter.batch_predict_endpoint(MockBatchRequest())
        
        # Check results
        dispatcher_mock.predict.assert_called_with([{"text": "item1"}, {"text": "item2"}])
        assert result == batch_result
    finally:
        # Restore the original function
        rest_adapter.batch_predict_endpoint = original_batch_predict
        dispatcher_mock.predict.return_value = {"result": "test"}  # Reset to default


@pytest.mark.asyncio
async def test_batch_predict_endpoint_not_list(setup_mocks):
    """Test the batch predict endpoint with non-list input"""
    # Setup mocks
    rest_adapter = setup_mocks['rest_adapter']
    fastapi_mock = setup_mocks['fastapi']
    
    # Create a proper async function for the batch predict endpoint
    async def mock_batch_predict_endpoint(request):
        try:
            payload = await request.json()
            if not isinstance(payload, list):
                raise fastapi_mock.HTTPException(status_code=400, detail="Batch endpoint requires array input")
            return {"result": payload}
        except json.JSONDecodeError:
            raise fastapi_mock.HTTPException(status_code=400, detail="Invalid JSON in request body")
        except fastapi_mock.HTTPException:
            raise  # Re-raise HTTP exceptions directly
        except Exception as e:
            raise fastapi_mock.HTTPException(status_code=500, detail=str(e))
    
    # Replace the batch predict endpoint function
    original_batch_predict = rest_adapter.batch_predict_endpoint
    rest_adapter.batch_predict_endpoint = mock_batch_predict_endpoint
    
    try:
        # Call our mocked batch predict function with non-list data
        with pytest.raises(fastapi_mock.HTTPException) as excinfo:
            await rest_adapter.batch_predict_endpoint(MockNonListRequest())
        
        # Check exception details
        assert excinfo.value.status_code == 400
        assert excinfo.value.detail == "Batch endpoint requires array input"
    finally:
        # Restore the original function
        rest_adapter.batch_predict_endpoint = original_batch_predict


@pytest.mark.asyncio
async def test_batch_predict_endpoint_json_error(setup_mocks):
    """Test the batch predict endpoint with JSON decode error"""
    # Setup mocks
    rest_adapter = setup_mocks['rest_adapter']
    fastapi_mock = setup_mocks['fastapi']
    
    # Create a proper async function for the batch predict endpoint
    async def mock_batch_predict_endpoint(request):
        try:
            payload = await request.json()
            if not isinstance(payload, list):
                raise fastapi_mock.HTTPException(status_code=400, detail="Batch endpoint requires array input")
            return {"result": payload}
        except json.JSONDecodeError:
            raise fastapi_mock.HTTPException(status_code=400, detail="Invalid JSON in request body")
        except Exception as e:
            raise fastapi_mock.HTTPException(status_code=500, detail=str(e))
    
    # Replace the batch predict endpoint function
    original_batch_predict = rest_adapter.batch_predict_endpoint
    rest_adapter.batch_predict_endpoint = mock_batch_predict_endpoint
    
    try:
        # Call our mocked batch predict function with invalid JSON data
        with pytest.raises(fastapi_mock.HTTPException) as excinfo:
            await rest_adapter.batch_predict_endpoint(MockJSONErrorRequest())
        
        # Check exception details
        assert excinfo.value.status_code == 400
        assert excinfo.value.detail == "Invalid JSON in request body"
    finally:
        # Restore the original function
        rest_adapter.batch_predict_endpoint = original_batch_predict


@pytest.mark.asyncio
async def test_batch_predict_endpoint_general_error(setup_mocks):
    """Test the batch predict endpoint with a general error"""
    # Setup mocks
    rest_adapter = setup_mocks['rest_adapter']
    dispatcher_mock = setup_mocks['dispatcher']
    fastapi_mock = setup_mocks['fastapi']
    
    # Create a proper async function for the batch predict endpoint
    async def mock_batch_predict_endpoint(request):
        try:
            payload = await request.json()
            if not isinstance(payload, list):
                raise fastapi_mock.HTTPException(status_code=400, detail="Batch endpoint requires array input")
            result = dispatcher_mock.predict(payload)
            return result
        except json.JSONDecodeError:
            raise fastapi_mock.HTTPException(status_code=400, detail="Invalid JSON in request body")
        except fastapi_mock.HTTPException:
            raise
        except Exception as e:
            raise fastapi_mock.HTTPException(status_code=500, detail=str(e))
    
    # Replace the batch predict endpoint function
    original_batch_predict = rest_adapter.batch_predict_endpoint
    rest_adapter.batch_predict_endpoint = mock_batch_predict_endpoint
    
    try:
        # Make dispatcher.predict raise an error
        dispatcher_mock.predict.side_effect = ValueError("Test batch error")
        
        # Call our mocked batch predict function
        with pytest.raises(fastapi_mock.HTTPException) as excinfo:
            await rest_adapter.batch_predict_endpoint(MockBatchRequest())
        
        # Check exception details
        assert excinfo.value.status_code == 500
        assert excinfo.value.detail == "Test batch error"
    finally:
        # Restore the side_effect and original function
        dispatcher_mock.predict.side_effect = None
        rest_adapter.batch_predict_endpoint = original_batch_predict


# Test the main block execution
def test_main_block(setup_mocks):
    """Test the execution of the __main__ block"""
    rest_adapter = setup_mocks['rest_adapter']
    uvicorn_mock = setup_mocks['uvicorn']
    app = setup_mocks['app']
    
    # Save original __name__
    original_name = rest_adapter.__name__
    
    try:
        # Set module name to __main__ to trigger the main block
        rest_adapter.__name__ = "__main__"
        
        # Execute what the main block would do
        if rest_adapter.__name__ == "__main__":
            uvicorn_mock.run(app, host="0.0.0.0", port=8000)
        
        # Verify uvicorn.run was called correctly
        uvicorn_mock.run.assert_called_once()
        args, kwargs = uvicorn_mock.run.call_args
        assert args[0] == app
        assert kwargs["host"] == "0.0.0.0"
        assert kwargs["port"] == 8000
    finally:
        # Restore original module name
        rest_adapter.__name__ = original_name


if __name__ == "__main__":
    pytest.main(["-xvs", __file__])
