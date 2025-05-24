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

3. **Local Development Environment**:
   - Install Python 3.8 or later
   - Install Azure CLI (latest version)
   - Install az ml extension if working with Azure ML components
   - Configure Azure CLI authentication (`az login`)

## Initial Configuration

### Azure Authentication Setup

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

### Testing Components Locally

1. Navigate to the component directory:
   ```bash
   cd components/{service_name}/{component_name}
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run local tests:
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

By following these instructions, you'll be able to effectively work with the Azure Components Foundry, handling the tasks that GitHub Copilot can't automate.