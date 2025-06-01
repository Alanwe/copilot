"""
Tests for the runtime dispatcher module.
"""
import os
import pytest
import importlib
from unittest.mock import patch, MagicMock, Mock
import sys


class TestDispatcher:
    """Test class for the runtime dispatcher."""
    
    def setup_method(self):
        """Set up test environment."""
        # Mock the component module before importing dispatcher
        mock_component_module = Mock()
        mock_component_module.predict = Mock(return_value={"result": "mocked"})
        sys.modules['components.word_count.src.component'] = mock_component_module
        
        # Re-import dispatcher to pick up the mock
        if 'runtime.dispatcher' in sys.modules:
            importlib.reload(sys.modules['runtime.dispatcher'])
        
    def teardown_method(self):
        """Clean up test environment."""
        # Remove mock modules
        if 'components.word_count.src.component' in sys.modules:
            del sys.modules['components.word_count.src.component']
        if 'runtime.dispatcher' in sys.modules:
            del sys.modules['runtime.dispatcher']
        
    def test_predict_function(self):
        """Test that predict correctly forwards to component."""
        # Import the predict function after mock setup
        from runtime.dispatcher import predict
        
        # Use the predict function
        result = predict({"text": "test"})
        
        # Verify it was forwarded to the mock
        assert result == {"result": "mocked"}
        
    def test_predict_function_with_batch(self):
        """Test that predict correctly handles batch processing."""
        # Import the predict function after mock setup
        from runtime.dispatcher import predict
        
        # Use the predict function with a batch
        batch_input = [{"text": "test1"}, {"text": "test2"}]
        result = predict(batch_input)
        
        # Verify it was processed as a batch
        assert isinstance(result, list)
        assert len(result) == 2
        assert all(item == {"result": "mocked"} for item in result)
        
    def test_predict_function_with_error(self):
        """Test that predict correctly handles errors."""
        # Import the predict function after mock setup
        from runtime.dispatcher import predict
        
        # Setup mock to raise an exception
        import sys
        mock_component_module = sys.modules['components.word_count.src.component']
        mock_component_module.predict.side_effect = ValueError("Test error")
        
        # Use the predict function and check that it raises the error
        with pytest.raises(ValueError, match="Test error"):
            predict({"text": "test"})
        
    def test_lazy_loading(self):
        """Test lazy loading behavior."""
        # Re-import dispatcher to pick up the mock
        if 'runtime.dispatcher' in sys.modules:
            del sys.modules['runtime.dispatcher']
        
        with patch('importlib.import_module') as mock_import:
            # Set up mock module for import
            mock_module = Mock()
            mock_module.predict = Mock(return_value={"result": "mocked"})
            mock_import.return_value = mock_module
            
            # Import the dispatcher
            from runtime.dispatcher import predict
            
            # First call to predict should trigger lazy loading
            predict({"text": "test"})
            mock_import.assert_called_once()
            
            # Reset mock and call again - should not trigger another import
            mock_import.reset_mock()
            predict({"text": "another test"})
            mock_import.assert_not_called()


class TestDispatcherEnvironment:
    """Test dispatcher environment variable handling."""
    
    def setup_method(self):
        """Set up test environment."""
        # Pre-configure mock modules
        mock_component_module = Mock()
        mock_component_module.predict = Mock(return_value={"result": "mocked"})
        sys.modules['components.word_count.src.component'] = mock_component_module
    
    def teardown_method(self):
        """Clean up test environment."""
        if 'components.word_count.src.component' in sys.modules:
            del sys.modules['components.word_count.src.component']
        if 'runtime.dispatcher' in sys.modules:
            del sys.modules['runtime.dispatcher']
    
    @patch.dict(os.environ, {"HANDLER": "components.word_count.src.component:predict"})
    def test_word_count_integration(self):
        """Test dispatcher integration with word_count component."""
        # Re-import dispatcher to pick up new environment
        if 'runtime.dispatcher' in sys.modules:
            del sys.modules['runtime.dispatcher']
        
        from runtime.dispatcher import _target
        
        # Check the target is set correctly
        assert _target == "components.word_count.src.component:predict"
        
        # Import the health_check function to verify integration
        from runtime.dispatcher import health_check
        health_result = health_check()
        
        # Check the module and function are extracted correctly from target
        assert health_result["module"] == "components.word_count.src.component"
        assert health_result["function"] == "predict"
        
    def test_invalid_handler_format(self):
        """Test behavior with invalid HANDLER format."""
        with patch.dict(os.environ, {"HANDLER": "invalid_format"}):
            # Remove dispatcher from cache
            if 'runtime.dispatcher' in sys.modules:
                del sys.modules['runtime.dispatcher']
            
            with pytest.raises(ValueError):
                from runtime.dispatcher import _load_handler
                _load_handler()

    def test_nonexistent_module(self):
        """Test behavior with module that doesn't exist."""
        with patch.dict(os.environ, {"HANDLER": "nonexistent.module:predict"}):
            # Remove dispatcher from cache
            if 'runtime.dispatcher' in sys.modules:
                del sys.modules['runtime.dispatcher']
            
            from runtime.dispatcher import _load_handler
            
            with pytest.raises(ModuleNotFoundError):
                _load_handler()

    def test_missing_function(self):
        """Test behavior with function that doesn't exist in module."""
        # Setup mock module without predict function
        mock_module = Mock(spec=[])  # No functions
        with patch.dict(sys.modules, {"mock_component": mock_module}):
            with patch.dict(os.environ, {"HANDLER": "mock_component:nonexistent_function"}):
                # Remove dispatcher from cache
                if 'runtime.dispatcher' in sys.modules:
                    del sys.modules['runtime.dispatcher']
                
                from runtime.dispatcher import _load_handler
                
                with pytest.raises(AttributeError):
                    _load_handler()


class TestDisptacherHealthCheck:
    """Test health check function."""
    
    def setup_method(self):
        """Set up test environment."""
        mock_component_module = Mock()
        mock_component_module.predict = Mock(return_value={"result": "mocked"})
        sys.modules['components.word_count.src.component'] = mock_component_module
    
    def teardown_method(self):
        """Clean up test environment."""
        if 'components.word_count.src.component' in sys.modules:
            del sys.modules['components.word_count.src.component']
        if 'runtime.dispatcher' in sys.modules:
            del sys.modules['runtime.dispatcher']
    
    def test_health_check_function(self):
        """Test health check returns ok."""
        # Re-import dispatcher to pick up the mock
        if 'runtime.dispatcher' in sys.modules:
            del sys.modules['runtime.dispatcher']
        
        from runtime.dispatcher import health_check
        
        # Get the health check result
        health_check_result = health_check()
        
        # Check that it contains the expected keys
        assert "status" in health_check_result
        assert "handler" in health_check_result
        assert "module" in health_check_result
        assert "function" in health_check_result
        assert "version" in health_check_result
        
        # Check that the status is healthy
        assert health_check_result["status"] == "healthy"

    def test_health_check_with_invalid_handler(self):
        """Test health check still works even if handler is invalid."""
        with patch.dict(os.environ, {"HANDLER": "invalid:format"}):
            # Remove dispatcher from cache
            if 'runtime.dispatcher' in sys.modules:
                del sys.modules['runtime.dispatcher']
            
            from runtime.dispatcher import health_check
            
            # Get the health check result
            health_check_result = health_check()
            
            # Check that it contains the expected keys
            assert "status" in health_check_result
            assert "handler" in health_check_result
            assert "module" in health_check_result
            assert "function" in health_check_result
            assert "version" in health_check_result
            
            # Check that the status is unhealthy since the handler is invalid
            assert health_check_result["status"] == "unhealthy"
