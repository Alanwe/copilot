"""
Test suite for azureml_adapter.py module to achieve 100% test coverage.
"""
import os
import sys
import pytest
from unittest.mock import patch, MagicMock

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

#-----------------------------------------------------------------------------
# Tests for runtime/azureml_adapter.py
#-----------------------------------------------------------------------------
def test_azureml_adapter_init():
    """Test AzureMLAdapter.init()"""
    from runtime.azureml_adapter import AzureMLAdapter
    
    with patch('runtime.azureml_adapter.logger') as mock_logger:
        AzureMLAdapter.init()
        mock_logger.info.assert_called_with("Initializing Azure ML adapter")

def test_azureml_adapter_run_online():
    """Test AzureMLAdapter.run() with online (single item) data."""
    from runtime.azureml_adapter import AzureMLAdapter
    
    # Mock predict function
    with patch('runtime.azureml_adapter.predict', return_value={"result": "online"}) as mock_predict:
        with patch('runtime.azureml_adapter.logger') as mock_logger:
            result = AzureMLAdapter.run({"data": "test"})
            
            # Verify logging and predict calls
            mock_logger.info.assert_any_call("Processing Azure ML request")
            mock_logger.info.assert_any_call("Processing online request")
            mock_predict.assert_called_once_with({"data": "test"})
            assert result == {"result": "online"}

def test_azureml_adapter_run_batch():
    """Test AzureMLAdapter.run() with batch data."""
    from runtime.azureml_adapter import AzureMLAdapter
    
    batch_data = [{"id": 1}, {"id": 2}]
    
    # Mock predict function
    with patch('runtime.azureml_adapter.predict', return_value=[{"result": 1}, {"result": 2}]) as mock_predict:
        with patch('runtime.azureml_adapter.logger') as mock_logger:
            result = AzureMLAdapter.run(batch_data)
            
            # Verify logging and predict calls
            mock_logger.info.assert_any_call("Processing Azure ML request")
            mock_logger.info.assert_any_call(f"Processing batch request with {len(batch_data)} items")
            mock_predict.assert_called_once_with(batch_data)
            assert result == [{"result": 1}, {"result": 2}]

def test_azureml_adapter_run_exception():
    """Test AzureMLAdapter.run() when an exception occurs."""
    from runtime.azureml_adapter import AzureMLAdapter
    
    # Mock predict function to raise exception
    with patch('runtime.azureml_adapter.predict', side_effect=ValueError("Test error")):
        with patch('runtime.azureml_adapter.logger') as mock_logger:
            result = AzureMLAdapter.run({"data": "test"})
            
            # Verify error logging and result
            mock_logger.error.assert_called_once()
            assert "Test error" in mock_logger.error.call_args[0][0]
            assert result == {"error": "Test error", "status": "failed"}

def test_azureml_init_function():
    """Test the AzureML init function."""
    from runtime.azureml_adapter import init, AzureMLAdapter
    
    # Mock AzureMLAdapter.init
    with patch.object(AzureMLAdapter, 'init') as mock_init:
        init()
        mock_init.assert_called_once()

def test_azureml_run_function():
    """Test the AzureML run function."""
    from runtime.azureml_adapter import run, AzureMLAdapter
    
    # Mock AzureMLAdapter.run
    with patch.object(AzureMLAdapter, 'run', return_value={"result": "test"}) as mock_run:
        result = run({"data": "test"})
        mock_run.assert_called_once_with({"data": "test"})
        assert result == {"result": "test"}

if __name__ == "__main__":
    # Run the tests manually
    pytest.main(["-v", "--cov=runtime.azureml_adapter", "--cov-report=term-missing", __file__])
