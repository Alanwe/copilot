# Azure Setup and Configuration Guide

This guide provides detailed instructions on setting up and configuring Azure resources for the Azure Components Foundry project, with a focus on security best practices and proper authentication methods.

## Prerequisites

- An active Azure account with appropriate permissions
- Administrative access on your local machine to install software

## Installing Azure CLI

Azure CLI is the command-line interface for Azure that enables you to create and manage Azure resources directly from your terminal.

### Automated Installation

You can use our environment setup script to automatically install the Azure CLI:

```bash
python admin/env_setup.py install --azure-cli
```

### Manual Installation by Platform

#### Windows

1. Download the MSI installer from [Microsoft's official download page](https://aka.ms/installazurecliwindows)
2. Run the installer and follow the on-screen instructions
3. Restart your terminal or command prompt

#### macOS

Using Homebrew:
```bash
brew update && brew install azure-cli
```

Alternatively, using the official installer script:
```bash
curl -L https://aka.ms/InstallAzureCli | bash
```

#### Linux - Ubuntu/Debian

```bash
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash
```

#### Linux - Other Distributions

Please refer to [Microsoft's official documentation](https://docs.microsoft.com/en-us/cli/azure/install-azure-cli-linux) for specific instructions.

## Installing Azure CLI Extensions

Azure CLI extensions provide additional functionality beyond the core commands. Several extensions are useful for working with specific Azure services.

### Using Our Scripts

To install recommended extensions:
```bash
python admin/env_setup.py install --azure-extensions
```

To install specific extensions:
```bash
python admin/env_setup.py install --azure-extensions azure-devops storage-preview
```

To update existing extensions:
```bash
python admin/env_setup.py install --upgrade-extensions
```

### Manual Management

List installed extensions:
```bash
az extension list
```

Add an extension:
```bash
az extension add --name <extension-name>
```

Update all extensions:
```bash
az extension update --all
```

## Authentication Methods

Azure offers several authentication methods, each suited to different scenarios. This section outlines the recommended approaches for both interactive development and automated scenarios.

### Interactive Login (Development)

For local development, interactive login is the simplest approach:

```bash
az login
```

This will open a browser window for you to sign in. If you're working on a machine without a browser:

```bash
az login --use-device-code
```

### Service Principals (Automation & CI/CD)

For automated processes like CI/CD pipelines, service principals are recommended:

1. Create a service principal:
   ```bash
   az ad sp create-for-rbac --name "MyServicePrincipal" --role contributor \
                            --scopes /subscriptions/{subscription-id}/resourceGroups/{resource-group} \
                            --sdk-auth
   ```

2. Save the JSON output securely - this contains sensitive credentials!

3. For GitHub Actions, add this JSON output as a repository secret named `AZURE_CREDENTIALS`

4. Use the service principal for authentication:
   ```bash
   az login --service-principal --username APP_ID --password PASSWORD --tenant TENANT_ID
   ```

### Managed Identity (Azure Services)

When running code on Azure resources (VMs, App Services, etc.), Managed Identity provides a secure authentication method without managing credentials:

1. Assign a managed identity to your Azure resource
2. Grant appropriate permissions to the identity
3. Code running on that resource can authenticate automatically:
   ```bash
   az login --identity
   ```

## Security Best Practices

### Credential Management

1. **Never store credentials in code or commit them to repositories**
   - Use environment variables or secure storage like Azure Key Vault

2. **Follow least privilege principle**
   - Grant only the permissions needed for the task
   - Use scoped roles instead of broad permissions

3. **Rotate credentials regularly**
   - Update service principal secrets periodically
   - Automate rotation where possible

### Using Azure Key Vault

For sensitive configuration values:

1. Create a Key Vault:
   ```bash
   az keyvault create --name <vault-name> --resource-group <resource-group> --location <location>
   ```

2. Store a secret:
   ```bash
   az keyvault secret set --vault-name <vault-name> --name <secret-name> --value <secret-value>
   ```

3. Grant access to a service principal:
   ```bash
   az keyvault set-policy --name <vault-name> --spn <service-principal-id> \
                          --secret-permissions get list
   ```

### Working with Multiple Azure Environments

To manage multiple environments (dev, test, prod):

1. List available accounts:
   ```bash
   az account list --output table
   ```

2. Set your active subscription:
   ```bash
   az account set --subscription <subscription-id>
   ```

3. Create separate service principals and configuration for each environment

## Example Configuration Workflow

1. Set up Azure CLI and extensions:
   ```bash
   python admin/env_setup.py install --azure-cli --azure-extensions
   ```

2. Log in to Azure:
   ```bash
   az login
   ```

3. Configure your environment:
   ```bash
   python admin/env_setup.py setup-azure --subscription <subscription-id> --resource-group <resource-group>
   ```

4. Create Azure resources:
   ```bash
   python admin/azure_setup.py interactive
   ```

5. Create a service principal for automation:
   ```bash
   python admin/azure_setup.py service-principal --name "MyServicePrincipal" \
                            --role contributor \
                            --scope "/subscriptions/{subscription-id}" \
                            --output-file sp-credentials.json
   ```

6. Store your credentials securely and then remove the credentials file:
   ```bash
   # After saving to secure location
   rm sp-credentials.json
   ```

## Troubleshooting

### Common Issues

1. **Authentication failures**:
   - Check that credentials are valid and haven't expired
   - Verify permissions assigned to the user/service principal
   - Confirm you're using the correct tenant and subscription

2. **Missing extensions**:
   - Verify extension is installed: `az extension list`
   - Try reinstalling the extension: `az extension add --name <name> --force`

3. **Permission denied errors**:
   - Check your role assignments: `az role assignment list --assignee <your-login>`
   - Verify scope of permissions matches the resources you're accessing

### Getting Help

- Azure CLI help: `az --help` or `az <command> --help`
- Extension help: `az <extension-name> --help`
- For additional support, please refer to [Azure's official documentation](https://docs.microsoft.com/en-us/azure/)