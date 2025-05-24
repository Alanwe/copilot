# Component Template Guidelines

This document outlines the template structure for creating new components in the Azure Components Foundry project.

## Directory Structure

```
/components/{service_name}/{component_name}/
├── README.md                    # Component documentation
├── src/                         # Source code
│   ├── __init__.py
│   └── main.py                  # Main component implementation
├── examples/                    # Example usage
│   ├── basic_usage.py
│   └── advanced_usage.py
├── tests/                       # Unit and integration tests
│   ├── __init__.py
│   ├── test_component.py
│   └── test_integration.py
├── deployment/                  # Deployment scripts
│   ├── deploy.py                # Main deployment script
│   └── parameters.json          # Default deployment parameters
└── metadata.json                # Component metadata
```

## Metadata Schema

The `metadata.json` file should include:

```json
{
  "name": "component-name",
  "version": "1.0.0",
  "description": "Brief component description",
  "author": "Author name",
  "created": "YYYY-MM-DD",
  "updated": "YYYY-MM-DD",
  "azure_services": [
    "service1",
    "service2"
  ],
  "tags": [
    "tag1",
    "tag2"
  ],
  "dependencies": [
    {
      "name": "dependency-name",
      "version": "x.y.z"
    }
  ]
}
```

## README.md Template

Each component should have a README.md file following this structure:

```markdown
# Component Name

Brief description of what the component does.

## Overview

Detailed description including purpose, functionality, and use cases.

## Azure Services

List of Azure services required for this component:
- Service 1
- Service 2

## Prerequisites

- Required Azure resources
- Required permissions
- Dependencies

## Installation

Instructions for installing the component.

## Configuration

Configuration parameters:

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| param1    | str  | Yes      | N/A     | Description |
| param2    | int  | No       | 10      | Description |

## Usage

Basic usage example:

```python
# Python code example
```

## Deployment

Instructions for deploying the component to Azure.

## Examples

Reference to example files in the /examples directory.

## Testing

Instructions for running tests.

## Best Practices

Guidelines specific to this component.

## Troubleshooting

Common issues and solutions.
```

## Implementation Guidelines

### Azure ML Components (YAML/SDK V2)

For Azure ML components:
- Use YAML format for component definitions
- Follow AzureML SDK V2 patterns
- Include input and output specifications
- Provide environment specifications

### Azure Functions

For Azure Functions components:
- Follow the function app structure
- Include proper bindings in function.json
- Implement proper authentication
- Follow the serverless best practices

### Authentication

Always use managed identities where possible. If not possible, use service principals with stored credentials in Azure Key Vault.

### Error Handling

Include comprehensive error handling with:
- Specific exception types
- Logging
- Retry logic for transient failures
- Proper status reporting

### Deployment Best Practices

- Use infrastructure as code (ARM templates, Bicep, or Terraform)
- Follow the principle of least privilege
- Include cleanup scripts
- Document resource requirements and estimated costs