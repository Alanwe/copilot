"""
Test suite for mcp_adapter.py module to achieve 100% test coverage.
"""
import os
import sys
import pytest
from unittest.mock import patch, MagicMock

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

#-----------------------------------------------------------------------------
# Tests for runtime/mcp_adapter.py
#-----------------------------------------------------------------------------
def test_mcp_adapter_init():
    """Test MCPAdapter.init()"""
    from runtime.mcp_adapter import MCPAdapter
    
    with patch('runtime.mcp_adapter.logger') as mock_logger:
        MCPAdapter.init()
        mock_logger.info.assert_called_with("Initializing MCP adapter")

def test_mcp_handle_action_predict():
    """Test MCPAdapter.handle_action() with predict action."""
    from runtime.mcp_adapter import MCPAdapter
    
    # Mock predict function
    with patch('runtime.mcp_adapter.predict', return_value={"result": "processed"}) as mock_predict:
        with patch('runtime.mcp_adapter.logger') as mock_logger:
            result = MCPAdapter.handle_action("predict", {"text": "test"})
            
            # Verify logging and predict calls
            mock_logger.info.assert_called_with("Processing MCP action: predict")
            mock_predict.assert_called_once_with({"text": "test"})
            
            # Check result format
            assert result["success"] is True
            assert result["action"] == "predict"
            assert result["result"] == {"result": "processed"}

def test_mcp_handle_action_process():
    """Test MCPAdapter.handle_action() with process action."""
    from runtime.mcp_adapter import MCPAdapter
    
    # Mock predict function
    with patch('runtime.mcp_adapter.predict', return_value={"result": "processed"}) as mock_predict:
        result = MCPAdapter.handle_action("process", {"text": "test"})
        
        # Check that predict was still called for 'process' action
        mock_predict.assert_called_once_with({"text": "test"})
        assert result["success"] is True
        assert result["action"] == "process"

def test_mcp_handle_action_execute():
    """Test MCPAdapter.handle_action() with execute action."""
    from runtime.mcp_adapter import MCPAdapter
    
    # Mock predict function
    with patch('runtime.mcp_adapter.predict', return_value={"result": "processed"}) as mock_predict:
        result = MCPAdapter.handle_action("execute", {"text": "test"})
        
        # Check that predict was still called for 'execute' action
        mock_predict.assert_called_once_with({"text": "test"})
        assert result["success"] is True
        assert result["action"] == "execute"

def test_mcp_handle_action_unknown():
    """Test MCPAdapter.handle_action() with unknown action."""
    from runtime.mcp_adapter import MCPAdapter
    
    # Mock predict function, should not be called
    with patch('runtime.mcp_adapter.predict') as mock_predict:
        result = MCPAdapter.handle_action("unknown", {"text": "test"})
        
        # Verify predict not called for unknown action
        mock_predict.assert_not_called()
        
        # Check error response
        assert result["success"] is False
        assert result["action"] == "unknown"
        assert "Unknown action" in result["error"]

def test_mcp_handle_action_exception():
    """Test MCPAdapter.handle_action() when predict raises exception."""
    from runtime.mcp_adapter import MCPAdapter
    
    # Mock predict function to raise exception
    with patch('runtime.mcp_adapter.predict', side_effect=ValueError("Test error")):
        with patch('runtime.mcp_adapter.logger') as mock_logger:
            result = MCPAdapter.handle_action("predict", {"text": "test"})
            
            # Verify error logging
            mock_logger.error.assert_called_once()
            assert "Test error" in mock_logger.error.call_args[0][0]
            
            # Check error response
            assert result["success"] is False
            assert result["action"] == "predict"
            assert result["error"] == "Test error"

def test_mcp_list_actions():
    """Test MCPAdapter.list_actions()"""
    from runtime.mcp_adapter import MCPAdapter
    
    actions = MCPAdapter.list_actions()
    
    # Check that the right actions are defined
    assert len(actions) == 2
    action_names = [action["name"] for action in actions]
    assert "predict" in action_names
    assert "process" in action_names
    
    # Check structure of first action
    predict_action = next(action for action in actions if action["name"] == "predict")
    assert "description" in predict_action
    assert "parameters" in predict_action

def test_handle_mcp_request_default():
    """Test handle_mcp_request() with default action (predict)."""
    from runtime.mcp_adapter import handle_mcp_request, MCPAdapter
    
    # Mock MCPAdapter.handle_action
    with patch.object(MCPAdapter, 'handle_action', return_value={"result": "ok"}) as mock_handle:
        # Test with no explicit action (should default to predict)
        result = handle_mcp_request({"params": {"text": "test"}})
        mock_handle.assert_called_once_with("predict", {"text": "test"})
        assert result == {"result": "ok"}

def test_handle_mcp_request_explicit():
    """Test handle_mcp_request() with explicit action."""
    from runtime.mcp_adapter import handle_mcp_request, MCPAdapter
    
    # Mock MCPAdapter.handle_action
    with patch.object(MCPAdapter, 'handle_action', return_value={"result": "ok"}) as mock_handle:
        # Test with explicit action
        result = handle_mcp_request({
            "action": "process",
            "params": {"text": "test"}
        })
        mock_handle.assert_called_once_with("process", {"text": "test"})
        assert result == {"result": "ok"}

def test_get_mcp_schema():
    """Test get_mcp_schema()"""
    from runtime.mcp_adapter import get_mcp_schema, MCPAdapter
    
    # Mock MCPAdapter.list_actions
    mock_actions = [{"name": "test_action"}]
    with patch.object(MCPAdapter, 'list_actions', return_value=mock_actions):
        schema = get_mcp_schema()
        
        # Check schema structure
        assert "name" in schema
        assert "version" in schema
        assert "description" in schema
        assert schema["actions"] == mock_actions

if __name__ == "__main__":
    # Run the tests manually
    pytest.main(["-v", "--cov=runtime.mcp_adapter", "--cov-report=term-missing", __file__])
