# GitHub Actions Guidelines

This document outlines how GitHub Actions should be set up and used for the Azure Components Foundry project.

## Workflow Overview

The project should utilize GitHub Actions for:
1. Testing components
2. Deploying components to Azure
3. Updating the component manifest
4. Discovering deployed components with tags

## Required Workflows

### 1. Component Testing Workflow

File: `.github/workflows/test-components.yml`

This workflow should:
- Trigger on pull requests to main branch
- Identify modified components
- Set up Python environment
- Install component dependencies
- Run component tests
- Report test results
- Fail the PR if tests fail

### 2. Component Deployment Workflow

File: `.github/workflows/deploy-components.yml`

This workflow should:
- Trigger on push to main branch
- Identify new or modified components since last deployment
- Authenticate with Azure using service principal
- Deploy components to the specified Azure subscription
- Tag deployed resources with component metadata
- Update the manifest with deployment information
- Report deployment status

### 3. Manifest Update Workflow

File: `.github/workflows/update-manifest.yml`

This workflow should:
- Trigger on schedule (daily) or manually
- Scan the Azure subscription for tagged resources
- Compare discovered resources with the manifest
- Update the manifest with any discrepancies
- Commit and push manifest changes

## Secrets and Environment Configuration

Required GitHub repository secrets:
- `AZURE_CREDENTIALS`: Service principal credentials for Azure authentication
- `AZURE_SUBSCRIPTION_ID`: Target Azure subscription ID
- `AZURE_RESOURCE_GROUP`: Default resource group for deployments

## Workflow Templates

### Authentication with Azure

```yaml
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v2
      
      - name: Azure login
        uses: azure/login@v1
        with:
          creds: ${{ secrets.AZURE_CREDENTIALS }}
```

### Detecting Changed Components

```yaml
jobs:
  detect_changes:
    runs-on: ubuntu-latest
    outputs:
      changed_components: ${{ steps.find_changes.outputs.changed_components }}
    steps:
      - name: Checkout code
        uses: actions/checkout@v2
        with:
          fetch-depth: 0
      
      - name: Find changed components
        id: find_changes
        run: |
          CHANGED_FILES=$(git diff --name-only ${{ github.event.before }} ${{ github.sha }})
          COMPONENTS=$(echo "$CHANGED_FILES" | grep -o 'components/[^/]*/[^/]*' | sort | uniq)
          echo "::set-output name=changed_components::$COMPONENTS"
```

### Tagging Resources

When deploying resources, use the following tags:
- `component-id`: Unique component identifier
- `component-version`: Component version
- `deployment-source`: "github-actions"
- `deployment-date`: Timestamp of deployment

These tags are essential for the discovery script to identify deployed components.