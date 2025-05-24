# Components Specification

This document describes the design and implementation standards for components in the Azure Components Foundry. The specification focuses on creating components that can run across all supported services while maintaining a consistent architecture.

## Core Architecture

### Component Base Class

All components should implement the following base interface to ensure consistency across different deployment targets:

```python
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class BaseComponent(ABC):
    """
    Base component interface that all components should implement.
    This ensures consistent behavior across different deployment targets.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the component with configuration.
        
        Args:
            config: A dictionary containing component configuration
        """
        self.config = config or {}
        self.initialize()
    
    def initialize(self):
        """
        Initialize resources needed by the component.
        Override this method for resource setup that's independent of deployment target.
        """
        pass
    
    @abstractmethod
    def run(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run the component's core logic.
        
        Args:
            inputs: Input data dictionary
            
        Returns:
            Dictionary containing the output data
        """
        pass
    
    def cleanup(self):
        """
        Clean up any resources used by the component.
        Override if your component needs to release resources.
        """
        pass
```

### Service-Specific Adaptors

To support different Azure services, components should use adaptors that handle the service-specific implementation details:

```python
class AzureMLComponentAdaptor:
    """Adaptor for Azure ML Components/Pipelines"""
    
    @staticmethod
    def init():
        """Initialize the Azure ML component environment"""
        # Setup Azure ML specific environment
        pass
        
    @staticmethod
    def run(component_instance, args):
        """
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

### 3. Deployment Strategy

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

Here's a complete example of a component following this specification:

```python
# component.py
from typing import Dict, Any
from common.base import BaseComponent

class TextProcessingComponent(BaseComponent):
    """Component that processes text data."""
    
    def initialize(self):
        """Set up resources needed by the component."""
        # Load any required resources
        self.min_length = self.config.get("min_length", 3)
        self.max_length = self.config.get("max_length", 100)
    
    def run(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Process text inputs."""
        if "batch" in inputs and isinstance(inputs["batch"], list):
            # Batch processing mode
            results = []
            for item in inputs["batch"]:
                text = item.get("text", "")
                results.append(self._process_text(text))
            return {"results": results}
        else:
            # Single item processing mode
            text = inputs.get("text", "")
            return {"result": self._process_text(text)}
    
    def _process_text(self, text: str) -> Dict[str, Any]:
        """Process a single text input."""
        # Count words
        words = text.split()
        word_count = len(words)
        
        # Filter words by length
        filtered_words = [w for w in words if self.min_length <= len(w) <= self.max_length]
        
        return {
            "original_text": text,
            "word_count": word_count,
            "filtered_word_count": len(filtered_words),
            "filtered_text": " ".join(filtered_words)
        }
    
    def cleanup(self):
        """Clean up resources."""
        # Release any resources if needed
        pass

# Azure ML adaptor
def init():
    """Initialize the component for Azure ML."""
    global component
    import json
    import os
    
    # Load configuration from environment variable or file
    config_path = os.environ.get("COMPONENT_CONFIG", "config.json")
    with open(config_path) as f:
        config = json.load(f)
    
    # Create component instance
    component = TextProcessingComponent(config)

def run(input_data):
    """Run the component in Azure ML context."""
    # Parse input_data according to Azure ML format
    inputs = input_data.read_as_dict()
    
    # Run the component
    outputs = component.run(inputs)
    
    # Return outputs in Azure ML expected format
    return outputs

# Azure Function adaptor
def main(req):
    """Azure Function entry point."""
    import json
    import azure.functions as func
    
    # Get configuration
    config = {}  # Load from environment or elsewhere
    
    # Create component instance
    component = TextProcessingComponent(config)
    
    try:
        # Parse request body
        req_body = req.get_json()
        
        # Run the component
        outputs = component.run(req_body)
        
        # Return success response
        return func.HttpResponse(
            json.dumps(outputs),
            mimetype="application/json",
            status_code=200
        )
    except Exception as e:
        # Log the error
        print(f"Error: {str(e)}")
        
        # Return error response
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            mimetype="application/json",
            status_code=500
        )
```

This specification provides a comprehensive guide for creating components that can run across all supported Azure services while maintaining consistency, simplicity, and extensibility for future cloud services.