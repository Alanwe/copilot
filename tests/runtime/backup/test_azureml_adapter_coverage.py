"""
Test coverage for the AzureML adapter module.
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
    # Mock dispatcher.predict to avoid dependencies
    sys.modules['runtime.dispatcher'] = Mock()
    sys.modules['runtime.dispatcher'].predict = Mock(return_value={"result": "test_result"})


def teardown_module():
    """Clean up mocks after tests."""
    if 'runtime.azureml_adapter' in sys.modules:
        del sys.modules['runtime.azureml_adapter']


def test_azureml_adapter_initialization():
    """Test initialization of the AzureML adapter."""
    # Import locally to get a fresh instance
    if 'runtime.azureml_adapter' in sys.modules:
        del sys.modules['runtime.azureml_adapter']
    
    # Set up mocks
    setup_module()
    
    # Import the module
    from runtime.azureml_adapter import AzureMLAdapter
    
    # Mock the logger
    logger_mock = MagicMock()
    
    with patch('runtime.azureml_adapter.logger', logger_mock):
        # Call the init method
        AzureMLAdapter.init()
        # Verify logger was called correctly
        logger_mock.info.assert_called_once_with("Initializing Azure ML adapter")


def test_azureml_adapter_run_with_dict():
    """Test the run method of the AzureML adapter with dict input."""
    # Import locally to get a fresh instance
    if 'runtime.azureml_adapter' in sys.modules:
        del sys.modules['runtime.azureml_adapter']
    
    # Set up mocks
    setup_module()
    mock_predict = MagicMock(return_value={"result": "mocked_result"})
    sys.modules['runtime.dispatcher'].predict = mock_predict
    
    # Import the module
    from runtime.azureml_adapter import AzureMLAdapter
    
    # Mock the logger
    logger_mock = MagicMock()
    
    with patch('runtime.azureml_adapter.logger', logger_mock):
        # Test with dictionary input
        input_data = {"text": "test"}
        result = AzureMLAdapter.run(input_data)
        
        # Verify predict was called correctly
        mock_predict.assert_called_with(input_data)
        
        # Verify result
        assert result == {"result": "mocked_result"}
        
        # Verify logging occurred
        logger_mock.info.assert_any_call("Processing Azure ML request")
        logger_mock.info.assert_any_call("Processing online request")


def test_azureml_adapter_run_with_batch():
    """Test the run method of the AzureML adapter with batch input."""
    # Import locally to get a fresh instance
    if 'runtime.azureml_adapter' in sys.modules:
        del sys.modules['runtime.azureml_adapter']
    
    # Set up mocks
    setup_module()
    mock_predict = MagicMock(return_value=[{"result": "result1"}, {"result": "result2"}])
    sys.modules['runtime.dispatcher'].predict = mock_predict
    
    # Import the module
    from runtime.azureml_adapter import AzureMLAdapter
    
    # Mock the logger
    logger_mock = MagicMock()
    
    with patch('runtime.azureml_adapter.logger', logger_mock):
        # Test with list input (batch mode)
        batch_input = [{"text": "test1"}, {"text": "test2"}]
        result = AzureMLAdapter.run(batch_input)
        
        # Verify predict was called correctly
        mock_predict.assert_called_with(batch_input)
        
        # Verify result
        assert result == [{"result": "result1"}, {"result": "result2"}]
        
        # Verify logging occurred
        logger_mock.info.assert_any_call("Processing Azure ML request")
        logger_mock.info.assert_any_call(f"Processing batch request with {len(batch_input)} items")


def test_azureml_adapter_run_with_exception():
    """Test the run method when an exception occurs."""
    # Import locally to get a fresh instance
    if 'runtime.azureml_adapter' in sys.modules:
        del sys.modules['runtime.azureml_adapter']
    
    # Set up mocks
    setup_module()
    mock_predict = MagicMock(side_effect=ValueError("Test error"))
    sys.modules['runtime.dispatcher'].predict = mock_predict
    
    # Import the module
    from runtime.azureml_adapter import AzureMLAdapter
    
    # Mock the logger
    logger_mock = MagicMock()
    
    with patch('runtime.azureml_adapter.logger', logger_mock):
        # Test with error
        input_data = {"text": "test"}
        result = AzureMLAdapter.run(input_data)
        
        # Verify error handling
        logger_mock.error.assert_called_once_with(f"Error in Azure ML adapter: Test error")
        assert result == {"error": "Test error", "status": "failed"}


def test_init_wrapper_function():
    """Test the init wrapper function."""
    # Import locally to get a fresh instance
    if 'runtime.azureml_adapter' in sys.modules:
        del sys.modules['runtime.azureml_adapter']
    
    # Set up mocks
    setup_module()
    
    # Import the module
    from runtime.azureml_adapter import init, AzureMLAdapter
    
    # Mock the class init method
    with patch.object(AzureMLAdapter, 'init') as mock_init:
        # Call the wrapper function
        init()
        # Verify the class method was called
        mock_init.assert_called_once()


def test_run_wrapper_function():
    """Test the run wrapper function."""
    # Import locally to get a fresh instance
    if 'runtime.azureml_adapter' in sys.modules:
        del sys.modules['runtime.azureml_adapter']
    
    # Set up mocks
    setup_module()
    
    # Import the module
    from runtime.azureml_adapter import run, AzureMLAdapter
    
    # Mock the class run method
    with patch.object(AzureMLAdapter, 'run') as mock_run:
        mock_run.return_value = {"result": "test"}
        # Call the wrapper function
        result = run({"input": "data"})
        # Verify the class method was called with correct args
        mock_run.assert_called_once_with({"input": "data"})
        # Verify result is passed through
        assert result == {"result": "test"}
