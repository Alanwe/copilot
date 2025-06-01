"""
Tests for the REST adapter module.
"""
import pytest
import json
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from runtime.rest_adapter import app, RESTAdapter


class TestRESTAdapter:
    """Test class for REST adapter."""
    
    def setup_method(self):
        """Set up test client."""
        self.client = TestClient(app)
        
    def test_init_method(self):
        """Test initialization method."""
        # Should not raise any exceptions
        RESTAdapter.init()
        
    def test_health_endpoint(self):
        """Test health check endpoint."""
        response = self.client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "handler" in data
        assert "version" in data
        
    def test_predict_endpoint_single_item(self):
        """Test predict endpoint with single item."""
        with patch('runtime.rest_adapter.predict') as mock_predict:
            mock_predict.return_value = {"result": "processed"}
            
            response = self.client.post(
                "/predict",
                json={"text": "test input"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data == {"result": "processed"}
            mock_predict.assert_called_once_with({"text": "test input"})
            
    def test_predict_endpoint_batch_items(self):
        """Test predict endpoint with batch of items."""
        with patch('runtime.rest_adapter.predict') as mock_predict:
            mock_predict.return_value = [
                {"result": "processed1"},
                {"result": "processed2"}
            ]
            
            response = self.client.post(
                "/predict",
                json=[
                    {"text": "test input 1"},
                    {"text": "test input 2"}
                ]
            )
            
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 2
            assert data[0] == {"result": "processed1"}
            assert data[1] == {"result": "processed2"}
            
    def test_predict_endpoint_string_input(self):
        """Test predict endpoint with string input."""
        with patch('runtime.rest_adapter.predict') as mock_predict:
            mock_predict.return_value = {"result": "processed string"}
            
            response = self.client.post(
                "/predict",
                json="test string input"
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data == {"result": "processed string"}
            mock_predict.assert_called_once_with("test string input")
            
    def test_predict_endpoint_error_handling(self):
        """Test predict endpoint error handling."""
        with patch('runtime.rest_adapter.predict') as mock_predict:
            mock_predict.side_effect = Exception("Processing failed")
            
            response = self.client.post(
                "/predict",
                json={"text": "test input"}
            )
            
            assert response.status_code == 500
            data = response.json()
            assert "detail" in data
            assert "Processing failed" in data["detail"]
            
    def test_batch_endpoint(self):
        """Test dedicated batch endpoint."""
        with patch('runtime.rest_adapter.predict') as mock_predict:
            mock_predict.return_value = [
                {"result": "processed1"},
                {"result": "processed2"},
                {"result": "processed3"}
            ]
            
            response = self.client.post(
                "/batch",
                json=[
                    {"text": "input 1"},
                    {"text": "input 2"},
                    {"text": "input 3"}
                ]
            )
            
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 3
            
    def test_batch_endpoint_empty_list(self):
        """Test batch endpoint with empty list."""
        with patch('runtime.rest_adapter.predict') as mock_predict:
            mock_predict.return_value = []
            
            response = self.client.post(
                "/batch",
                json=[]
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data == []
            
    def test_openapi_docs(self):
        """Test that OpenAPI documentation is available."""
        response = self.client.get("/docs")
        assert response.status_code == 200
        
        response = self.client.get("/openapi.json")
        assert response.status_code == 200
        
        # Verify OpenAPI schema structure
        openapi_data = response.json()
        assert "openapi" in openapi_data
        assert "paths" in openapi_data
        assert "/predict" in openapi_data["paths"]
        assert "/batch" in openapi_data["paths"]
        assert "/health" in openapi_data["paths"]


class TestRESTAdapterErrorHandling:
    """Test error handling in REST adapter."""
    
    def setup_method(self):
        """Set up test client."""
        self.client = TestClient(app)
        
    def test_invalid_json_handling(self):
        """Test handling of invalid JSON in requests."""
        response = self.client.post(
            "/predict",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 422  # FastAPI validation error
        
    def test_predict_with_validation_error(self):
        """Test predict endpoint with validation errors."""
        with patch('runtime.rest_adapter.predict') as mock_predict:
            mock_predict.side_effect = ValueError("Validation failed")
            
            response = self.client.post(
                "/predict",
                json={"text": "test"}
            )
            
            assert response.status_code == 500
            data = response.json()
            assert "Validation failed" in data["detail"]
            
    def test_timeout_handling(self):
        """Test handling of processing timeouts."""
        import time
        
        with patch('runtime.rest_adapter.predict') as mock_predict:
            def slow_predict(data):
                time.sleep(0.1)  # Simulate slow processing
                return {"result": "slow"}
                
            mock_predict.side_effect = slow_predict
            
            response = self.client.post(
                "/predict",
                json={"text": "test"}
            )
            
            # Should still complete but may be slow
            assert response.status_code == 200
            
    def test_large_payload_handling(self):
        """Test handling of large payloads."""
        large_payload = {"text": "x" * 10000}  # Large text
        
        with patch('runtime.rest_adapter.predict') as mock_predict:
            mock_predict.return_value = {"result": "processed large"}
            
            response = self.client.post(
                "/predict",
                json=large_payload
            )
            
            assert response.status_code == 200
            mock_predict.assert_called_once_with(large_payload)


class TestRESTAdapterPerformance:
    """Test performance aspects of REST adapter."""
    
    def setup_method(self):
        """Set up test client."""
        self.client = TestClient(app)
        
    def test_concurrent_requests(self):
        """Test handling of concurrent requests."""
        import threading
        import time
        
        results = []
        
        def make_request(i):
            with patch('runtime.rest_adapter.predict') as mock_predict:
                mock_predict.return_value = {"result": f"processed_{i}"}
                
                response = self.client.post(
                    "/predict",
                    json={"text": f"test_{i}"}
                )
                results.append(response.status_code)
        
        threads = []
        for i in range(5):
            thread = threading.Thread(target=make_request, args=(i,))
            threads.append(thread)
            thread.start()
            
        for thread in threads:
            thread.join()
            
        # All requests should succeed
        assert all(status == 200 for status in results)
        
    def test_batch_processing_performance(self):
        """Test performance of batch processing."""
        batch_size = 100
        batch_data = [{"text": f"item_{i}"} for i in range(batch_size)]
        
        with patch('runtime.rest_adapter.predict') as mock_predict:
            mock_predict.return_value = [{"result": f"processed_{i}"} for i in range(batch_size)]
            
            import time
            start_time = time.time()
            
            response = self.client.post(
                "/batch",
                json=batch_data
            )
            
            end_time = time.time()
            processing_time = end_time - start_time
            
            assert response.status_code == 200
            assert len(response.json()) == batch_size
            # Should process reasonably quickly
            assert processing_time < 5.0  # 5 seconds max


class TestRESTAdapterLogging:
    """Test logging functionality in REST adapter."""
    
    def setup_method(self):
        """Set up test client."""
        self.client = TestClient(app)
        
    @patch('runtime.rest_adapter.logger')
    def test_init_logging(self, mock_logger):
        """Test logging in init method."""
        RESTAdapter.init()
        mock_logger.info.assert_called_with("Initializing REST adapter")
        
    @patch('runtime.rest_adapter.logger')
    def test_predict_logging(self, mock_logger):
        """Test logging in predict endpoint."""
        with patch('runtime.rest_adapter.predict') as mock_predict:
            mock_predict.return_value = {"result": "test"}
            
            self.client.post("/predict", json={"text": "test"})
            
            # Should log the request processing
            mock_logger.info.assert_any_call("Processing request via REST API")
            
    @patch('runtime.rest_adapter.logger')
    def test_error_logging(self, mock_logger):
        """Test error logging."""
        with patch('runtime.rest_adapter.predict') as mock_predict:
            mock_predict.side_effect = Exception("Test error")
            
            self.client.post("/predict", json={"text": "test"})
            
            mock_logger.error.assert_called()


class TestRESTAdapterIntegration:
    """Integration tests for REST adapter."""
    
    def setup_method(self):
        """Set up test client."""
        self.client = TestClient(app)
        
    def test_adapter_interface_compliance(self):
        """Test that adapter complies with expected interface."""
        assert hasattr(RESTAdapter, 'init')
        assert callable(RESTAdapter.init)
        
    def test_fastapi_app_configuration(self):
        """Test FastAPI app configuration."""
        assert app.title == "Azure Components Foundry Runtime"
        assert app.description == "REST API for component execution"
        assert app.version == "1.0.0"
        
    def test_cors_configuration(self):
        """Test CORS configuration if enabled."""
        # Test preflight request
        response = self.client.options("/predict")
        
        # Should handle OPTIONS requests
        assert response.status_code in [200, 405]  # 405 if CORS not configured
        
    def test_middleware_stack(self):
        """Test that middleware is properly configured."""
        # Test that requests are processed through the middleware stack
        response = self.client.post(
            "/predict",
            json={"text": "test"}
        )
        
        # Should have proper headers set
        assert "content-type" in response.headers
        assert response.headers["content-type"] == "application/json"
