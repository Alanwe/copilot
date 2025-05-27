# Azure Components Foundry

A foundry for creating reusable components for Azure cloud services using Python. This project leverages GitHub Copilot to create components based on issues, following strict template guidelines.

## Project Overview

The Azure Components Foundry is designed to:
- Create reusable, well-documented components for Azure cloud services
- Implement best practices for component creation including documentation, examples, and tests
- Provide deployment scripts for component integration with Azure services
- Maintain a central gallery of components for easy discovery and reuse

## Supported Azure Services

Components can be created and deployed for the following Azure services:
- Azure ML Components and pipelines (YAML/AzureML SDK V2 only)
- Azure ML Batch Inference
- Azure ML Endpoints
- Azure Functions
- Azure Managed Endpoints Serverless

## Component Structure

Each component follows a standardized template that includes:
- Source code implementing the component functionality
- Comprehensive documentation
- Usage examples
- Tests for validation
- Deployment scripts for Azure integration

For detailed component guidelines, see the [component template](.github/copilot-instructions/component-template.md).

## Component Gallery

Components are organized in a gallery structure under the `/components` directory. Each component includes scripts to deploy to the relevant Azure services.

All components adhere to Azure best practices for:
- Authentication
- Key Management (using Azure Key Vault)
- Error handling
- Logging and monitoring
- Security and compliance

## Component Manifest

A manifest file is maintained in the root directory containing:
- List of all available components
- Cross-reference to required Azure services for each component
- Deployment status and information

For more information about the manifest structure, see the [manifest guidelines](.github/copilot-instructions/manifest-guidelines.md).

## Deployment Workflow

GitHub Actions automate the process of:
1. Testing new or modified components
2. Deploying components to specified Azure subscriptions
3. Updating the manifest with deployment information
4. Discovering deployed services using Azure tags

For more details about GitHub Actions integration, see the [GitHub Actions guidelines](.github/copilot-instructions/github-actions.md).

## Contributing

To contribute a new component to the Azure Components Foundry:
1. Create a new issue describing the component requirements
2. Use GitHub Copilot to help create the component following the template guidelines
3. Ensure all required documentation, examples, and tests are included
4. Submit a pull request for review

All contributions should adhere to the guidelines specified in the Copilot instructions.

## Getting Started

To get started with the Azure Components Foundry:
1. Clone this repository
2. Review the component guidelines in `.github/copilot-instructions`
3. Set up the required Azure resources for component deployment
   - See [Azure Setup Guide](docs/Azure_Setup.md) for detailed instructions
   - Use the devcontainer for seamless development with Azure
4. Explore existing components in the components gallery

## Azure Integration

The Azure Components Foundry provides seamless Azure integration:
- Secure authentication in both devcontainers and GitHub Actions
- Automatic detection of environment and appropriate authentication method
- Service principal support for non-interactive environments
- Helper utilities in the common/authentication module

For detailed setup instructions, refer to the [Azure Setup Guide](docs/Azure_Setup.md).
