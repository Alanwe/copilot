# Text Processor Component

A component that processes text data, including word counting and filtering by word length.

## Overview

The Text Processor Component analyzes text data and provides statistics about word counts and filtered text based on word length criteria. This component can be used in both batch and real-time processing scenarios.

## Azure Services

This component can be deployed to the following Azure services:
- Azure ML Components and pipelines
- Azure ML Batch Inference
- Azure ML Endpoints
- Azure Functions

## Prerequisites

- Azure subscription
- Azure ML workspace or Azure Functions resource
- Python 3.8+
- Required Python packages (listed in requirements.txt)

## Installation

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Configuration

The component accepts the following configuration parameters:

| Parameter  | Type | Required | Default | Description |
|------------|------|----------|---------|-------------|
| min_length | int  | No       | 3       | Minimum word length to include in filtered text |
| max_length | int  | No       | 100     | Maximum word length to include in filtered text |

## Usage

### Single Item Processing

```python
from components.azure_ml.text_processor.src.component import TextProcessingComponent

# Create component
component = TextProcessingComponent({"min_length": 4, "max_length": 15})

# Process text
result = component.run({
    "text": "This is a sample text with some long and short words"
})

print(result)
```

### Batch Processing

```python
from components.azure_ml.text_processor.src.component import TextProcessingComponent

# Create component
component = TextProcessingComponent()

# Process batch of texts
result = component.run({
    "batch": [
        {"text": "This is sample text one"},
        {"text": "This is sample text two"}
    ]
})

print(result)
```

## Deployment

### Azure ML Component

1. Navigate to the component directory
2. Deploy using the deployment script:
   ```bash
   cd deployment
   python deploy_aml.py --subscription <subscription-id> --resource-group <resource-group> --workspace <workspace>
   ```

### Azure Function

1. Navigate to the component directory
2. Deploy using the deployment script:
   ```bash
   cd deployment
   python deploy_function.py --subscription <subscription-id> --resource-group <resource-group>
   ```

## Examples

See the [examples](./examples) directory for more usage examples.

## Testing

Run the component tests:

```bash
cd tests
python -m pytest
```

## Best Practices

- Use appropriate word length filters for your use case
- For large documents, consider increasing memory allocation
- In batch processing mode, limit batch size to avoid memory issues

## Troubleshooting

Common issues:
- If processing fails with memory errors, try reducing batch size
- Ensure input text is properly encoded (UTF-8 recommended)