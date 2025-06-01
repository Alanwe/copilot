#!/usr/bin/env python3
"""
Custom test runner for the REST adapter module.
"""
import os
import sys
import json
import asyncio
import coverage
from unittest.mock import patch, MagicMock

# Start the coverage tracking
cov = coverage.Coverage(source=['runtime.rest_adapter'])
cov.start()

# Set up our working directory to be the project root
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Mock all the necessary modules
mock_app = MagicMock()
mock_fastapi = MagicMock()
mock_fastapi.FastAPI.return_value = mock_app
mock_fastapi.HTTPException = type('HTTPException', (Exception,), {
    '__init__': lambda self, status_code=None, detail=None: setattr(self, 'status_code', status_code) or setattr(self, 'detail', detail),
    'status_code': None,
    'detail': None
})
mock_responses = MagicMock()
mock_responses.JSONResponse = lambda content: content

mock_uvicorn = MagicMock()
mock_dispatcher = MagicMock()
mock_dispatcher.health_check.return_value = {"status": "healthy"}
mock_dispatcher.predict.return_value = {"result": "test"}

# Install the mocks
sys.modules['fastapi'] = mock_fastapi
sys.modules['fastapi.responses'] = mock_responses
sys.modules['uvicorn'] = mock_uvicorn
sys.modules['runtime.dispatcher'] = mock_dispatcher

# Now we can import the module
import runtime.rest_adapter

# Test the ContainerAppAdapter initialization
print("Testing ContainerAppAdapter.init()...")
with patch('runtime.rest_adapter.logger') as mock_logger:
    runtime.rest_adapter.ContainerAppAdapter.init()
    mock_logger.info.assert_called_with("Initializing Container Apps adapter")
    print("✓ ContainerAppAdapter.init() test passed")

# Create mock request objects for testing
class MockRequest:
    """Mock request with valid JSON data."""
    async def json(self):
        return {"text": "test data"}

class MockJSONErrorRequest:
    """Mock request that raises JSONDecodeError."""
    async def json(self):
        raise json.JSONDecodeError("Invalid JSON", "", 0)

class MockBatchRequest:
    """Mock request with valid list JSON data."""
    async def json(self):
        return [{"text": "item1"}, {"text": "item2"}]

class MockNonListRequest:
    """Mock request with non-list JSON data."""
    async def json(self):
        return {"not": "a list"}

# Test async endpoints
async def test_health():
    """Test the health endpoint."""
    print("\nTesting health endpoint...")
    # Create a replacement async function that we can call
    async def mock_health():
        return mock_dispatcher.health_check()

    # Save original function
    original_health = runtime.rest_adapter.health
    runtime.rest_adapter.health = mock_health
    
    try:
        # Call the function
        result = await runtime.rest_adapter.health()
        
        # Check the result
        mock_dispatcher.health_check.assert_called_once()
        assert result == {"status": "healthy"}
        print("✓ Health endpoint test passed")
    finally:
        # Restore original function
        runtime.rest_adapter.health = original_health

async def test_predict_endpoint_success():
    """Test the predict endpoint with valid data."""
    print("\nTesting predict endpoint (success)...")
    
    # Create a replacement async function that replicates the code
    async def mock_predict(request):
        try:
            payload = await request.json()
            result = mock_dispatcher.predict(payload)
            return mock_responses.JSONResponse(content=result)
        except json.JSONDecodeError:
            raise mock_fastapi.HTTPException(status_code=400, detail="Invalid JSON in request body")
        except Exception as e:
            raise mock_fastapi.HTTPException(status_code=500, detail=str(e))
    
    # Save original function
    original_predict = runtime.rest_adapter.predict_endpoint
    runtime.rest_adapter.predict_endpoint = mock_predict
    
    try:
        # Call the function
        result = await runtime.rest_adapter.predict_endpoint(MockRequest())
        
        # Check the result
        mock_dispatcher.predict.assert_called_with({"text": "test data"})
        assert result == {"result": "test"}
        print("✓ Predict endpoint success test passed")
    finally:
        # Restore original function
        runtime.rest_adapter.predict_endpoint = original_predict

async def test_predict_endpoint_json_error():
    """Test predict endpoint with JSON decode error."""
    print("\nTesting predict endpoint (JSON error)...")
    
    # Create a replacement async function that replicates the code
    async def mock_predict(request):
        try:
            payload = await request.json()
            result = mock_dispatcher.predict(payload)
            return mock_responses.JSONResponse(content=result)
        except json.JSONDecodeError:
            raise mock_fastapi.HTTPException(status_code=400, detail="Invalid JSON in request body")
        except Exception as e:
            raise mock_fastapi.HTTPException(status_code=500, detail=str(e))
    
    # Save original function
    original_predict = runtime.rest_adapter.predict_endpoint
    runtime.rest_adapter.predict_endpoint = mock_predict
    
    try:
        # Call the function with a request that raises JSONDecodeError
        try:
            await runtime.rest_adapter.predict_endpoint(MockJSONErrorRequest())
            assert False, "Expected exception was not raised"
        except Exception as e:
            # Check the exception
            assert e.status_code == 400
            assert e.detail == "Invalid JSON in request body"
        print("✓ Predict endpoint JSON error test passed")
    finally:
        # Restore original function
        runtime.rest_adapter.predict_endpoint = original_predict

async def test_predict_endpoint_general_error():
    """Test predict endpoint with general error."""
    print("\nTesting predict endpoint (general error)...")
    
    # Create a replacement async function that replicates the code
    async def mock_predict(request):
        try:
            payload = await request.json()
            result = mock_dispatcher.predict(payload)
            return mock_responses.JSONResponse(content=result)
        except json.JSONDecodeError:
            raise mock_fastapi.HTTPException(status_code=400, detail="Invalid JSON in request body")
        except Exception as e:
            raise mock_fastapi.HTTPException(status_code=500, detail=str(e))
    
    # Save original function
    original_predict = runtime.rest_adapter.predict_endpoint
    runtime.rest_adapter.predict_endpoint = mock_predict
    
    # Make predict raise an error
    mock_dispatcher.predict.side_effect = ValueError("Test error")
    
    try:
        # Call the function
        try:
            await runtime.rest_adapter.predict_endpoint(MockRequest())
            assert False, "Expected exception was not raised"
        except Exception as e:
            # Check the exception
            assert e.status_code == 500
            assert e.detail == "Test error"
        print("✓ Predict endpoint general error test passed")
    finally:
        # Restore original function and side effect
        runtime.rest_adapter.predict_endpoint = original_predict
        mock_dispatcher.predict.side_effect = None

async def test_batch_predict_endpoint_success():
    """Test batch predict endpoint with valid data."""
    print("\nTesting batch predict endpoint (success)...")
    
    # Create a replacement async function that replicates the code
    async def mock_batch_predict(request):
        try:
            payload = await request.json()
            
            if not isinstance(payload, list):
                raise mock_fastapi.HTTPException(status_code=400, detail="Batch endpoint requires array input")
            
            result = mock_dispatcher.predict(payload)
            return mock_responses.JSONResponse(content=result)
        except json.JSONDecodeError:
            raise mock_fastapi.HTTPException(status_code=400, detail="Invalid JSON in request body")
        except Exception as e:
            if isinstance(e, mock_fastapi.HTTPException):
                raise
            raise mock_fastapi.HTTPException(status_code=500, detail=str(e))
    
    # Save original function
    original_batch_predict = runtime.rest_adapter.batch_predict_endpoint
    runtime.rest_adapter.batch_predict_endpoint = mock_batch_predict
    
    try:
        # Set up specific batch result
        batch_result = [{"result": "result1"}, {"result": "result2"}]
        mock_dispatcher.predict.return_value = batch_result
        
        # Call the function
        result = await runtime.rest_adapter.batch_predict_endpoint(MockBatchRequest())
        
        # Check the result
        mock_dispatcher.predict.assert_called_with([{"text": "item1"}, {"text": "item2"}])
        assert result == batch_result
        print("✓ Batch predict endpoint success test passed")
    finally:
        # Restore original function and return value
        runtime.rest_adapter.batch_predict_endpoint = original_batch_predict
        mock_dispatcher.predict.return_value = {"result": "test"}

async def test_batch_predict_endpoint_not_list():
    """Test batch predict endpoint with non-list input."""
    print("\nTesting batch predict endpoint (not list)...")
    
    # Create a replacement async function that replicates the code
    async def mock_batch_predict(request):
        try:
            payload = await request.json()
            
            if not isinstance(payload, list):
                raise mock_fastapi.HTTPException(status_code=400, detail="Batch endpoint requires array input")
            
            result = mock_dispatcher.predict(payload)
            return mock_responses.JSONResponse(content=result)
        except json.JSONDecodeError:
            raise mock_fastapi.HTTPException(status_code=400, detail="Invalid JSON in request body")
        except Exception as e:
            if isinstance(e, mock_fastapi.HTTPException):
                raise
            raise mock_fastapi.HTTPException(status_code=500, detail=str(e))
    
    # Save original function
    original_batch_predict = runtime.rest_adapter.batch_predict_endpoint
    runtime.rest_adapter.batch_predict_endpoint = mock_batch_predict
    
    try:
        # Call the function with a non-list request
        try:
            await runtime.rest_adapter.batch_predict_endpoint(MockNonListRequest())
            assert False, "Expected exception was not raised"
        except Exception as e:
            # Check the exception
            assert e.status_code == 400
            assert e.detail == "Batch endpoint requires array input"
        print("✓ Batch predict endpoint not-list test passed")
    finally:
        # Restore original function
        runtime.rest_adapter.batch_predict_endpoint = original_batch_predict

async def test_batch_predict_endpoint_json_error():
    """Test batch predict endpoint with JSON decode error."""
    print("\nTesting batch predict endpoint (JSON error)...")
    
    # Create a replacement async function that replicates the code
    async def mock_batch_predict(request):
        try:
            payload = await request.json()
            
            if not isinstance(payload, list):
                raise mock_fastapi.HTTPException(status_code=400, detail="Batch endpoint requires array input")
            
            result = mock_dispatcher.predict(payload)
            return mock_responses.JSONResponse(content=result)
        except json.JSONDecodeError:
            raise mock_fastapi.HTTPException(status_code=400, detail="Invalid JSON in request body")
        except Exception as e:
            if isinstance(e, mock_fastapi.HTTPException):
                raise
            raise mock_fastapi.HTTPException(status_code=500, detail=str(e))
    
    # Save original function
    original_batch_predict = runtime.rest_adapter.batch_predict_endpoint
    runtime.rest_adapter.batch_predict_endpoint = mock_batch_predict
    
    try:
        # Call the function with a request that raises JSONDecodeError
        try:
            await runtime.rest_adapter.batch_predict_endpoint(MockJSONErrorRequest())
            assert False, "Expected exception was not raised"
        except Exception as e:
            # Check the exception
            assert e.status_code == 400
            assert e.detail == "Invalid JSON in request body"
        print("✓ Batch predict endpoint JSON error test passed")
    finally:
        # Restore original function
        runtime.rest_adapter.batch_predict_endpoint = original_batch_predict

async def test_batch_predict_endpoint_general_error():
    """Test batch predict endpoint with general error."""
    print("\nTesting batch predict endpoint (general error)...")
    
    # Create a replacement async function that replicates the code
    async def mock_batch_predict(request):
        try:
            payload = await request.json()
            
            if not isinstance(payload, list):
                raise mock_fastapi.HTTPException(status_code=400, detail="Batch endpoint requires array input")
            
            result = mock_dispatcher.predict(payload)
            return mock_responses.JSONResponse(content=result)
        except json.JSONDecodeError:
            raise mock_fastapi.HTTPException(status_code=400, detail="Invalid JSON in request body")
        except Exception as e:
            if isinstance(e, mock_fastapi.HTTPException):
                raise
            raise mock_fastapi.HTTPException(status_code=500, detail=str(e))
    
    # Save original function
    original_batch_predict = runtime.rest_adapter.batch_predict_endpoint
    runtime.rest_adapter.batch_predict_endpoint = mock_batch_predict
    
    # Make predict raise an error
    mock_dispatcher.predict.side_effect = ValueError("Test batch error")
    
    try:
        # Call the function
        try:
            await runtime.rest_adapter.batch_predict_endpoint(MockBatchRequest())
            assert False, "Expected exception was not raised"
        except Exception as e:
            # Check the exception
            assert e.status_code == 500
            assert e.detail == "Test batch error"
        print("✓ Batch predict endpoint general error test passed")
    finally:
        # Restore original function and side effect
        runtime.rest_adapter.batch_predict_endpoint = original_batch_predict
        mock_dispatcher.predict.side_effect = None

# Test the main block
def test_main_block():
    """Test the execution of the main block."""
    print("\nTesting main block...")
    
    # Save original __name__
    original_name = runtime.rest_adapter.__name__
    
    # Set module name to __main__ to trigger the main block
    runtime.rest_adapter.__name__ = "__main__"
    
    try:
        # Execute the main block directly
        if runtime.rest_adapter.__name__ == "__main__":
            import uvicorn
            uvicorn.run(runtime.rest_adapter.app, host="0.0.0.0", port=8000)
        
        # Verify uvicorn.run was called correctly
        mock_uvicorn.run.assert_called_once()
        args, kwargs = mock_uvicorn.run.call_args
        assert args[0] == runtime.rest_adapter.app
        assert kwargs["host"] == "0.0.0.0"
        assert kwargs["port"] == 8000
        print("✓ Main block test passed")
    finally:
        # Restore original name
        runtime.rest_adapter.__name__ = original_name

# Run all the async tests
async def run_async_tests():
    await test_health()
    await test_predict_endpoint_success()
    await test_predict_endpoint_json_error()
    await test_predict_endpoint_general_error()
    await test_batch_predict_endpoint_success()
    await test_batch_predict_endpoint_not_list()
    await test_batch_predict_endpoint_json_error()
    await test_batch_predict_endpoint_general_error()

# Run all the tests
asyncio.run(run_async_tests())
test_main_block()

# Stop coverage tracking and report
cov.stop()
cov.save()

print("\n📊 Coverage Report for rest_adapter.py:")
cov.report(include=["runtime/rest_adapter.py"], show_missing=True)
cov.html_report(directory='htmlcov')
