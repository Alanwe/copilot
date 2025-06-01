# filepath: /workspaces/copilot/tests/runtime/test_runtime_coverage.py
"""
Comprehensive test suite for achieving 100% test coverage on runtime modules.

This file creates tests for each runtime module:
- runtime/__init__.py
- runtime/azureml_adapter.py
- runtime/dispatcher.py
- runtime/function_adapter.py
- runtime/mcp_adapter.py
- runtime/rest_adapter.py

Usage:
    python -m pytest tests/runtime/test_runtime_coverage.py -v \\
    --cov=runtime --cov-report=term-missing
"""
import os
import sys
import json
import pytest
from unittest.mock import patch, MagicMock


# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__),
                                                '../..')))

# Mock classes for HTTP requests
class MockRequest:
    async def json(self):
        return {"text": "test data"}


class MockJSONErrorRequest:
    async def json(self):
        raise json.JSONDecodeError("Invalid JSON", "", 0)


class MockBatchRequest:
    async def json(self):
        return [{"text": "item1"}, {"text": "item2"}]


class MockNonListRequest:
    async def json(self):
        return {"not": "a list"}


class MockHTTPRequest:
    def __init__(self, body=None):
        self.body = body or b'{"text": "test data"}'

    def get_body(self):
        return self.body

    def get_json(self):
        return json.loads(self.body)


# Fixtures for different modules
@pytest.fixture(scope="module")
def mock_azure_functions():
    """Mock Azure Functions dependencies."""
    mock_func = MagicMock()

    # Mock HttpRequest
    mock_func.HttpRequest = MockHTTPRequest

    # Mock HttpResponse
    def mock_http_response(
        body, status_code=200, headers=None, mimetype="application/json"
    ):
        return {
            "body": body,
            "status_code": status_code,
            "headers": headers,
            "mimetype": mimetype,
        }

    mock_func.HttpResponse = MagicMock(side_effect=mock_http_response)

    with patch.dict(sys.modules, {'azure.functions': mock_func}):
        yield mock_func


def test_module_imports():
    """Test that all runtime modules can be imported."""
    # Import all modules
    import runtime
    import runtime.azureml_adapter
    import runtime.dispatcher
    import runtime.function_adapter
    import runtime.mcp_adapter
    import runtime.rest_adapter

    # Verify the modules are properly imported
    assert runtime.__version__ == "1.0.0"
    assert hasattr(runtime.azureml_adapter, "AzureMLAdapter")
    assert hasattr(runtime.dispatcher, "health_check")
    assert hasattr(runtime.function_adapter, "AzureFunctionAdapter")
    assert hasattr(runtime.mcp_adapter, "MCPAdapter")
    assert hasattr(runtime.rest_adapter, "ContainerAppAdapter")


def test_dispatcher_health_check():
    """Test the health check functionality."""
    from runtime.dispatcher import health_check

    result = health_check()
    assert "status" in result
    assert result["status"] == "healthy"


def test_azureml_adapter_init():
    """Test AzureML adapter initialization."""
    from runtime.azureml_adapter import AzureMLAdapter

    # Test initialization
    # Test initialization - just make sure it doesn't raise exceptions
    AzureMLAdapter.init()


def test_function_adapter_init():
    """Test Azure Function adapter initialization."""
    from runtime.function_adapter import AzureFunctionAdapter

    # Test initialization
    # Test initialization - just make sure it doesn't raise exceptions
    AzureFunctionAdapter.init()


def test_mcp_adapter_init():
    """Test MCP adapter initialization."""
    from runtime.mcp_adapter import MCPAdapter

    # Test initialization
    # Test initialization - just make sure it doesn't raise exceptions
    MCPAdapter.init()


def test_rest_adapter_init():
    """Test REST adapter initialization."""
    from runtime.rest_adapter import ContainerAppAdapter

    # Test initialization
    # Test initialization - just make sure it doesn't raise exceptions
    ContainerAppAdapter.init()


if __name__ == "__main__":
    # Run the tests manually
    pytest.main(["-v", "--cov=runtime", "--cov-report=term-missing", __file__])
