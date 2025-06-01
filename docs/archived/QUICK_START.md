# Azure Components Foundry Quick Start Guide

This quick start guide will help you get up and running with the Azure Components Foundry using Visual Studio Code tasks.

## Prerequisites

1. **Azure Account**: Active Azure account with appropriate permissions
2. **Visual Studio Code**: Latest version with Azure extensions installed
3. **Azure CLI**: Installed and updated to the latest version

## Step 1: Azure Login

Use the VS Code task to login:

1. Press `Ctrl+Shift+P` (Windows/Linux) or `Cmd+Shift+P` (Mac)
2. Type "Tasks: Run Task"
3. Select "Azure: Login"

If you're in a headless environment, use "Azure: Login with device code" instead.

## Step 2: Select Your Subscription

1. Press `Ctrl+Shift+P` or `Cmd+Shift+P`
2. Type "Tasks: Run Task" 
3. Select "Azure: Set subscription"
4. Enter your subscription ID when prompted

## Step 3: Create a New Component

1. Create the component directory structure:
   ```
   components/
   └── my_component/
       ├── __init__.py
       ├── src/
       │   └── component.py
       ├── tests/
       ├── README.md
       └── requirements.txt
   ```

2. Implement the component.py file with a `predict` function.
3. Run a quick test to verify your component.

## Step 4: Add Component to Deployment Manifest

Edit the `/deploy/manifest.yaml` file to add your component:

```yaml
groups:
  dev-eastus:
    subscription: "your-subscription-id"
    resourceGroup: "rg-components-dev"
    region: "eastus"
    deployments:
      - component: my_component
        services: [containerapp]
        overrides:
          min_replicas: 1
```

## Step 5: Deploy Your Component

Run the deployment script:

```bash
python admin/deploy_components.py deploy --group dev-eastus --component my_component
```

## Step 6: Verify Deployment

List all resources to verify your deployment:

1. Press `Ctrl+Shift+P` or `Cmd+Shift+P`
2. Type "Tasks: Run Task"
3. Select "Azure ML: List online endpoints" (or appropriate service listing task)

Or use the built-in discovery script:

```bash
python admin/discover_components.py list-resources --resource-group "rg-components-dev"
```

## Next Steps

- Review the `USER_GUIDE.md` for comprehensive documentation
- Explore the `docs/Practical_Examples.md` for detailed examples
- Check out existing components in the components/ directory
