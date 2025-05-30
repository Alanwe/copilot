# Azure Components Foundry - Copilot Instructions

This document provides guidelines for GitHub Copilot to assist in developing components for the Azure Components Foundry project.

## Project Overview

This project serves as a foundry for creating reusable components for Azure cloud services using Python. GitHub Copilot is used to create components based on issues. Each component follows specific template guidelines implementing best practices for documentation, examples, and tests.

## Component Development Guidelines

When developing components for this project, follow these guidelines:

### General Structure
- All components should be placed in a dedicated directory under `/components/{service_name}/{component_name}/`
- Each component should include:
  - Main implementation code (Python files)
  - Documentation (README.md)
  - Examples
  - Tests
  - Deployment scripts

### Documentation Requirements
- Every component must have a README.md file that includes:
  - Purpose and functionality
  - Required Azure services
  - Configuration parameters
  - Usage examples
  - Deployment instructions

### Implementation Best Practices
- Follow Azure best practices for:
  - Authentication
  - Key Management (Azure Key Vault)
  - Error handling
  - Logging
  - Security
- Use Azure SDK V2 for Azure ML components and pipelines (YAML format)

### Testing
- Unit tests are required for all components
- Integration tests should be provided where applicable
- Tests should verify component functionality and deployment

## Manifest Structure

A manifest file should be maintained in the root directory that lists all available components and their required Azure services. The manifest should:
- List each component with a unique identifier
- Specify required Azure services for each component
- Include metadata about each component (author, version, etc.)
- Cross-reference components with Azure services

## GitHub Actions Integration

GitHub Actions should:
- Check the manifest for changes
- Test new or edited components
- Deploy verified components to the specified Azure subscription
- Update the manifest with deployment information
- Use Azure tags for component identification and tracking

This document serves as a guide for GitHub Copilot to assist in developing components that adhere to project standards and best practices.