"""
Test coverage for the MCP adapter module.
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
    # Mock dispatcher.predict
    sys.modules['runtime.dispatcher'] = Mock()
    sys.modules['runtime.dispatcher'].predict = Mock(return_value={"result": "test_result"})


def teardown_module():
    """Clean up mocks after tests."""
    if 'runtime.mcp_adapter' in sys.modules:
        del sys.modules['runtime.mcp_adapter']


def test_mcp_adapter_initialization():
    """Test initialization of the MCP adapter."""
    # Import locally to get a fresh instance
    if 'runtime.mcp_adapter' in sys.modules:
        del sys.modules['runtime.mcp_adapter']
    
    # Set up mocks
    setup_module()
    
    # Import the module
    from runtime.mcp_adapter import MCPAdapter
    
    # Mock the logger
    logger_mock = MagicMock()
    
    with patch('runtime.mcp_adapter.logger', logger_mock):
        # Call the init method
        MCPAdapter.init()
        # Verify logger was called correctly
        logger_mock.info.assert_called_once_with("Initializing MCP adapter")


def test_mcp_adapter_handle_action_predict():
    """Test the handle_action method with predict action."""
    # Import locally to get a fresh instance
    if 'runtime.mcp_adapter' in sys.modules:
        del sys.modules['runtime.mcp_adapter']
    
    # Set up mocks
    setup_module()
    mock_predict = MagicMock(return_value={"result": "mocked_result"})
    sys.modules['runtime.dispatcher'].predict = mock_predict
    
    # Import the module
    from runtime.mcp_adapter import MCPAdapter
    
    # Mock the logger
    logger_mock = MagicMock()
    
    with patch('runtime.mcp_adapter.logger', logger_mock):
        # Test handle_action with predict action
        result = MCPAdapter.handle_action("predict", {"text": "test"})
        
        # Verify predict was called correctly
        mock_predict.assert_called_with({"text": "test"})
        
        # Verify result
        assert result == {
            "success": True,
            "result": {"result": "mocked_result"},
            "action": "predict"
        }
        
        # Verify logging
        logger_mock.info.assert_called_once_with("Processing MCP action: predict")


def test_mcp_adapter_handle_action_process():
    """Test the handle_action method with process action."""
    # Import locally to get a fresh instance
    if 'runtime.mcp_adapter' in sys.modules:
        del sys.modules['runtime.mcp_adapter']
    
    # Set up mocks
    setup_module()
    mock_predict = MagicMock(return_value={"result": "mocked_result"})
    sys.modules['runtime.dispatcher'].predict = mock_predict
    
    # Import the module
    from runtime.mcp_adapter import MCPAdapter
    
    # Mock the logger
    logger_mock = MagicMock()
    
    with patch('runtime.mcp_adapter.logger', logger_mock):
        # Test handle_action with process action
        result = MCPAdapter.handle_action("process", {"text": "test"})
        
        # Verify predict was called correctly
        mock_predict.assert_called_with({"text": "test"})
        
        # Verify result
        assert result == {
            "success": True,
            "result": {"result": "mocked_result"},
            "action": "process"
        }
        
        # Verify logging
        logger_mock.info.assert_called_once_with("Processing MCP action: process")


def test_mcp_adapter_handle_action_execute():
    """Test the handle_action method with execute action."""
    # Import locally to get a fresh instance
    if 'runtime.mcp_adapter' in sys.modules:
        del sys.modules['runtime.mcp_adapter']
    
    # Set up mocks
    setup_module()
    mock_predict = MagicMock(return_value={"result": "mocked_result"})
    sys.modules['runtime.dispatcher'].predict = mock_predict
    
    # Import the module
    from runtime.mcp_adapter import MCPAdapter
    
    # Mock the logger
    logger_mock = MagicMock()
    
    with patch('runtime.mcp_adapter.logger', logger_mock):
        # Test handle_action with execute action
        result = MCPAdapter.handle_action("execute", {"text": "test"})
        
        # Verify predict was called correctly
        mock_predict.assert_called_with({"text": "test"})
        
        # Verify result
        assert result == {
            "success": True,
            "result": {"result": "mocked_result"},
            "action": "execute"
        }
        
        # Verify logging
        logger_mock.info.assert_called_once_with("Processing MCP action: execute")


def test_mcp_adapter_handle_action_unknown():
    """Test the handle_action method with unknown action."""
    # Import locally to get a fresh instance
    if 'runtime.mcp_adapter' in sys.modules:
        del sys.modules['runtime.mcp_adapter']
    
    # Set up mocks
    setup_module()
    
    # Import the module
    from runtime.mcp_adapter import MCPAdapter
    
    # Mock the logger
    logger_mock = MagicMock()
    
    with patch('runtime.mcp_adapter.logger', logger_mock):
        # Test handle_action with unknown action
        result = MCPAdapter.handle_action("unknown", {"text": "test"})
        
        # Verify result
        assert result == {
            "success": False,
            "error": "Unknown action: unknown",
            "action": "unknown"
        }
        
        # Verify logging
        logger_mock.info.assert_called_once_with("Processing MCP action: unknown")


def test_mcp_adapter_handle_action_exception():
    """Test the handle_action method when an exception occurs."""
    # Import locally to get a fresh instance
    if 'runtime.mcp_adapter' in sys.modules:
        del sys.modules['runtime.mcp_adapter']
    
    # Set up mocks
    setup_module()
    mock_predict = MagicMock(side_effect=ValueError("Test error"))
    sys.modules['runtime.dispatcher'].predict = mock_predict
    
    # Import the module
    from runtime.mcp_adapter import MCPAdapter
    
    # Mock the logger
    logger_mock = MagicMock()
    
    with patch('runtime.mcp_adapter.logger', logger_mock):
        # Test handle_action with exception
        result = MCPAdapter.handle_action("predict", {"text": "test"})
        
        # Verify result
        assert result == {
            "success": False,
            "error": "Test error",
            "action": "predict"
        }
        
        # Verify logging
        logger_mock.info.assert_called_once_with("Processing MCP action: predict")
        logger_mock.error.assert_called_once_with("Error in MCP action predict: Test error")


def test_mcp_adapter_list_actions():
    """Test the list_actions method."""
    # Import locally to get a fresh instance
    if 'runtime.mcp_adapter' in sys.modules:
        del sys.modules['runtime.mcp_adapter']
    
    # Set up mocks
    setup_module()
    
    # Import the module
    from runtime.mcp_adapter import MCPAdapter
    
    # Test list_actions
    result = MCPAdapter.list_actions()
    
    # Verify result
    assert isinstance(result, list)
    assert len(result) == 2
    assert result[0]["name"] == "predict"
    assert result[1]["name"] == "process"


def test_handle_mcp_request_with_default():
    """Test the handle_mcp_request function with default action."""
    # Import locally to get a fresh instance
    if 'runtime.mcp_adapter' in sys.modules:
        del sys.modules['runtime.mcp_adapter']
    
    # Set up mocks
    setup_module()
    
    # Import the module
    from runtime.mcp_adapter import handle_mcp_request, MCPAdapter
    
    # Mock handle_action
    with patch.object(MCPAdapter, 'handle_action') as mock_handle_action:
        mock_handle_action.return_value = {"result": "mocked"}
        
        # Test handle_mcp_request with empty request
        result = handle_mcp_request({})
        
        # Verify handle_action was called with default values
        mock_handle_action.assert_called_with("predict", {})
        
        # Verify result
        assert result == {"result": "mocked"}


def test_handle_mcp_request_with_action():
    """Test the handle_mcp_request function with specified action."""
    # Import locally to get a fresh instance
    if 'runtime.mcp_adapter' in sys.modules:
        del sys.modules['runtime.mcp_adapter']
    
    # Set up mocks
    setup_module()
    
    # Import the module
    from runtime.mcp_adapter import handle_mcp_request, MCPAdapter
    
    # Mock handle_action
    with patch.object(MCPAdapter, 'handle_action') as mock_handle_action:
        mock_handle_action.return_value = {"result": "mocked"}
        
        # Test handle_mcp_request with action and params
        result = handle_mcp_request({
            "action": "process",
            "params": {"text": "test"}
        })
        
        # Verify handle_action was called with specified values
        mock_handle_action.assert_called_with("process", {"text": "test"})
        
        # Verify result
        assert result == {"result": "mocked"}
