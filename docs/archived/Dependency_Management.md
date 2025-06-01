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

With the unified architecture pattern, dependency management follows this flatter structure:

```
azure-components-foundry/
├── pyproject.toml          # Root project dependencies
├── poetry.lock             # Lock file for root dependencies
├── Dockerfile              # Single Dockerfile for all components
├── components/
│   ├── word_count/         # Component directory (flat structure)
│   │   ├── pyproject.toml      # Component-specific dependencies
│   │   ├── poetry.lock         # Lock file for component dependencies
│   │   ├── requirements.txt    # Generated for compatibility
│   │   ├── defaults.yaml       # Component configuration defaults
│   │   └── src/
│   │       └── component.py    # Component implementation with predict() function
│   └── other_component/
│       └── ...
├── runtime/
│   ├── dispatcher.py       # Central dispatcher that selects components
│   ├── azureml_adapter.py  # Azure ML adapter (online/batch)
│   ├── function_adapter.py # Azure Functions adapter
│   └── rest_adapter.py     # REST API adapter for Container Apps
├── deploy/
│   └── manifest.yaml       # Centralized deployment manifest
├── scripts/
│   └── manage_dependencies.py  # Helper script for dependency management
```

This structure ensures that:
1. Each component is self-contained with its own dependencies
2. The unified runtime system handles integration with Azure services
3. Deployment is orchestrated through a central manifest

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

Example from the word_count component:

```toml
[tool.poetry.dependencies]
python = "^3.9"
# Component-specific dependencies
numpy = "^1.22.0"
pandas = "^2.0.0"

# Include shared foundry libraries
azure-components-foundry = {path = "../../", develop = true}

[tool.poetry.group.dev.dependencies]
pytest = "^7.0.0"
pytest-cov = "^4.0.0"
```

With the unified architecture, components are now standalone Python modules with a standardized interface. This allows them to be:
1. Tested independently
2. Selected at runtime by the dispatcher
3. Deployed to multiple Azure services

## Dependency Management Workflows

### Initial Setup

1. Install Poetry following the [official instructions](https://python-poetry.org/docs/#installation)
2. Install root dependencies:
   ```bash
   poetry install
   ```

### Creating a New Component with Dependencies

1. Create the component structure with the unified architecture:
   ```bash
   mkdir -p components/component_name/src components/component_name/tests
   touch components/component_name/src/__init__.py components/component_name/tests/__init__.py
   touch components/component_name/__init__.py components/component_name/defaults.yaml
   ```
   
2. Initialize the component dependencies:
   ```bash
   python scripts/manage_dependencies.py init --component component_name
   ```
   
3. Edit the generated `pyproject.toml` to add component-specific dependencies

4. Create the component environment:
   ```bash
   python scripts/manage_dependencies.py env --component component_name
   ```
   
5. Implement the component interface in `src/component.py`:
   ```python
   from typing import Dict, Any, Union, List

   def predict(input_data: Union[Dict[str, Any], List[Dict[str, Any]], str]) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
       # Component implementation
       pass
   ```

### Working with Component Environments

Each component gets its own isolated virtual environment:

```bash
cd components/component_name
poetry shell
```

You can also work with the root environment, which has access to the runtime system:

```bash
cd /workspaces/copilot
poetry shell
```

### Generating Deployment Files

With the unified architecture, deployment files are generated from the component's dependencies and combined with the runtime system. To generate component-specific compatibility files:

```bash
# From component directory
poetry export --format requirements.txt --output requirements.txt --without-hashes
```

Or use the management script:

```bash
python scripts/manage_dependencies.py env --component component_name
```

For the unified container, the main Dockerfile combines all dependencies:

```bash
# From project root
make build
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

With the unified architecture, a single container image is used for all deployment targets:

- **Azure ML**: Container image with `HANDLER` environment variable set to the component
- **Azure Functions**: Container image with Function adapter enabled
- **Container Apps**: Container image with REST adapter enabled
- **MCP**: Container image with MCP adapter enabled

The deployment manifest (`deploy/manifest.yaml`) specifies which component to deploy to each environment and service.

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