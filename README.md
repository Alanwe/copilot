# Azure Components Foundry

A foundry for creating reusable components for Azure cloud services using Python with a unified architecture pattern that enables deployment to multiple Azure runtimes from a single codebase. This project provides a unified approach to deploy the same component to multiple Azure services from a single implementation.

## Project Overview

The Azure Components Foundry is designed to:
- Create reusable, well-documented components for Azure cloud services
- Implement best practices for component creation including documentation, examples, and tests
- Provide a unified architecture pattern for deploying components to multiple Azure runtimes
- Use a single container image + dispatcher approach for component selection
- Orchestrate deployments using a centralized YAML manifest
- Maintain a central gallery of components for easy discovery and reuse

## Supported Azure Services

Components can be created and deployed for the following Azure services:
- Azure ML Components and pipelines (YAML/AzureML SDK V2 only)
- Azure ML Batch Inference
- Azure ML Endpoints
- Azure Functions
- Azure Managed Endpoints Serverless
- REST/OpenAI/Swagger MCP

## Component Structure

Each component follows the unified architecture pattern that includes:
- A simple `predict(input_data)` function that processes inputs and returns outputs
- Support for string, dictionary, and batch input formats
- Comprehensive documentation
- Unit tests for validation
- Integration with the unified runtime dispatcher

Components are designed to work with a central dispatcher that selects them at runtime based on environment variables, allowing the same container image to be used across different Azure services.

For detailed component guidelines and examples, see the [User Guide](/USER_GUIDE.md).

## Component Gallery

Components are organized in a gallery structure under the `/components` directory. Each component is a Python module with a standardized structure that works with the unified runtime system.

Deployment is handled through a central manifest in `/deploy/manifest.yaml` that specifies:
- Which components to deploy to which environments
- What Azure services to use (AML Online, AML Batch, Functions, Container Apps)
- Configuration overrides for each deployment

See [Practical Examples](/docs/Practical_Examples.md) for detailed examples of deployment configurations.

All components adhere to Azure best practices for:
- Authentication
- Key Management (using Azure Key Vault)
- Error handling
- Logging and monitoring
- Security and compliance

## Runtime System

The unified runtime system consists of:

- **Dispatcher**: Central module that loads and invokes component functions based on the `HANDLER` environment variable
- **Adapters**: Service-specific modules that translate between Azure service protocols and the component interface
- **Container Image**: Single Docker image that can run any component based on environment configuration

This design allows:
- One build, multiple deployments
- Simplified testing and validation
- Consistent behavior across environments
- Horizontal scaling on any Azure runtime

## Component Manifest

A deployment manifest file (`deploy/manifest.yaml`) serves as the single source of truth for all deployments:
- Defines which components are deployed to which environments
- Specifies Azure services to use for each component
- Contains configuration overrides for different environments (dev, test, prod)
- Enables reproducible deployments across environments

The component manifest system allows:
- One-command deployments across multiple services
- Consistent configuration management
- Easy auditing of what's deployed where
- Simplified environment promotion workflows

## Documentation

The Azure Components Foundry includes the following documentation:

- [User Guide](/USER_GUIDE.md) - Comprehensive guide to using the foundry
- [Quick Start](/QUICK_START.md) - Get started quickly with the basics
- [Practical Examples](/docs/Practical_Examples.md) - Step-by-step examples for common tasks

## Getting Started

1. Set up your Azure environment:
   ```bash
   python admin/azure_setup.py setup --subscription "your-subscription-id" --resource-group "your-resource-group"
   ```

2. Create a new component or use an existing one:
   ```bash
   # Example: Test an existing component
   cd components/word_count
   python simple_test.py
   ```

3. Deploy components to Azure:
   ```bash
   python admin/deploy_components.py deploy --group dev-eastus
   ```

4. List your deployed resources:
   ```bash
   python admin/discover_components.py list-resources --resource-group "your-resource-group"
   ```

## Contributing

To contribute a new component to the Azure Components Foundry:
1. Follow the component structure and guidelines in the [User Guide](/USER_GUIDE.md)
2. Create component tests and documentation
3. Submit a pull request for review

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

## Azure Connectivity

If you're experiencing issues connecting to Azure services in the devcontainer environment, you can use the provided connectivity helper:

```bash
# Check Azure connectivity and attempt authentication
./scripts/check_azure.sh
```

This script will:
1. Check network connectivity to Azure endpoints
2. Attempt authentication if connectivity is available
3. Provide helpful guidance if issues are detected

If your devcontainer environment has network restrictions preventing Azure connectivity, you'll need to:
1. Ensure your network allows connections to Azure services (login.microsoftonline.com, etc.)
2. Configure proxy settings if your environment requires a proxy
3. Try manual authentication once connectivity is established

For detailed setup instructions, refer to the [Azure Setup Guide](docs/Azure_Setup.md).

## Local Development

For local development and testing:

```bash
# Clone the repository
git clone https://github.com/example/azure-components-foundry.git
cd azure-components-foundry

# Install dependencies
pip install -r requirements.txt

# Run tests
python -m pytest

# Test a specific component using the dispatcher
python -c "import sys; sys.path.append('.'); from runtime.dispatcher import predict; print(predict({'text': 'Hello world!'}))"

# Run with Docker
docker build -t azure-components-foundry .
docker run -p 8000:8000 -e HANDLER="components.word_count.src.component:predict" azure-components-foundry
```

## Working with Components

To add a new component:

1. Create a directory under `/components/{component_name}` with the required structure
2. Implement the `predict(input_data)` function
3. Add tests in the component's `tests/` directory
4. Update the deployment manifest in `/deploy/manifest.yaml`

To deploy components:

```bash
# Deploy all components defined in the manifest
make deploy

# Deploy to a specific environment
make deploy ENV=dev-eastus
```

See the [User Instructions](User-Instructions.md) for more detailed setup and usage information.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Azure Cloud Services Team
- GitHub Copilot for assistance in component generation
- Contributors to the project
