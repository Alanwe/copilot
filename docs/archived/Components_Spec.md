# Components Specification

This document describes the design and implementation standards for components in the Azure Components Foundry. The specification focuses on creating components that can run across all supported services using the unified architecture pattern.

## Core Architecture

The new unified architecture uses a simplified function-based approach rather than class-based components. This enables easier integration with various Azure runtimes through a central dispatcher.

### Component Function

All components should implement a `predict` function with the following signature:

```python
from typing import Dict, Any, Union, List

def predict(input_data: Union[Dict[str, Any], List[Dict[str, Any]], str]) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
    """
    Process the input data and return predictions.
    
    Args:
        input_data: Can be:
            - A dictionary with required input fields
            - A list of dictionaries for batch processing
            - A raw string input
            
    Returns:
        - Dictionary with results for single inputs
        - List of dictionaries for batch processing results
    """
    # Implementation goes here
    pass
        """
        Clean up any resources used by the component.
        Override if your component needs to release resources.
        """
        pass
```

### Runtime Dispatcher System

The unified architecture uses a central dispatcher that selects and invokes components at runtime based on environment variables. This approach allows the same container image to be used across different Azure services.

#### Dispatcher

The dispatcher is responsible for:
1. Reading the `HANDLER` environment variable to determine which component to load
2. Dynamically importing the component module
3. Invoking the component's `predict` function with the provided input

```python
import importlib
import os
import logging
from typing import Union, Dict, List, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get component handler from environment variable
_target = os.getenv("HANDLER", "components.word_count.src.component:predict")
logger.info(f"Using handler: {_target}")

# Initialize predict_fn as None for lazy loading
predict_fn = None
_mod = None
_fn = None

def _load_handler():
    """Lazy load the handler function."""
    global predict_fn, _mod, _fn
    if predict_fn is None:
        try:
            _mod, _fn = _target.split(":")
            predict_fn = getattr(importlib.import_module(_mod), _fn)
            logger.info(f"Successfully loaded function: {_fn} from module: {_mod}")
        except Exception as e:
            logger.error(f"Failed to load handler {_target}: {str(e)}")
            raise
    return predict_fn

def predict(payload: Union[str, dict, list]) -> Union[dict, list]:
    """
    Universal predict function that handles single items or batches.
    """
    try:
        # Lazy load the handler function
        handler_fn = _load_handler()
        return handler_fn(payload)
    except Exception as e:
        logger.error(f"Error in predict function: {str(e)}")
        raise
```

#### Service Adapters

The runtime system includes adapters for each supported Azure service:

1. **AzureML Adapter** (`runtime/azureml_adapter.py`): 
   - Handles both online and batch endpoints
   - Adapts Azure ML scoring protocol to the dispatcher
   - Supports mini-batch processing

2. **Function Adapter** (`runtime/function_adapter.py`):
   - Adapts HTTP triggers to the component interface
   - Handles HTTP request/response conversion
   - Supports Azure Functions triggers

3. **REST Adapter** (`runtime/rest_adapter.py`):
   - Provides a standard REST API for Container Apps/App Service
   - Implements health check endpoints
   - Handles API protocol conversion

4. **MCP Adapter** (`runtime/mcp_adapter.py`):
   - Exposes components as Model Context Protocol actions
   - Handles MCP action protocol
   - Enables AI agent integration

All adapters follow a common pattern:
        Run the component in Azure ML context
        
        Args:
            component_instance: Instance of a BaseComponent
            args: Arguments from Azure ML component call
            
        Returns:
            Properly formatted Azure ML outputs
        """
        # Convert Azure ML inputs to component format
        inputs = {k: v.read() for k, v in args.items()}
        
        # Run the component
        outputs = component_instance.run(inputs)
        
        # Convert outputs to Azure ML format
        return outputs

class AzureFunctionAdaptor:
    """Adaptor for Azure Functions"""
    
    @staticmethod
    def init():
        """Initialize the Azure Function environment"""
        # Setup Azure Function specific environment
        pass
    
    @staticmethod
    def run(component_instance, req):
        """
        Run the component in Azure Function context
        
        Args:
            component_instance: Instance of a BaseComponent
            req: HTTP request object
            
        Returns:
            HTTP response
        """
        # Convert HTTP request to component inputs
        try:
            req_body = req.get_json()
        except ValueError:
            req_body = {}
            
        # Run the component
        outputs = component_instance.run(req_body)
        
        # Return as HTTP response
        return func.HttpResponse(
            json.dumps(outputs),
            status_code=200,
            mimetype="application/json"
        )
```

## Implementation Guidelines

### 1. Batch and Realtime Processing

Components should support both batch and realtime processing modes through a consistent interface:

```python
class MyComponent(BaseComponent):
    def run(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process inputs in either batch or single-item mode.
        
        Args:
            inputs: Dictionary with either a single item or a batch of items
            
        Returns:
            Processed output in the corresponding format
        """
        if "batch" in inputs and isinstance(inputs["batch"], list):
            # Batch processing mode
            results = []
            for item in inputs["batch"]:
                results.append(self._process_single_item(item))
            return {"batch_results": results}
        else:
            # Single item processing mode
            return {"result": self._process_single_item(inputs)}
    
    def _process_single_item(self, item):
        """Process a single input item"""
        # Implement your component logic here
        pass
```

### 2. Encapsulation and Abstraction

Components should:
- Encapsulate their internal logic
- Expose a clean, consistent interface
- Hide service-specific implementation details
- Use dependency injection for external services

Example implementation pattern:

```python
class ImageProcessingComponent(BaseComponent):
    def initialize(self):
        # Set up resources needed by the component
        self.model = self._load_model()
    
    def _load_model(self):
        # Encapsulated logic for model loading
        model_path = self.config.get("model_path")
        # Load and return the model
        
    def run(self, inputs):
        # Core component logic
        images = inputs.get("images", [])
        processed = [self._process_image(img) for img in images]
        return {"processed_images": processed}
    
    def _process_image(self, image):
        # Encapsulated image processing logic
        pass
```

### 3. Shared Libraries

Components can share common functionality through a library structure:

```
/common/                             # Shared libraries
├── authentication/                  # Authentication utilities
│   ├── __init__.py
│   ├── key_vault.py                 # Key Vault integration
│   └── managed_identity.py          # Managed Identity helpers
├── storage/                         # Storage utilities
│   ├── __init__.py
│   ├── blob_storage.py              # Blob storage helpers
│   └── file_storage.py              # File storage helpers
└── utils/                           # General utilities
    ├── __init__.py
    ├── logging.py                   # Logging helpers
    └── telemetry.py                 # Telemetry helpers
```

To use shared libraries in components:

```python
from common.authentication import managed_identity
from common.storage import blob_storage

class MyComponent(BaseComponent):
    def initialize(self):
        # Get credentials using managed identity
        self.credentials = managed_identity.get_credentials()
        # Create blob client
        self.blob_client = blob_storage.create_client(self.credentials)
```

### 4. Cross-Platform Design

To ensure components can be extended to other cloud platforms (AWS, GCP) in the future:

1. Use dependency injection for cloud-specific services
2. Create platform-specific adaptors
3. Keep core business logic independent of cloud platform

Example structure:

```python
# Generic storage interface
class StorageProvider(ABC):
    @abstractmethod
    def upload_file(self, local_path, remote_path):
        pass
    
    @abstractmethod
    def download_file(self, remote_path, local_path):
        pass

# Azure implementation
class AzureBlobStorage(StorageProvider):
    def upload_file(self, local_path, remote_path):
        # Azure-specific implementation
        
    def download_file(self, remote_path, local_path):
        # Azure-specific implementation

# AWS implementation (future)
class S3Storage(StorageProvider):
    def upload_file(self, local_path, remote_path):
        # AWS-specific implementation
        
    def download_file(self, remote_path, local_path):
        # AWS-specific implementation

# Component using storage
class DataProcessingComponent(BaseComponent):
    def __init__(self, config, storage_provider):
        super().__init__(config)
        self.storage = storage_provider
    
    def run(self, inputs):
        # Download data using the storage provider
        self.storage.download_file(inputs["source"], "temp.data")
        # Process data
        # Upload results
        self.storage.upload_file("results.data", inputs["destination"])
```

## Deployment Considerations

### 1. Azure ML Components and Endpoints

For Azure ML components and endpoints:
- Components should have a clear YAML definition
- Component code should be packaged with dependencies
- Parameters should be clearly defined with types and defaults

Example Azure ML component YAML:

```yaml
$schema: https://azuremlschemas.azureedge.net/latest/commandComponent.schema.json
name: my-component
display_name: My Component
version: 1.0.0
type: command
inputs:
  input_data:
    type: uri_folder
  parameter_1:
    type: string
    default: "default_value"
outputs:
  output_data:
    type: uri_folder
code: ./src
environment: azureml:my-env:1
command: >-
  python run.py 
  --input_data ${{inputs.input_data}} 
  --parameter_1 ${{inputs.parameter_1}} 
  --output_data ${{outputs.output_data}}
```

### 2. Azure Functions

For Azure Functions:
- Use input and output bindings appropriate for the scenario
- Implement proper error handling and status codes
- Support asynchronous processing for long-running operations

Example function.json:

```json
{
  "bindings": [
    {
      "authLevel": "function",
      "type": "httpTrigger",
      "direction": "in",
      "name": "req",
      "methods": ["post"],
      "route": "component/{componentName}"
    },
    {
      "type": "http",
      "direction": "out",
      "name": "$return"
    }
  ]
}
```

### 3. REST/OpenAI/Swagger MCP

For REST/OpenAI/Swagger MCP components:
- Define a clear OpenAPI (Swagger) specification
- Implement consistent RESTful endpoints
- Support standard HTTP methods (GET, POST, PUT, DELETE)
- Include proper authentication and authorization mechanisms
- Handle rate limiting and throttling appropriately

Example OpenAPI specification:

```yaml
openapi: 3.0.0
info:
  title: Component API
  version: 1.0.0
  description: API for component
paths:
  /component:
    post:
      summary: Process data using the component
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                text:
                  type: string
                  description: Text to process
      responses:
        '200':
          description: Successful processing
          content:
            application/json:
              schema:
                type: object
                properties:
                  result:
                    type: object
```

### 4. Deployment Strategy

Each component should include:
- Clear deployment scripts
- Infrastructure as code templates (ARM, Bicep, or Terraform)
- Documented environment requirements
- Deployment validation checks

## Best Practices

1. **Error Handling**
   - Use specific exception types
   - Provide detailed error messages
   - Implement retry logic for transient failures
   - Log errors comprehensively

2. **Logging and Telemetry**
   - Log component initialization, execution, and cleanup
   - Include performance metrics
   - Use structured logging
   - Support different log levels

3. **Testing**
   - Unit test all business logic
   - Create integration tests for each supported platform
   - Test both batch and real-time modes
   - Include error and edge case scenarios

4. **Documentation**
   - Document all public interfaces
   - Include examples for both batch and real-time usage
   - Document configuration options
   - Explain deployment requirements

## Example Implementation

Here's a complete example of a component following the unified architecture pattern:

```python
# components/word_count/src/component.py
import logging
from typing import Dict, Any, Union, List

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def predict(input_data: Union[Dict[str, Any], List[Dict[str, Any]], str]) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
    """
    Count words in the provided text.
    
    Args:
        input_data: Can be:
            - A dictionary with a "text" key
            - A list of dictionaries for batch processing
            - A raw string
            
    Returns:
        - Dictionary with word count results, or
        - List of dictionaries for batch processing results
    """
    logger.info(f"Processing input of type {type(input_data)}")
    
    # Handle batch processing
    if isinstance(input_data, list):
        logger.info(f"Processing batch of {len(input_data)} items")
        results = []
        for item in input_data:
            text = item.get("text", "") if isinstance(item, dict) else str(item)
            results.append(process_single_text(text))
        return results
    
    # Handle single item (dict or string)
    elif isinstance(input_data, dict):
        text = input_data.get("text", "")
        return process_single_text(text)
    
    # Handle raw string input
    else:
        text = str(input_data)
        return process_single_text(text)

def process_single_text(text: str) -> Dict[str, Any]:
    """Count words in a single text input."""
    # Split text into words
    words = text.split()
    
    # Count words by length
    length_distribution = {}
    for word in words:
        word_len = len(word)
        if word_len in length_distribution:
            length_distribution[word_len] += 1
        else:
            length_distribution[word_len] = 1
      return {
        "text": text,
        "word_count": len(words),
        "character_count": len(text),
        "average_word_length": sum(len(w) for w in words) / max(len(words), 1),
        "length_distribution": length_distribution
    }
```

## Unified Deployment Architecture

The unified architecture enables deploying the same component to multiple Azure runtimes:

### 1. Deployment Manifest

The deployment manifest (`deploy/manifest.yaml`) is the single source of truth for all deployments:

```yaml
# Azure Components Foundry Deployment Manifest

# Container registry configuration
acr: myacr.azurecr.io
imageName: azure-components-foundry
imageTag: latest

# Global defaults
defaults:
  instance_type: Standard_DS3_v2
  instance_count: 1
  request_timeout_ms: 60000
  max_concurrent_requests: 10

# Deployment groups - organize by environment/region
groups:
  # Development environment
  dev-eastus:
    subscription: "sub-dev-12345678-1234-1234-1234-123456789012"
    resourceGroup: "rg-components-dev"
    region: "eastus"
    deployments:
      - component: word_count
        services: [aml_online, function, containerapp] 
        overrides:
          instance_type: Standard_DS2_v2
          min_replicas: 0
          max_replicas: 3

  # Production environment
  prod-westus2:
    subscription: "sub-prod-12345678-1234-1234-1234-123456789012"
    resourceGroup: "rg-components-prod"
    region: "westus2"
    deployments:
      - component: word_count
        services: [aml_online, aml_batch, function, containerapp]
        overrides:
          instance_type: Standard_DS4_v2
          min_replicas: 2
          max_replicas: 20

# Component-specific defaults
components:
  word_count:
    handler: "components.word_count.src.component:predict"
    defaults:
      request_timeout_ms: 20000
      max_concurrent_requests: 15
```

### 2. Docker Container

A single Docker container image is used for all components and deployment targets. The container uses the runtime dispatcher to select which component to run based on environment variables:

```dockerfile
# Base Dockerfile for all components
FROM python:3.10-slim

WORKDIR /app

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy component code
COPY . .

# Set Python path
ENV PYTHONPATH=/app

# Default environment variables
ENV HANDLER="components.word_count.src.component:predict"
ENV PORT=8000

# Expose the port
EXPOSE 8000

# Run the REST adapter by default
CMD ["python", "-m", "runtime.rest_adapter"]
```

### 3. Runtime Adapters

The adapters connect the components to different Azure services. Here's an example of the REST adapter:

```python
# runtime/rest_adapter.py
import os
import logging
import json
from fastapi import FastAPI, Request, HTTPException
import uvicorn

from runtime.dispatcher import predict, health_check

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title="Azure Components Foundry", version="1.0.0")

logger.info("Initializing Container Apps adapter")

@app.get("/health")
async def health():
    """Health check endpoint."""
    return health_check()

@app.post("/predict")
async def predict_endpoint(request: Request):
    """Prediction endpoint."""
    try:
        # Parse request body
        payload = await request.json()
        
        # Process with dispatcher
        result = predict(payload)
        
        return result
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

def main():
    """Run the FastAPI server."""
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port)

if __name__ == "__main__":
    main()
```

## Best Practices for Unified Architecture

### 1. Component Development

When developing components for the unified architecture:

- Keep components small and focused on a specific task
- Use the standard `predict` function signature
- Support string, dictionary, and batch input formats
- Include clear logging for monitoring and debugging
- Avoid global state or file system dependencies
- Use dependency injection for external services
- Document the input and output formats

### 2. Testing Components

To test components in the unified architecture:

- Write unit tests for each component function
- Include tests for all input formats (string, dictionary, batch)
- Test edge cases (empty input, unexpected types)
- Use the dispatcher for integration testing
- Create realistic test fixtures

### 3. Deployment

For deploying components in the unified architecture:

- Use the manifest to define deployment targets
- Build one container image per Git commit (e.g., using Git SHA as tag)
- Use the same image across all environments
- Configure components through environment variables
- Use separate environment-specific configurations in the manifest
- Validate deployments with health checks

## Conclusion

The unified architecture pattern provides several advantages:

1. **Simplicity**: Components are simple functions with a standardized signature
2. **Flexibility**: The same component can run on multiple Azure services
3. **Maintainability**: Changes to runtime adapters benefit all components
4. **Scalability**: Components can be deployed to services that match their scaling requirements
5. **Consistency**: Unified approach to logging, error handling, and configuration

By adopting this architecture, teams can focus on the business logic of their components while the runtime system handles the integration with Azure services.

This specification provides a comprehensive guide for creating components that can run across all supported Azure services while maintaining consistency, simplicity, and extensibility for future cloud services.