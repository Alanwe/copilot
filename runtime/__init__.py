"""
Runtime package for Azure Components Foundry.
Provides adapters and dispatcher for different deployment targets.
"""

__version__ = "1.0.0"

# Make key components available at package level
from .dispatcher import predict, health_check
from .azureml_adapter import AzureMLAdapter
from .function_adapter import AzureFunctionAdapter
from .rest_adapter import ContainerAppAdapter as RESTAdapter
from .mcp_adapter import MCPAdapter

__all__ = [
    "predict",
    "health_check",
    "AzureMLAdapter", 
    "AzureFunctionAdapter",
    "RESTAdapter",
    "MCPAdapter"
]
