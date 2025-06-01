# Azure Components Foundry User Guide

This guide provides comprehensive instructions for using the Azure Components Foundry, a platform for creating reusable, deployable components for Azure cloud services.

## Table of Contents

1. [Introduction](#introduction)
2. [Creating New Components](#creating-new-components)
3. [Deployment Configuration](#deployment-configuration)
4. [Connecting to Azure](#connecting-to-azure)
5. [Deploying Components](#deploying-components)
6. [Managing Azure Resources](#managing-azure-resources)
7. [Troubleshooting](#troubleshooting)

## Introduction

The Azure Components Foundry provides a unified architecture pattern for developing components that can be deployed to multiple Azure runtimes from a single codebase. This approach offers:

- **Consistency**: Uniform deployment across environments
- **Simplicity**: Create components with a simple function interface
- **Efficiency**: Build once, deploy everywhere
- **Scalability**: Use the same code on multiple Azure services

### Supported Azure Services

- Azure ML Components and pipelines
- Azure ML Batch Inference
- Azure ML Endpoints
- Azure Functions
- Azure Container Apps
- REST APIs/MCP (Model Context Protocol)

## Creating New Components

### Component Structure

Each component must follow this directory structure:

```
components/
└── my_component/
    ├── __init__.py
    ├── README.md          # Component documentation
    ├── requirements.txt   # Dependencies
    ├── defaults.yaml      # Configuration defaults
    ├── Dockerfile         # Component Docker image
    └── src/
        └── component.py   # Main implementation
```

### Component Implementation

1. Create a new directory under `/components` with your component name
2. Implement the main component logic in `src/component.py` with a `predict` function:

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
    # Your component logic here
    result = {"result": "processed data"}
    return result
```

### Component Documentation

Each component must include a README.md with:

1. Component name and purpose
2. Input/output schema
3. Usage examples
4. Configuration options
5. Dependencies

### Component Testing

Create tests to validate your component:

1. Unit tests in the `tests/` directory
2. A `simple_test.py` script for quick validation

Example test script:

```python
from src.component import predict

# Test with a single item
result = predict({"text": "This is a test."})
print(f"Result: {result}")
assert "word_count" in result

# Test with batch input
batch_result = predict([{"text": "Test 1"}, {"text": "Test 2"}])
print(f"Batch result: {batch_result}")
assert len(batch_result) == 2
```

## Deployment Configuration

### Manifest File

Deployments are configured in the `/deploy/manifest.yaml` file, which specifies:

1. Which components to deploy
2. Which Azure services to use
3. Configuration values for each environment

Example manifest structure:

```yaml
# Azure Components Foundry Deployment Manifest
acr: myacr.azurecr.io
imageName: azure-components-foundry
imageTag: latest

# Global defaults
defaults:
  instance_type: Standard_DS3_v2
  instance_count: 1
  request_timeout_ms: 60000
  max_concurrent_requests: 10

# Deployment groups
groups:
  dev-eastus:
    subscription: "subscription-id-1"
    resourceGroup: "rg-components-dev"
    region: "eastus"
    deployments:
      - component: word_count
        services: [containerapp, function]
        overrides:
          min_replicas: 1
          
  production-westus:
    subscription: "subscription-id-2"
    resourceGroup: "rg-components-prod"
    region: "westus"
    deployments:
      - component: text_analyzer
        services: [aml_online, aml_batch]
        overrides:
          instance_type: Standard_DS4_v2
          instance_count: 2
```

### Adding a Component to a Deployment Group

To add your component to a deployment group:

1. Open `/deploy/manifest.yaml`
2. Under the desired group, add a new entry in the `deployments` array:

```yaml
deployments:
  - component: my_component_name
    services: [containerapp, function, aml_online, aml_batch]
    overrides:
      # Component-specific configuration overrides
      instance_count: 2
      min_replicas: 1
```

## Connecting to Azure

### Azure CLI Setup

1. Install the Azure CLI:
   ```bash
   curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash   # Ubuntu/Debian
   brew update && brew install azure-cli                    # macOS
   ```

2. Log in to Azure:
   ```bash
   az login
   ```

3. Set your subscription:
   ```bash
   az account set --subscription "your-subscription-id"
   ```

### Azure Authentication

For automated deployments, create a service principal:

```bash
az ad sp create-for-rbac --name "components-foundry-sp" \
  --role contributor \
  --scopes /subscriptions/your-subscription-id/resourceGroups/your-resource-group \
  --sdk-auth
```

Save the output JSON for CI/CD integration.

### Environment Setup

Use the provided setup script to configure your local environment:

```bash
python admin/azure_setup.py setup \
  --subscription "your-subscription-id" \
  --resource-group "your-resource-group" \
  --location "eastus"
```

## Deploying Components

### Prerequisites

Ensure you have:
1. An Azure subscription
2. An Azure Container Registry
3. The deployment manifest configured properly

### Deploying with the Command Line

Deploy components using the deployment script:

```bash
# Deploy all components in a group
python admin/deploy_components.py deploy --group dev-eastus

# Deploy a specific component
python admin/deploy_components.py deploy --group dev-eastus --component word_count

# Deploy to a specific service
python admin/deploy_components.py deploy --group dev-eastus --component word_count --service containerapp
```

### Build and Push Container Images

Build and push Docker images for your components:

```bash
python admin/deploy_components.py build --acr your-acr-name.azurecr.io
```

## Managing Azure Resources

### Listing Deployed Resources

List all resources created by the Components Foundry in a resource group:

```bash
python admin/discover_components.py list-resources --subscription "your-subscription-id" --resource-group "your-resource-group"
```

This will show:
- Deployed components
- Service types
- Endpoints
- Creation dates
- Status

### Querying Resources by Component

Find all resources associated with a specific component:

```bash
python admin/discover_components.py find-component --name "word_count"
```

### Managing Resources with Azure CLI

List all resources in a resource group:

```bash
az resource list --resource-group "your-resource-group" --output table
```

Delete specific resources:

```bash
az resource delete --ids /subscriptions/{sub-id}/resourceGroups/{group-name}/providers/{resource-provider}/{resource-type}/{resource-name}
```

## Troubleshooting

### Common Issues and Solutions

1. **Authentication Errors**:
   ```bash
   az account show  # Verify current authentication
   az login         # Re-authenticate if needed
   ```

2. **Deployment Failures**:
   ```bash
   # Check resource group deployments
   az deployment group list --resource-group "your-resource-group" --output table
   ```

3. **Component Not Found**:
   Ensure your component is properly structured and the `HANDLER` environment variable points to the correct module path.

4. **Connection Issues**:
   ```bash
   # Test Azure connectivity
   python admin/check_azure_connectivity.py
   ```

### Logs and Diagnostics

Access logs for your deployed components:

1. **Container Apps**:
   ```bash
   az containerapp logs show --name "component-name" --resource-group "your-resource-group"
   ```

2. **Azure Functions**:
   ```bash
   az functionapp log tail --name "component-name" --resource-group "your-resource-group"
   ```

3. **Azure ML**:
   ```bash
   az ml online-deployment get-logs --name "component-name" --endpoint "endpoint-name" --resource-group "your-resource-group"
   ```
