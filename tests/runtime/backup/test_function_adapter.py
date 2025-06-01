"""
Tests for the Azure Function adapter module.
"""
import json
import pytest
from unittest.mock import patch, MagicMock
from runtime.function_adapter import AzureFunctionAdapter


class TestAzureFunctionAdapter:
    """Test class for Azure Function adapter."""
    
    def test_init_method(self):
        """Test initialization method."""
        # Should not raise any exceptions
        AzureFunctionAdapter.init()
        
    def test_main_with_json_body(self):
        """Test main method with JSON body."""
        # Mock Azure Functions request
        mock_req = MagicMock()
        mock_req.get_json.return_value = {"text": "test input"}
        
        with patch('runtime.function_adapter.predict') as mock_predict:
            mock_predict.return_value = {"result": "processed"}
            
            result = AzureFunctionAdapter.main(mock_req)
            
            mock_predict.assert_called_once_with({"text": "test input"})
            assert result.status_code == 200
            
            # Parse response body
            response_body = json.loads(result.get_body())
            assert response_body == {"result": "processed"}
            
    def test_main_with_string_body(self):
        """Test main method with string body."""
        mock_req = MagicMock()
        mock_req.get_json.side_effect = ValueError("Not JSON")
        mock_req.get_body.return_value = b"test string input"
        
        with patch('runtime.function_adapter.predict') as mock_predict:
            mock_predict.return_value = {"result": "processed string"}
            
            result = AzureFunctionAdapter.main(mock_req)
            
            mock_predict.assert_called_once_with("test string input")
            assert result.status_code == 200
            
    def test_main_with_empty_body(self):
        """Test main method with empty body."""
        mock_req = MagicMock()
        mock_req.get_json.side_effect = ValueError("Not JSON")
        mock_req.get_body.return_value = b""
        
        result = AzureFunctionAdapter.main(mock_req)
        
        assert result.status_code == 400
        response_body = json.loads(result.get_body())
        assert "error" in response_body
        assert "No input data provided" in response_body["error"]
        
    def test_main_processing_error(self):
        """Test main method when processing raises an error."""
        mock_req = MagicMock()
        mock_req.get_json.return_value = {"text": "test input"}
        
        with patch('runtime.function_adapter.predict') as mock_predict:
            mock_predict.side_effect = Exception("Processing failed")
            
            result = AzureFunctionAdapter.main(mock_req)
            
            assert result.status_code == 500
            response_body = json.loads(result.get_body())
            assert "error" in response_body
            assert "Processing failed" in response_body["error"]
            
    def test_main_with_batch_input(self):
        """Test main method with batch input."""
        mock_req = MagicMock()
        mock_req.get_json.return_value = [
            {"text": "input 1"},
            {"text": "input 2"}
        ]
        
        with patch('runtime.function_adapter.predict') as mock_predict:
            mock_predict.return_value = [
                {"result": "processed 1"},
                {"result": "processed 2"}
            ]
            
            result = AzureFunctionAdapter.main(mock_req)
            
            mock_predict.assert_called_once_with([
                {"text": "input 1"},
                {"text": "input 2"}
            ])
            assert result.status_code == 200
            
            response_body = json.loads(result.get_body())
            assert len(response_body) == 2
            
    @patch('runtime.function_adapter.logger')
    def test_init_logging(self, mock_logger):
        """Test logging in init method."""
        AzureFunctionAdapter.init()
        mock_logger.info.assert_called_with("Initializing Azure Function adapter")
        
    @patch('runtime.function_adapter.logger')
    def test_main_logging_success(self, mock_logger):
        """Test logging in successful main execution."""
        mock_req = MagicMock()
        mock_req.get_json.return_value = {"text": "test"}
        
        with patch('runtime.function_adapter.predict') as mock_predict:
            mock_predict.return_value = {"result": "test"}
            
            AzureFunctionAdapter.main(mock_req)
            
            # Check that info logging occurred
            mock_logger.info.assert_any_call("Processing request in Azure Function context")
            mock_logger.info.assert_any_call("Successfully processed request")
            
    @patch('runtime.function_adapter.logger')
    def test_main_logging_error(self, mock_logger):
        """Test error logging in main method."""
        mock_req = MagicMock()
        mock_req.get_json.return_value = {"text": "test"}
        
        with patch('runtime.function_adapter.predict') as mock_predict:
            mock_predict.side_effect = Exception("Test error")
            
            AzureFunctionAdapter.main(mock_req)
            
            mock_logger.error.assert_called()
            args = mock_logger.error.call_args[0]
            assert "Error processing request" in args[0]


class TestAzureFunctionAdapterRequestParsing:
    """Test request parsing functionality."""
    
    def test_parse_json_request(self):
        """Test parsing valid JSON request."""
        mock_req = MagicMock()
        mock_req.get_json.return_value = {"key": "value"}
        
        with patch('runtime.function_adapter.predict') as mock_predict:
            mock_predict.return_value = {"result": "test"}
            
            AzureFunctionAdapter.main(mock_req)
            
            mock_predict.assert_called_once_with({"key": "value"})
            
    def test_parse_malformed_json(self):
        """Test handling of malformed JSON."""
        mock_req = MagicMock()
        mock_req.get_json.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)
        mock_req.get_body.return_value = b'{"invalid": json}'
        
        result = AzureFunctionAdapter.main(mock_req)
        
        # Should fall back to string processing
        assert result.status_code in [200, 500]  # Depends on predict function behavior
        
    def test_parse_binary_data(self):
        """Test handling of binary data."""
        mock_req = MagicMock()
        mock_req.get_json.side_effect = ValueError("Not JSON")
        mock_req.get_body.return_value = b'\x00\x01\x02binary data'
        
        with patch('runtime.function_adapter.predict') as mock_predict:
            # Predict should handle decode errors gracefully
            mock_predict.side_effect = UnicodeDecodeError("utf-8", b"", 0, 1, "invalid")
            
            result = AzureFunctionAdapter.main(mock_req)
            
            assert result.status_code == 500
            
    def test_parse_large_request(self):
        """Test handling of large requests."""
        large_data = {"data": "x" * 10000}  # Large payload
        
        mock_req = MagicMock()
        mock_req.get_json.return_value = large_data
        
        with patch('runtime.function_adapter.predict') as mock_predict:
            mock_predict.return_value = {"processed": True}
            
            result = AzureFunctionAdapter.main(mock_req)
            
            mock_predict.assert_called_once_with(large_data)
            assert result.status_code == 200


class TestAzureFunctionAdapterResponseFormatting:
    """Test response formatting functionality."""
    
    def test_json_response_format(self):
        """Test that responses are properly formatted as JSON."""
        mock_req = MagicMock()
        mock_req.get_json.return_value = {"input": "test"}
        
        with patch('runtime.function_adapter.predict') as mock_predict:
            mock_predict.return_value = {"output": "result", "metadata": {"count": 1}}
            
            result = AzureFunctionAdapter.main(mock_req)
            
            assert result.status_code == 200
            assert result.headers["Content-Type"] == "application/json"
            
            # Verify JSON is valid
            response_data = json.loads(result.get_body())
            assert response_data["output"] == "result"
            assert response_data["metadata"]["count"] == 1
            
    def test_error_response_format(self):
        """Test error response formatting."""
        mock_req = MagicMock()
        mock_req.get_json.return_value = {"input": "test"}
        
        with patch('runtime.function_adapter.predict') as mock_predict:
            mock_predict.side_effect = ValueError("Invalid input")
            
            result = AzureFunctionAdapter.main(mock_req)
            
            assert result.status_code == 500
            response_data = json.loads(result.get_body())
            assert "error" in response_data
            assert "Invalid input" in response_data["error"]
            
    def test_response_headers(self):
        """Test that proper headers are set on responses."""
        mock_req = MagicMock()
        mock_req.get_json.return_value = {"test": "data"}
        
        with patch('runtime.function_adapter.predict') as mock_predict:
            mock_predict.return_value = {"result": "success"}
            
            result = AzureFunctionAdapter.main(mock_req)
            
            assert result.headers["Content-Type"] == "application/json"
            # Could test for additional headers like CORS if implemented


class TestAzureFunctionAdapterIntegration:
    """Integration tests for Azure Function adapter."""
    
    def test_adapter_interface_compliance(self):
        """Test that adapter complies with expected interface."""
        assert hasattr(AzureFunctionAdapter, 'init')
        assert hasattr(AzureFunctionAdapter, 'main')
        assert callable(AzureFunctionAdapter.init)
        assert callable(AzureFunctionAdapter.main)
        
    def test_adapter_static_methods(self):
        """Test that adapter methods work as static methods."""
        # Should work without instantiation
        AzureFunctionAdapter.init()
        
        mock_req = MagicMock()
        mock_req.get_json.return_value = {"test": "data"}
        
        with patch('runtime.function_adapter.predict') as mock_predict:
            mock_predict.return_value = {"result": "test"}
            result = AzureFunctionAdapter.main(mock_req)
            assert result.status_code == 200
