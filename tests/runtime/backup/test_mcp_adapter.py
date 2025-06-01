"""
Tests for the MCP (Model Context Protocol) adapter module.
"""
import pytest
import json
from unittest.mock import patch, MagicMock, AsyncMock
from runtime.mcp_adapter import MCPAdapter


class TestMCPAdapter:
    """Test class for MCP adapter."""
    
    def test_init_method(self):
        """Test initialization method."""
        # Should not raise any exceptions
        MCPAdapter.init()
        
    @pytest.mark.asyncio
    async def test_handle_call_success(self):
        """Test successful handle_call method."""
        with patch('runtime.mcp_adapter.predict') as mock_predict:
            mock_predict.return_value = {"result": "processed"}
            
            call_data = {
                "method": "predict",
                "params": {"text": "test input"}
            }
            
            result = await MCPAdapter.handle_call(call_data)
            
            mock_predict.assert_called_once_with({"text": "test input"})
            assert result == {"result": "processed"}
            
    @pytest.mark.asyncio
    async def test_handle_call_with_batch(self):
        """Test handle_call method with batch data."""
        with patch('runtime.mcp_adapter.predict') as mock_predict:
            mock_predict.return_value = [
                {"result": "processed1"},
                {"result": "processed2"}
            ]
            
            call_data = {
                "method": "predict",
                "params": [
                    {"text": "input 1"},
                    {"text": "input 2"}
                ]
            }
            
            result = await MCPAdapter.handle_call(call_data)
            
            mock_predict.assert_called_once_with([
                {"text": "input 1"},
                {"text": "input 2"}
            ])
            assert len(result) == 2
            
    @pytest.mark.asyncio
    async def test_handle_call_unsupported_method(self):
        """Test handle_call with unsupported method."""
        call_data = {
            "method": "unsupported_method",
            "params": {"text": "test"}
        }
        
        with pytest.raises(ValueError) as exc_info:
            await MCPAdapter.handle_call(call_data)
            
        assert "Unsupported method" in str(exc_info.value)
        
    @pytest.mark.asyncio
    async def test_handle_call_missing_method(self):
        """Test handle_call with missing method."""
        call_data = {
            "params": {"text": "test"}
        }
        
        with pytest.raises(KeyError):
            await MCPAdapter.handle_call(call_data)
            
    @pytest.mark.asyncio
    async def test_handle_call_processing_error(self):
        """Test handle_call when predict raises an error."""
        with patch('runtime.mcp_adapter.predict') as mock_predict:
            mock_predict.side_effect = Exception("Processing failed")
            
            call_data = {
                "method": "predict",
                "params": {"text": "test"}
            }
            
            with pytest.raises(Exception) as exc_info:
                await MCPAdapter.handle_call(call_data)
                
            assert "Processing failed" in str(exc_info.value)
            
    @pytest.mark.asyncio
    async def test_handle_call_empty_params(self):
        """Test handle_call with empty parameters."""
        with patch('runtime.mcp_adapter.predict') as mock_predict:
            mock_predict.return_value = {"result": "empty_processed"}
            
            call_data = {
                "method": "predict",
                "params": {}
            }
            
            result = await MCPAdapter.handle_call(call_data)
            
            mock_predict.assert_called_once_with({})
            assert result == {"result": "empty_processed"}
            
    @pytest.mark.asyncio
    async def test_handle_call_none_params(self):
        """Test handle_call with None parameters."""
        with patch('runtime.mcp_adapter.predict') as mock_predict:
            mock_predict.return_value = {"result": "none_processed"}
            
            call_data = {
                "method": "predict",
                "params": None
            }
            
            result = await MCPAdapter.handle_call(call_data)
            
            mock_predict.assert_called_once_with(None)
            assert result == {"result": "none_processed"}


class TestMCPAdapterLogging:
    """Test logging functionality in MCP adapter."""
    
    @patch('runtime.mcp_adapter.logger')
    def test_init_logging(self, mock_logger):
        """Test logging in init method."""
        MCPAdapter.init()
        mock_logger.info.assert_called_with("Initializing MCP adapter")
        
    @pytest.mark.asyncio
    @patch('runtime.mcp_adapter.logger')
    async def test_handle_call_logging_success(self, mock_logger):
        """Test logging in successful handle_call."""
        with patch('runtime.mcp_adapter.predict') as mock_predict:
            mock_predict.return_value = {"result": "test"}
            
            call_data = {
                "method": "predict",
                "params": {"text": "test"}
            }
            
            await MCPAdapter.handle_call(call_data)
            
            mock_logger.info.assert_any_call("Processing MCP call: predict")
            mock_logger.info.assert_any_call("Successfully processed MCP call")
            
    @pytest.mark.asyncio
    @patch('runtime.mcp_adapter.logger')
    async def test_handle_call_logging_error(self, mock_logger):
        """Test error logging in handle_call."""
        with patch('runtime.mcp_adapter.predict') as mock_predict:
            mock_predict.side_effect = Exception("Test error")
            
            call_data = {
                "method": "predict",
                "params": {"text": "test"}
            }
            
            with pytest.raises(Exception):
                await MCPAdapter.handle_call(call_data)
                
            mock_logger.error.assert_called()
            args = mock_logger.error.call_args[0]
            assert "Error processing MCP call" in args[0]


class TestMCPAdapterMethodValidation:
    """Test method validation in MCP adapter."""
    
    @pytest.mark.asyncio
    async def test_predict_method_supported(self):
        """Test that predict method is supported."""
        with patch('runtime.mcp_adapter.predict') as mock_predict:
            mock_predict.return_value = {"result": "test"}
            
            call_data = {
                "method": "predict",
                "params": {"text": "test"}
            }
            
            # Should not raise an exception
            result = await MCPAdapter.handle_call(call_data)
            assert result == {"result": "test"}
            
    @pytest.mark.asyncio
    async def test_health_method_supported(self):
        """Test that health method is supported."""
        with patch('runtime.mcp_adapter.health_check') as mock_health:
            mock_health.return_value = {"status": "healthy"}
            
            call_data = {
                "method": "health",
                "params": {}
            }
            
            result = await MCPAdapter.handle_call(call_data)
            mock_health.assert_called_once()
            assert result == {"status": "healthy"}
            
    @pytest.mark.asyncio
    async def test_invalid_method_rejected(self):
        """Test that invalid methods are rejected."""
        invalid_methods = [
            "invalid_method",
            "execute",
            "delete",
            "admin",
            "",
            123,
            None
        ]
        
        for method in invalid_methods:
            call_data = {
                "method": method,
                "params": {"text": "test"}
            }
            
            with pytest.raises((ValueError, TypeError, AttributeError)):
                await MCPAdapter.handle_call(call_data)


class TestMCPAdapterDataTypes:
    """Test data type handling in MCP adapter."""
    
    @pytest.mark.asyncio
    async def test_string_params(self):
        """Test handling of string parameters."""
        with patch('runtime.mcp_adapter.predict') as mock_predict:
            mock_predict.return_value = {"result": "string_processed"}
            
            call_data = {
                "method": "predict",
                "params": "test string"
            }
            
            result = await MCPAdapter.handle_call(call_data)
            
            mock_predict.assert_called_once_with("test string")
            assert result == {"result": "string_processed"}
            
    @pytest.mark.asyncio
    async def test_list_params(self):
        """Test handling of list parameters."""
        with patch('runtime.mcp_adapter.predict') as mock_predict:
            mock_predict.return_value = [{"result": "item1"}, {"result": "item2"}]
            
            call_data = {
                "method": "predict",
                "params": [{"text": "item1"}, {"text": "item2"}]
            }
            
            result = await MCPAdapter.handle_call(call_data)
            
            mock_predict.assert_called_once_with([{"text": "item1"}, {"text": "item2"}])
            assert len(result) == 2
            
    @pytest.mark.asyncio
    async def test_complex_nested_params(self):
        """Test handling of complex nested parameters."""
        complex_params = {
            "metadata": {"id": 1, "version": "1.0"},
            "data": {
                "inputs": [
                    {"text": "input1", "config": {"param": "value1"}},
                    {"text": "input2", "config": {"param": "value2"}}
                ],
                "options": {"batch_size": 10, "timeout": 30}
            }
        }
        
        with patch('runtime.mcp_adapter.predict') as mock_predict:
            mock_predict.return_value = {"processed": True, "count": 2}
            
            call_data = {
                "method": "predict",
                "params": complex_params
            }
            
            result = await MCPAdapter.handle_call(call_data)
            
            mock_predict.assert_called_once_with(complex_params)
            assert result["processed"] is True
            assert result["count"] == 2


class TestMCPAdapterIntegration:
    """Integration tests for MCP adapter."""
    
    def test_adapter_interface_compliance(self):
        """Test that adapter complies with expected interface."""
        assert hasattr(MCPAdapter, 'init')
        assert hasattr(MCPAdapter, 'handle_call')
        assert callable(MCPAdapter.init)
        assert callable(MCPAdapter.handle_call)
        
    def test_adapter_static_methods(self):
        """Test that adapter methods work as static methods."""
        # Should work without instantiation
        MCPAdapter.init()
        
        # handle_call is async, so we need to test it differently
        import asyncio
        
        async def test_async():
            with patch('runtime.mcp_adapter.predict') as mock_predict:
                mock_predict.return_value = {"result": "test"}
                
                call_data = {
                    "method": "predict",
                    "params": {"text": "test"}
                }
                
                result = await MCPAdapter.handle_call(call_data)
                return result
                
        # This would need to be run in an async context
        # For now, just verify the method exists and is callable
        assert callable(MCPAdapter.handle_call)
        
    @pytest.mark.asyncio
    async def test_adapter_with_dispatcher_integration(self):
        """Test adapter integration with the dispatcher."""
        # This test would verify that the MCP adapter properly
        # integrates with the dispatcher's predict function
        with patch('runtime.mcp_adapter.predict') as mock_predict:
            mock_predict.return_value = {"integration": "success"}
            
            call_data = {
                "method": "predict",
                "params": {"text": "integration test"}
            }
            
            result = await MCPAdapter.handle_call(call_data)
            
            # Verify the predict function was called correctly
            mock_predict.assert_called_once_with({"text": "integration test"})
            assert result["integration"] == "success"


class TestMCPAdapterErrorHandling:
    """Test comprehensive error handling in MCP adapter."""
    
    @pytest.mark.asyncio
    async def test_malformed_call_data(self):
        """Test handling of malformed call data."""
        malformed_data_cases = [
            {},  # Missing method
            {"method": "predict"},  # Missing params
            {"params": {"text": "test"}},  # Missing method
            None,  # None data
            "string_data",  # String instead of dict
            123,  # Number instead of dict
        ]
        
        for case in malformed_data_cases:
            with pytest.raises((KeyError, TypeError, AttributeError)):
                await MCPAdapter.handle_call(case)
                
    @pytest.mark.asyncio
    async def test_timeout_handling(self):
        """Test handling of processing timeouts."""
        import asyncio
        
        async def slow_predict(data):
            await asyncio.sleep(0.1)  # Simulate slow processing
            return {"result": "slow"}
        
        with patch('runtime.mcp_adapter.predict', side_effect=slow_predict):
            call_data = {
                "method": "predict",
                "params": {"text": "test"}
            }
            
            # Should complete without timeout issues
            result = await MCPAdapter.handle_call(call_data)
            assert result == {"result": "slow"}
            
    @pytest.mark.asyncio
    async def test_large_payload_handling(self):
        """Test handling of large payloads."""
        large_payload = {"text": "x" * 10000}  # Large text
        
        with patch('runtime.mcp_adapter.predict') as mock_predict:
            mock_predict.return_value = {"result": "processed_large"}
            
            call_data = {
                "method": "predict",
                "params": large_payload
            }
            
            result = await MCPAdapter.handle_call(call_data)
            
            mock_predict.assert_called_once_with(large_payload)
            assert result == {"result": "processed_large"}
