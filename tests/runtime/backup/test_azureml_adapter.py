"""
Tests for the Azure ML adapter module.
"""
import pytest
from unittest.mock import patch, MagicMock
from runtime.azureml_adapter import AzureMLAdapter


class TestAzureMLAdapter:
    """Test class for Azure ML adapter."""
    
    def test_init_method(self):
        """Test initialization method."""
        # Should not raise any exceptions
        AzureMLAdapter.init()
        
    @patch('runtime.azureml_adapter.predict')
    def test_run_single_item(self, mock_predict):
        """Test run method with single item."""
        mock_predict.return_value = {"result": "processed"}
        
        input_data = {"text": "test input"}
        result = AzureMLAdapter.run(input_data)
        
        mock_predict.assert_called_once_with(input_data)
        assert result == {"result": "processed"}
        
    @patch('runtime.azureml_adapter.predict')
    def test_run_batch_items(self, mock_predict):
        """Test run method with batch of items."""
        mock_predict.return_value = [
            {"result": "processed1"},
            {"result": "processed2"}
        ]
        
        input_data = [
            {"text": "test input 1"},
            {"text": "test input 2"}
        ]
        result = AzureMLAdapter.run(input_data)
        
        mock_predict.assert_called_once_with(input_data)
        assert len(result) == 2
        assert result[0] == {"result": "processed1"}
        assert result[1] == {"result": "processed2"}
        
    @patch('runtime.azureml_adapter.predict')
    def test_run_error_handling(self, mock_predict):
        """Test error handling in run method."""
        mock_predict.side_effect = Exception("Processing error")
        
        with pytest.raises(Exception) as exc_info:
            AzureMLAdapter.run({"text": "test"})
            
        assert "Processing error" in str(exc_info.value)
        
    @patch('runtime.azureml_adapter.logger')
    def test_init_logging(self, mock_logger):
        """Test logging in init method."""
        AzureMLAdapter.init()
        mock_logger.info.assert_called_with("Initializing Azure ML adapter")
        
    @patch('runtime.azureml_adapter.logger')
    @patch('runtime.azureml_adapter.predict')
    def test_run_logging(self, mock_predict, mock_logger):
        """Test logging in run method."""
        mock_predict.return_value = {"result": "test"}
        
        AzureMLAdapter.run({"text": "test"})
        
        mock_logger.info.assert_called_with("Processing request in Azure ML context")
        
    @patch('runtime.azureml_adapter.predict')
    def test_run_with_none_input(self, mock_predict):
        """Test run method with None input."""
        mock_predict.return_value = None
        
        result = AzureMLAdapter.run(None)
        
        mock_predict.assert_called_once_with(None)
        assert result is None
        
    @patch('runtime.azureml_adapter.predict')
    def test_run_with_empty_list(self, mock_predict):
        """Test run method with empty list."""
        mock_predict.return_value = []
        
        result = AzureMLAdapter.run([])
        
        mock_predict.assert_called_once_with([])
        assert result == []
        
    @patch('runtime.azureml_adapter.predict')
    def test_run_preserves_data_types(self, mock_predict):
        """Test that run method preserves various data types."""
        test_cases = [
            "string input",
            {"dict": "input"},
            [1, 2, 3],
            123,
            True,
            None
        ]
        
        for test_input in test_cases:
            mock_predict.return_value = f"processed_{test_input}"
            result = AzureMLAdapter.run(test_input)
            
            mock_predict.assert_called_with(test_input)
            assert result == f"processed_{test_input}"


class TestAzureMLAdapterEdgeCases:
    """Test edge cases for Azure ML adapter."""
    
    @patch('runtime.azureml_adapter.predict')
    def test_large_batch_processing(self, mock_predict):
        """Test processing of large batches."""
        large_batch = [{"text": f"item_{i}"} for i in range(1000)]
        mock_predict.return_value = [{"result": f"processed_{i}"} for i in range(1000)]
        
        result = AzureMLAdapter.run(large_batch)
        
        mock_predict.assert_called_once_with(large_batch)
        assert len(result) == 1000
        
    @patch('runtime.azureml_adapter.predict')
    def test_nested_data_structures(self, mock_predict):
        """Test handling of nested data structures."""
        complex_input = {
            "metadata": {"id": 1, "type": "test"},
            "data": [
                {"text": "item 1", "config": {"param": "value"}},
                {"text": "item 2", "config": {"param": "value2"}}
            ]
        }
        mock_predict.return_value = {"processed": True, "items": 2}
        
        result = AzureMLAdapter.run(complex_input)
        
        mock_predict.assert_called_once_with(complex_input)
        assert result["processed"] is True
        assert result["items"] == 2


class TestAzureMLAdapterIntegration:
    """Integration tests for Azure ML adapter."""
    
    def test_adapter_static_methods(self):
        """Test that adapter methods are static and can be called without instantiation."""
        # Should be able to call without creating instance
        AzureMLAdapter.init()
        
        # Mock predict to avoid import issues
        with patch('runtime.azureml_adapter.predict') as mock_predict:
            mock_predict.return_value = {"test": "result"}
            result = AzureMLAdapter.run({"input": "test"})
            assert result == {"test": "result"}
            
    def test_adapter_interface_compliance(self):
        """Test that adapter complies with expected interface."""
        # Check that required methods exist and are callable
        assert hasattr(AzureMLAdapter, 'init')
        assert hasattr(AzureMLAdapter, 'run')
        assert callable(AzureMLAdapter.init)
        assert callable(AzureMLAdapter.run)
