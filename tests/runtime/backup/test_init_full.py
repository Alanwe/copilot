"""
Test suite for init module to achieve 100% test coverage.
"""
import os
import sys
import pytest
from unittest.mock import patch, MagicMock

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

#-----------------------------------------------------------------------------
# Tests for runtime/__init__.py
#-----------------------------------------------------------------------------
def test_init_imports():
    """Test that all expected components are imported and exported."""
    # Import the runtime module
    import runtime
    
    # Check that all expected components are available
    assert hasattr(runtime, "__version__")
    assert runtime.__version__ == "1.0.0"
    
    # Check for specific imports
    assert hasattr(runtime, "predict")
    assert hasattr(runtime, "health_check")
    assert hasattr(runtime, "AzureMLAdapter")
    assert hasattr(runtime, "AzureFunctionAdapter")
    assert hasattr(runtime, "RESTAdapter")
    assert hasattr(runtime, "MCPAdapter")
    
    # Check __all__ list
    expected_exports = [
        "predict", "health_check", "AzureMLAdapter", 
        "AzureFunctionAdapter", "RESTAdapter", "MCPAdapter"
    ]
    assert sorted(runtime.__all__) == sorted(expected_exports)

if __name__ == "__main__":
    # Run the tests manually
    pytest.main(["-v", "--cov=runtime.__init__", "--cov-report=term-missing", __file__])
