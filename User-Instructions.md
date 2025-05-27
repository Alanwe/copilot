# User Instructions for the Azure Components Foundry

This document provides instructions on how to work with the Azure Components Foundry, focusing specifically on the setup tasks that GitHub Copilot isn't able to perform automatically.

## Prerequisites

Before you can start using the Azure Components Foundry effectively, you'll need to set up:

1. **Azure Account and Subscription**: 
   - Create an Azure account if you don't already have one
   - Set up a subscription with sufficient permissions for deploying Azure resources
   - Ensure you have contributor or owner access to the subscription

2. **Azure Resources Setup**:
   - Create a Resource Group for component deployments
   - Set up Azure Key Vault for secure key management
   - Configure Azure AD permissions and service principals
   - For detailed Azure setup instructions, see [Azure Setup Guide](docs/Azure_Setup.md)

3. **Local Development Environment**:
   - Install Python 3.8 or later
   - Install Azure CLI (latest version)
   - Install Azure CLI extensions required for your components
   - Install az ml extension if working with Azure ML components
   - Install Poetry for dependency management (`curl -sSL https://install.python-poetry.org | python3 -`)
   - Configure Azure CLI authentication (`az login`)
   - For automated setup, use `python admin/env_setup.py setup-all`

## Initial Configuration

### Azure Authentication Setup

For detailed authentication instructions and security best practices, please see the [Azure Setup Guide](docs/Azure_Setup.md#authentication-methods).

1. Create a service principal for GitHub Actions:
   ```bash
   az ad sp create-for-rbac --name "AzureComponentsFoundry" --role contributor \
                          --scopes /subscriptions/{subscription-id} \
                          --sdk-auth
   ```

2. Save the output JSON as a GitHub secret named `AZURE_CREDENTIALS` in your repository.

3. Configure additional required secrets:
   - `AZURE_SUBSCRIPTION_ID`: Your Azure subscription ID
   - `AZURE_RESOURCE_GROUP`: Default resource group for deployments
   - `AZURE_LOCATION`: Default Azure region for deployments (optional, defaults to eastus)

4. You can test your Azure authentication setup by manually triggering the `az-login` workflow from the Actions tab in your GitHub repository.

### Key Vault Configuration

1. Create an Azure Key Vault:
   ```bash
   az keyvault create --name {vault-name} --resource-group {resource-group} --location {location}
   ```

2. Grant access to your service principal:
   ```bash
   az keyvault set-policy --name {vault-name} --spn {service-principal-id} \
                       --secret-permissions get list set delete
   ```

## Administration Scripts

The Azure Components Foundry includes a set of administration scripts in the `/admin` directory to help with setup, configuration, discovery, testing, and deployment tasks:

### Azure Setup and Configuration

```bash
# Interactive guided setup for Azure resources
python admin/azure_setup.py interactive

# Set up all required Azure resources
python admin/azure_setup.py all --resource-group myResourceGroup --location eastus --key-vault myKeyVault --service-principal myServicePrincipal
```

### Component Discovery and Management

```bash
# Discover local components
python admin/discover_components.py local --save

# Discover components deployed in Azure
python admin/discover_components.py azure --subscription your-subscription-id --save

# Discover both local and Azure components
python admin/discover_components.py all --save
```

### Environment Setup and Validation

```bash
# Validate the development environment
python admin/env_setup.py validate

# Set up the complete development environment
python admin/env_setup.py setup-all
```

### Testing Components

```bash
# Test all components
python admin/test_components.py all

# Test a specific component
python admin/test_components.py component --service service_name --component component_name

# Test only components with recent changes
python admin/test_components.py changed
```

### Managing the Component Manifest

```bash
# Validate the manifest structure
python admin/manage_manifest.py validate

# List all components in the manifest
python admin/manage_manifest.py list --format

# Get a summary of the manifest
python admin/manage_manifest.py summary
```

### Deploying Components

```bash
# Deploy all components
python admin/deploy_components.py all --subscription your-subscription-id --resource-group myResourceGroup --update-manifest

# Deploy a specific component
python admin/deploy_components.py component --component-id service-component --subscription your-subscription-id --resource-group myResourceGroup

# Deploy all components for a specific service
python admin/deploy_components.py service --service service_name --subscription your-subscription-id --resource-group myResourceGroup
```

For detailed usage information, run any script with the `--help` option.

## Working with the Foundry

### Creating New Components

1. **Define Requirements**:
   - Create a new issue in GitHub describing the component
   - Include detailed requirements and considerations
   - Apply appropriate tags to the issue

2. **Let GitHub Copilot Assist**:
   - Assign the issue to GitHub Copilot
   - GitHub Copilot will create the initial component structure
   - Review and refine the generated code

3. **Manual Refinements**:
   - Clone the repository locally
   - Review the generated component
   - Make any necessary adjustments
   - Add detailed component documentation

### Managing Component Dependencies

1. **Initialize Component Dependencies**:
   ```bash
   python scripts/manage_dependencies.py init --service {service_name} --component {component_name}
   ```

2. **Edit the Dependencies**:
   - Open the generated `pyproject.toml` in the component directory
   - Add component-specific dependencies under `[tool.poetry.dependencies]`
   - Version dependencies appropriately using `^version` format

3. **Create Component Environment**:
   ```bash
   python scripts/manage_dependencies.py env --service {service_name} --component {component_name}
   ```

4. **Activate the Component Environment**:
   ```bash
   cd components/{service_name}/{component_name}
   poetry shell
   ```

5. **Generate Deployment Files**:
   - Run the manage_dependencies script to update requirements.txt
   - This is done automatically when creating the environment

### Testing Components Locally

1. Navigate to the component directory:
   ```bash
   cd components/{service_name}/{component_name}
   ```

2. Install dependencies using Poetry (preferred):
   ```bash
   poetry install
   ```
   
   Or with pip (alternative):
   ```bash
   pip install -r requirements.txt
   ```

3. Run local tests:
   ```bash
   poetry run pytest
   ```
   
   Or without Poetry:
   ```bash
   python -m pytest
   ```

4. Verify deployment scripts locally:
   ```bash
   az login
   python deployment/deploy.py --dry-run
   ```

### Deploying Components

1. **Automated Deployment via GitHub Actions**:
   - Push changes to the main branch
   - GitHub Actions will automatically deploy any new or modified components
   - Check the workflow execution status for deployment results

2. **Manual Deployment**:
   - Navigate to the component directory
   - Run the deployment script:
     ```bash
     python deployment/deploy.py --subscription {subscription-id} --resource-group {resource-group}
     ```
   - Update the manifest manually if needed

3. **Docker Deployment**:
   - Navigate to the component directory
   - Build the Docker image:
     ```bash
     docker build -t {component-name}:{version} .
     ```
   - Run the container:
     ```bash
     docker run {component-name}:{version}
     ```

4. **Azure ML Environment Deployment**:
   - Use the component's environment.yml file:
     ```bash
     az ml environment create --file environment.yml
     ```
   - Or use the Docker container:
     ```bash
     az ml environment create --image {container-registry}/{component-name}:{version}
     ```

### Updating the Component Manifest

If GitHub Actions cannot update the manifest automatically:

1. Run the discovery script:
   ```bash
   python scripts/discover_components.py
   ```

2. Review and commit the updated manifest:
   ```bash
   git add manifest.json
   git commit -m "Update component manifest"
   git push
   ```

## Troubleshooting

### Common Issues and Solutions

1. **Authentication Failures**:
   - Verify your service principal credentials
   - Check that your service principal has sufficient permissions
   - Run `az login` to refresh your local authentication

2. **Deployment Failures**:
   - Check the resource group for partially deployed resources
   - Review error messages in the GitHub Actions logs
   - Verify that your deployment parameters are correct

3. **Component Discovery Issues**:
   - Ensure that deployed resources are properly tagged
   - Check that the manifest format is valid JSON
   - Verify that the discovery script has access to the subscription

## Best Practices

1. **Version Control**:
   - Create feature branches for new components
   - Use pull requests for code reviews
   - Tag releases with semantic versioning

2. **Documentation**:
   - Keep component documentation up to date
   - Document any manual steps clearly
   - Include usage examples

3. **Testing**:
   - Write comprehensive tests for each component
   - Include edge case scenarios
   - Test deployment scripts with `--dry-run` before actual deployment

4. **Security**:
   - Never commit secrets or credentials to the repository
   - Use Azure Key Vault for all sensitive information
   - Follow the principle of least privilege for all permissions
   - See the [Security Best Practices](docs/Azure_Setup.md#security-best-practices) section in the Azure Setup Guide

5. **Dependency Management**:
   - Keep component dependencies isolated using Poetry
   - Document specific version requirements in pyproject.toml
   - Regularly audit and update dependencies for security
   - Use dependency locking for reproducible builds
   - Generate deployment-specific files (requirements.txt, environment.yml) from Poetry

By following these instructions, you'll be able to effectively work with the Azure Components Foundry, handling the tasks that GitHub Copilot can't automate.