# Administration Scripts for Azure Components Foundry

This directory contains administration scripts that support the Azure Components Foundry in terms of setup, configuration, discovery, testing, and deployment. These scripts are designed to work together and build on top of each other to provide a comprehensive administration experience.

## Available Scripts

### Azure Setup and Configuration

- `azure_setup.py`: Configures Azure resources required by the foundry, including resource groups, key vaults, and service principals.

### Component Management

- `discover_components.py`: Discovers and registers components in the foundry, updating the component manifest.
- `manage_manifest.py`: Manages the component manifest, including validation, updates, and reporting.

### Environment Management

- `env_setup.py`: Sets up local development environments, validates requirements, and ensures proper configuration.

### Testing and Quality Assurance

- `test_components.py`: Orchestrates testing across components and services, generating test reports.

### Deployment

- `deploy_components.py`: Orchestrates deployment across multiple components and services.

## Usage Guidelines

Each script follows a consistent pattern for usage:

```bash
# Basic usage
python admin/script_name.py [command] [options]

# Get help
python admin/script_name.py --help
```

For detailed usage information, run each script with the `--help` option or refer to the specific documentation within each script.

## Best Practices

1. **Automation**: Use these scripts to automate repetitive tasks and ensure consistency.
2. **Configuration Files**: Store configuration in dedicated files rather than hardcoding values.
3. **Credentials**: Never store credentials in scripts or commit them to the repository.
4. **Logging**: Enable appropriate logging for better troubleshooting.
5. **Error Handling**: Always check for errors and provide meaningful messages.

## Dependencies

These scripts generally depend on:

- Azure CLI (for Azure operations)
- Azure SDK for Python (for programmatic access to Azure)
- Poetry (for dependency management)

Ensure these tools are installed and properly configured before using the administration scripts.