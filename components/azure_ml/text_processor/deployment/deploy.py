"""
Deployment script for Text Processor component.
"""

import os
import argparse
import json
import logging
import sys

# Add parent directory to path to import from src
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def deploy_to_aml(subscription_id, resource_group, workspace_name, dry_run=False):
    """
    Deploy component to Azure ML.
    
    Args:
        subscription_id: Azure subscription ID
        resource_group: Resource group name
        workspace_name: AzureML workspace name
        dry_run: If True, only print actions without deploying
    """
    logging.info(f"Deploying Text Processor component to AzureML workspace {workspace_name}")
    
    if dry_run:
        logging.info("[DRY RUN] Deployment would happen here")
        return
    
    try:
        from azure.ai.ml import MLClient
        from azure.ai.ml.entities import Component
        from azure.identity import DefaultAzureCredential
        
        # Get credentials
        credential = DefaultAzureCredential()
        
        # Connect to workspace
        ml_client = MLClient(
            credential=credential,
            subscription_id=subscription_id,
            resource_group_name=resource_group,
            workspace_name=workspace_name
        )
        
        # Define component
        component_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "text_processor.yaml"
        )
        
        # Register component
        component = Component.load(source=component_path)
        registered_component = ml_client.components.create_or_update(component)
        
        logging.info(f"Component registered: {registered_component.name} (version: {registered_component.version})")
        
    except ImportError:
        logging.error("Azure ML SDK not installed. Run 'pip install azure-ai-ml'")
        sys.exit(1)
    except Exception as e:
        logging.error(f"Error deploying component: {str(e)}")
        sys.exit(1)


def deploy_to_functions(subscription_id, resource_group, function_app_name, dry_run=False):
    """
    Deploy component to Azure Functions.
    
    Args:
        subscription_id: Azure subscription ID
        resource_group: Resource group name
        function_app_name: Azure Function App name
        dry_run: If True, only print actions without deploying
    """
    logging.info(f"Deploying Text Processor component to Azure Function App {function_app_name}")
    
    if dry_run:
        logging.info("[DRY RUN] Deployment would happen here")
        return
    
    try:
        import subprocess
        
        # Create deployment package
        component_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        # Deploy using Azure CLI
        logging.info(f"Deploying to Function App {function_app_name}")
        subprocess.run([
            "az", "functionapp", "deployment", "source", "config-zip",
            "-g", resource_group,
            "-n", function_app_name,
            "--src", f"{component_dir}/function_deployment.zip"
        ], check=True)
        
        logging.info("Function App deployment completed")
        
    except Exception as e:
        logging.error(f"Error deploying component: {str(e)}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Deploy Text Processor Component")
    parser.add_argument("--subscription", required=True, help="Azure subscription ID")
    parser.add_argument("--resource-group", required=True, help="Azure resource group name")
    parser.add_argument("--target", choices=["aml", "functions", "all"], default="aml",
                      help="Deployment target (aml, functions, or all)")
    parser.add_argument("--workspace", help="AzureML workspace name (required for AML deployment)")
    parser.add_argument("--function-app", help="Function App name (required for Functions deployment)")
    parser.add_argument("--dry-run", action="store_true", help="Perform a dry run without deploying")
    
    args = parser.parse_args()
    
    # Configure logging
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    
    # Validate arguments
    if args.target in ["aml", "all"] and not args.workspace:
        logging.error("--workspace argument is required for AzureML deployment")
        sys.exit(1)
    
    if args.target in ["functions", "all"] and not args.function_app:
        logging.error("--function-app argument is required for Azure Functions deployment")
        sys.exit(1)
    
    # Perform deployments
    if args.target in ["aml", "all"]:
        deploy_to_aml(args.subscription, args.resource_group, args.workspace, args.dry_run)
    
    if args.target in ["functions", "all"]:
        deploy_to_functions(args.subscription, args.resource_group, args.function_app, args.dry_run)


if __name__ == "__main__":
    main()