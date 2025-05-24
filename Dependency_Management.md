# Dependency Management for Azure Components Foundry

This document outlines the dependency management approach for the Azure Components Foundry, explaining how dependencies are managed at both project and component levels.

## Overview

The Azure Components Foundry uses a hybrid approach to dependency management that balances:
- Component encapsulation
- Dependency conflict prevention
- Ease of management
- Compatibility with various Azure deployment targets

## Tools and Approaches

We use the following tools to manage dependencies:

### Primary Tool: Poetry

[Poetry](https://python-poetry.org/) is our primary dependency management tool, used to:
- Define project and component dependencies
- Create isolated virtual environments
- Generate lock files for reproducible builds
- Export dependencies to other formats when needed

### Alternative Formats for Compatibility

For compatibility with different deployment targets, we also support:

- **requirements.txt**: For traditional pip-based workflows and Azure Functions
- **environment.yml**: For conda environments and Azure ML workspaces
- **Dockerfile**: For containerized deployments

## Project Structure

Dependency management follows this structure:

```
azure-components-foundry/
├── pyproject.toml          # Root project dependencies
├── poetry.lock             # Lock file for root dependencies
├── components/
│   ├── service_name/
│   │   ├── component_name/
│   │   │   ├── pyproject.toml     # Component-specific dependencies
│   │   │   ├── poetry.lock        # Lock file for component dependencies
│   │   │   ├── requirements.txt    # Generated for compatibility
│   │   │   ├── environment.yml     # For conda/Azure ML compatibility
│   │   │   └── Dockerfile          # For containerized deployments
├── scripts/
│   └── manage_dependencies.py      # Helper script for dependency management
```

## Managing Dependencies

### Root Project Dependencies

The root `pyproject.toml` defines common dependencies used across the project:

```toml
[tool.poetry.dependencies]
python = "^3.8"
azure-identity = "^1.15.0"
azure-keyvault-secrets = "^4.7.0"
azure-storage-blob = "^12.19.0"
pydantic = "^2.5.0"
```

### Component-Specific Dependencies

Each component has its own `pyproject.toml` with:
1. Component-specific dependencies
2. A reference to the root project
3. Development dependencies for testing

Example:

```toml
[tool.poetry.dependencies]
python = "^3.8"
# Component-specific dependencies
nltk = "^3.8.1"

# Include shared foundry libraries
azure-components-foundry = {path = "../../../", develop = true}
```

## Dependency Management Workflows

### Initial Setup

1. Install Poetry following the [official instructions](https://python-poetry.org/docs/#installation)
2. Install root dependencies:
   ```bash
   poetry install
   ```

### Creating a New Component with Dependencies

1. Create the component structure:
   ```bash
   mkdir -p components/service_name/component_name
   ```
2. Initialize the component dependencies:
   ```bash
   python scripts/manage_dependencies.py init --service service_name --component component_name
   ```
3. Edit the generated `pyproject.toml` to add component-specific dependencies
4. Create the component environment:
   ```bash
   python scripts/manage_dependencies.py env --service service_name --component component_name
   ```

### Working with Component Environments

Each component gets its own isolated virtual environment:

```bash
cd components/service_name/component_name
poetry shell
```

### Generating Deployment Files

To generate compatibility files for deployment:

```bash
# From component directory
poetry export --format requirements.txt --output requirements.txt --without-hashes
```

Or use the management script:

```bash
python scripts/manage_dependencies.py env --service service_name --component component_name
```

## Environment Management Considerations

### Development Environment

Developers can:
1. Use the root Poetry environment for general work
2. Switch to component-specific environments for component development
3. Use IDE integration with Poetry for a seamless experience

### CI/CD Environment

CI/CD workflows should:
1. Install Poetry
2. Install dependencies from lockfiles for reproducibility
3. Generate appropriate deployment files for the target platform

### Deployment Environment

Depending on the deployment target:

- **Azure Functions**: Use generated `requirements.txt`
- **Azure ML**: Use generated `environment.yml` or Docker containers
- **Containerized Deployments**: Use the component's `Dockerfile`

## Best Practices

1. **Version Constraints**:
   - Use caret (`^`) constraints for flexibility with safety
   - Pin versions only when necessary for compatibility

2. **Dependency Conflicts**:
   - Resolve conflicts in component-level pyproject.toml
   - Maintain consistency with common dependencies

3. **Environment Isolation**:
   - Use isolated environments for component development
   - Don't mix dependencies between components

4. **Updating Dependencies**:
   - Regularly update dependencies for security
   - Test thoroughly after updates
   - Update lock files after verification

5. **Documentation**:
   - Document component-specific dependency requirements
   - Explain any complex dependency constraints

## Conclusion

This dependency management approach provides a balance between:
- **Encapsulation**: Each component manages its own dependencies
- **Consistency**: Common dependencies are managed centrally
- **Flexibility**: Multiple deployment targets are supported
- **Simplicity**: Helper scripts simplify management tasks

By following these guidelines, you'll maintain clean dependency management across all components in the Azure Components Foundry.