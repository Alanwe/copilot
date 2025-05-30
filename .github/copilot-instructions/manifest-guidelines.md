# Manifest Guidelines

This document describes the structure and maintenance of the components manifest file for the Azure Components Foundry.

## Manifest Location

The manifest file should be located at `/manifest.json` in the root directory of the project.

## Manifest Structure

The manifest should be a JSON file with the following structure:

```json
{
  "last_updated": "YYYY-MM-DD",
  "components": [
    {
      "id": "unique-component-id",
      "name": "Component Name",
      "path": "components/service_name/component_name",
      "description": "Brief description of component",
      "version": "1.0.0",
      "azure_services": [
        {
          "name": "Azure Service 1",
          "type": "required"
        },
        {
          "name": "Azure Service 2",
          "type": "optional"
        }
      ],
      "deployment": {
        "status": "deployed|pending|failed",
        "subscription_id": "subscription-id",
        "resource_group": "resource-group-name",
        "deployment_date": "YYYY-MM-DD",
        "tags": [
          "tag1",
          "tag2"
        ]
      }
    }
  ],
  "azure_services": [
    {
      "name": "Azure ML",
      "components": ["component-id-1", "component-id-2"]
    },
    {
      "name": "Azure Functions",
      "components": ["component-id-3"]
    }
  ]
}
```

## Manifest Maintenance

The manifest file should be updated:
1. When a new component is added to the repository
2. When a component is updated or modified
3. After successful deployment of a component
4. When deployment status changes

## GitHub Actions Integration

GitHub Actions should:

1. Check if new components exist that are not in the manifest
2. Validate manifest integrity
3. Update the manifest after deployment operations
4. Use the manifest to determine which components need to be deployed

## Manual Manifest Update

To manually update the manifest, follow these steps:

1. Add new component information to the "components" array
2. Update the "azure_services" cross-reference section
3. Update the "last_updated" timestamp
4. Validate manifest format with the provided validation script

## Manifest Discovery Script

If GitHub Actions cannot update the manifest directory, a discovery script will:

1. Scan the Azure subscription for deployed components using tags
2. Compare discovered components with the manifest
3. Update the manifest with new deployment information
4. Log discrepancies between discovered components and the manifest

This ensures that the manifest stays in sync with the actual deployed components, even if there are manual deployments or changes outside of the GitHub Actions workflow.