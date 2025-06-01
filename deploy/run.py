#!/usr/bin/env python3
"""
Deployment orchestrator for the unified Azure Components Foundry.
This script handles deployment based on the YAML manifest and template-based generation.
Supports multiple Azure services: AML, Functions, Container Apps, and MCP.
"""

import argparse
import json
import logging
import os
import re
import subprocess
import sys
import tempfile
import time
import yaml
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
from string import Template
from typing import Dict, List, Any, Union, Optional, Tuple


def setup_logging(verbose: bool = False):
    """Configure logging based on verbosity level."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt="%Y-%m-%d %H:%M:%S"
    )


def load_manifest(manifest_path: str) -> Dict[str, Any]:
    """Load the deployment manifest."""
    try:
        with open(manifest_path, 'r') as f:
            manifest = yaml.safe_load(f)
        logging.info(f"Loaded manifest with {len(manifest.get('groups', {}))} group(s)")
        return manifest
    except Exception as e:
        logging.error(f"Failed to load manifest: {e}")
        sys.exit(1)


def set_subscription(subscription_id: str):
    """Set the active Azure subscription."""
    try:
        cmd = ["az", "account", "set", "--subscription", subscription_id]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise Exception(f"Failed to set subscription: {result.stderr}")
        logging.info(f"Set active subscription: {subscription_id}")
    except Exception as e:
        logging.error(f"Error setting subscription: {e}")
        raise


def render_template(template_path: str, variables: Dict[str, Any]) -> str:
    """Render a template with variable substitution."""
    try:
        with open(template_path, 'r') as f:
            template_content = f.read()
        
        # Simple token replacement
        for key, value in variables.items():
            token = f"${{{{{key}}}}}"
            template_content = template_content.replace(token, str(value))
        
        return template_content
    except Exception as e:
        logging.error(f"Failed to render template {template_path}: {e}")
        raise


def deploy_aml_online(deployment_vars: Dict[str, Any], template_dir: Path) -> bool:
    """Deploy to Azure ML online endpoint."""
    try:
        logging.info(f"Deploying to Azure ML online endpoint: {deployment_vars['ENDPOINT_NAME']}")
        
        # Render template
        template_content = render_template(
            template_dir / "aml-online.yml", 
            deployment_vars
        )
        
        # Write temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
            f.write(template_content)
            temp_file = f.name
        
        try:
            # Create/update endpoint
            endpoint_cmd = [
                "az", "ml", "online-endpoint", "create",
                "--name", deployment_vars['ENDPOINT_NAME'],
                "--workspace-name", deployment_vars['WORKSPACE_NAME'],
                "--resource-group", deployment_vars['RESOURCE_GROUP']
            ]
            
            subprocess.run(endpoint_cmd, check=False)  # May already exist
            
            # Create/update deployment
            deploy_cmd = [
                "az", "ml", "online-deployment", "create",
                "--file", temp_file,
                "--workspace-name", deployment_vars['WORKSPACE_NAME'],
                "--resource-group", deployment_vars['RESOURCE_GROUP'],
                "--all-traffic"
            ]
            
            result = subprocess.run(deploy_cmd, capture_output=True, text=True)
            if result.returncode != 0:
                logging.error(f"AML deployment failed: {result.stderr}")
                return False
                
            logging.info("Azure ML online deployment successful")
            return True
            
        finally:
            os.unlink(temp_file)
            
    except Exception as e:
        logging.error(f"Error in AML online deployment: {e}")
        return False


def deploy_aml_batch(deployment_vars: Dict[str, Any], template_dir: Path) -> bool:
    """Deploy to Azure ML batch endpoint."""
    try:
        logging.info(f"Deploying to Azure ML batch endpoint: {deployment_vars['ENDPOINT_NAME']}")
        
        # Render template
        template_content = render_template(
            template_dir / "aml-batch.yml", 
            deployment_vars
        )
        
        # Write temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
            f.write(template_content)
            temp_file = f.name
        
        try:
            # Create/update batch endpoint
            endpoint_cmd = [
                "az", "ml", "batch-endpoint", "create",
                "--name", deployment_vars['ENDPOINT_NAME'],
                "--workspace-name", deployment_vars['WORKSPACE_NAME'],
                "--resource-group", deployment_vars['RESOURCE_GROUP']
            ]
            
            subprocess.run(endpoint_cmd, check=False)  # May already exist
            
            # Create/update deployment
            deploy_cmd = [
                "az", "ml", "batch-deployment", "create",
                "--file", temp_file,
                "--workspace-name", deployment_vars['WORKSPACE_NAME'],
                "--resource-group", deployment_vars['RESOURCE_GROUP'],
                "--set-default"
            ]
            
            result = subprocess.run(deploy_cmd, capture_output=True, text=True)
            if result.returncode != 0:
                logging.error(f"AML batch deployment failed: {result.stderr}")
                return False
                
            logging.info("Azure ML batch deployment successful")
            return True
            
        finally:
            os.unlink(temp_file)
            
    except Exception as e:
        logging.error(f"Error in AML batch deployment: {e}")
        return False


def deploy_function(deployment_vars: Dict[str, Any], template_dir: Path) -> bool:
    """Deploy to Azure Functions."""
    try:
        logging.info(f"Deploying to Azure Function: {deployment_vars['FUNCTION_APP_NAME']}")
        
        # Update function app with container image and handler
        cmd = [
            "az", "functionapp", "config", "container", "set",
            "--name", deployment_vars['FUNCTION_APP_NAME'],
            "--resource-group", deployment_vars['RESOURCE_GROUP'],
            "--image", deployment_vars['IMAGE_URI']
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            logging.error(f"Function container update failed: {result.stderr}")
            return False
        
        # Set handler environment variable
        env_cmd = [
            "az", "functionapp", "config", "appsettings", "set",
            "--name", deployment_vars['FUNCTION_APP_NAME'],
            "--resource-group", deployment_vars['RESOURCE_GROUP'],
            "--settings", f"HANDLER={deployment_vars['HANDLER']}"
        ]
        
        result = subprocess.run(env_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            logging.error(f"Function app settings update failed: {result.stderr}")
            return False
            
        logging.info("Azure Functions deployment successful")
        return True
        
    except Exception as e:
        logging.error(f"Error in Functions deployment: {e}")
        return False


def deploy_containerapp(deployment_vars: Dict[str, Any], template_dir: Path) -> bool:
    """Deploy to Azure Container Apps."""
    try:
        logging.info(f"Deploying to Container App: {deployment_vars['CONTAINER_APP_NAME']}")
        
        # Update container app
        cmd = [
            "az", "containerapp", "update",
            "--name", deployment_vars['CONTAINER_APP_NAME'],
            "--resource-group", deployment_vars['RESOURCE_GROUP'],
            "--image", deployment_vars['IMAGE_URI'],
            "--env-vars", f"HANDLER={deployment_vars['HANDLER']}"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            logging.error(f"Container app update failed: {result.stderr}")
            return False
            
        logging.info("Container Apps deployment successful")
        return True
        
    except Exception as e:
        logging.error(f"Error in Container Apps deployment: {e}")
        return False


def build_deployment_vars(manifest: Dict, group_name: str, deployment: Dict, image_uri: str) -> Dict[str, Any]:
    """Build deployment variables from manifest and overrides."""
    group = manifest['groups'][group_name]
    component_name = deployment['component']
    
    # Start with global defaults
    vars_dict = manifest.get('defaults', {}).copy()
    
    # Add component-specific defaults
    component_defaults = manifest.get('components', {}).get(component_name, {}).get('defaults', {})
    vars_dict.update(component_defaults)
    
    # Add deployment-specific overrides
    vars_dict.update(deployment.get('overrides', {}))
    
    # Add required deployment variables
    vars_dict.update({
        'IMAGE_URI': image_uri,
        'HANDLER': manifest.get('components', {}).get(component_name, {}).get('handler', f'components.{component_name}.src.component:predict'),
        'COMPONENT_NAME': component_name,
        'RESOURCE_GROUP': group['resourceGroup'],
        'REGION': group['region'],
        'DEPLOY_NAME': f"{component_name}-deploy",
        'ENDPOINT_NAME': f"{component_name}-endpoint",
        'WORKSPACE_NAME': f"ml-{group['resourceGroup']}",
        'FUNCTION_APP_NAME': f"func-{component_name}",
        'CONTAINER_APP_NAME': f"ca-{component_name}",
        'ENVIRONMENT_NAME': f"env-{group['resourceGroup']}",
        'COMPUTE_NAME': f"cpu-{component_name}",
        'FUNCTION_ROUTE': f"{component_name}/{{*route}}",
        'MINI_BATCH_SIZE': 10,
        'MAX_CONCURRENCY': 4
    })
    
    return vars_dict


def deploy_group(manifest: Dict, group_name: str, image_uri: str, services_filter: List[str] = None, dry_run: bool = False) -> bool:
    """Deploy all components in a group."""
    group = manifest['groups'][group_name]
    template_dir = Path(__file__).parent / "templates"
    
    logging.info(f"Deploying group: {group_name}")
    
    # Set subscription
    if not dry_run:
        set_subscription(group['subscription'])
    
    success_count = 0
    total_count = 0
    
    for deployment in group['deployments']:
        component_name = deployment['component']
        services = deployment['services']
        
        # Apply services filter if provided
        if services_filter:
            services = [s for s in services if s in services_filter]
            if not services:
                continue
        
        logging.info(f"Deploying component {component_name} to services: {services}")
        
        # Build deployment variables
        deployment_vars = build_deployment_vars(manifest, group_name, deployment, image_uri)
        
        if dry_run:
            logging.info(f"[DRY RUN] Would deploy {component_name} with vars: {deployment_vars}")
            continue
        
        # Deploy to each service
        for service in services:
            total_count += 1
            
            try:
                if service == "aml_online":
                    success = deploy_aml_online(deployment_vars, template_dir)
                elif service == "aml_batch":
                    success = deploy_aml_batch(deployment_vars, template_dir)
                elif service == "function":
                    success = deploy_function(deployment_vars, template_dir)
                elif service == "containerapp":
                    success = deploy_containerapp(deployment_vars, template_dir)
                else:
                    logging.error(f"Unknown service type: {service}")
                    success = False
                
                if success:
                    success_count += 1
                    logging.info(f"✓ {component_name} -> {service}")
                else:
                    logging.error(f"✗ {component_name} -> {service}")
                    
            except Exception as e:
                logging.error(f"✗ {component_name} -> {service}: {e}")
    
    logging.info(f"Group {group_name} deployment complete: {success_count}/{total_count} successful")
    return success_count == total_count


def main():
    """Main deployment orchestrator."""
    parser = argparse.ArgumentParser(description="Azure Components Foundry Deployment Orchestrator")
    
    parser.add_argument("--manifest", default="deploy/manifest.yaml", help="Path to deployment manifest")
    parser.add_argument("--image", required=True, help="Container image URI (e.g., myacr.azurecr.io/components:tag)")
    parser.add_argument("--group", help="Deploy specific group only")
    parser.add_argument("--service", action="append", help="Deploy to specific service types only (can be repeated)")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be deployed without deploying")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose logging")
    
    args = parser.parse_args()
    
    setup_logging(args.verbose)
    
    # Load manifest
    manifest = load_manifest(args.manifest)
    
    # Deploy groups
    if args.group:
        # Deploy specific group
        if args.group not in manifest['groups']:
            logging.error(f"Group {args.group} not found in manifest")
            sys.exit(1)
        
        success = deploy_group(manifest, args.group, args.image, args.service, args.dry_run)
        sys.exit(0 if success else 1)
    else:
        # Deploy all groups
        all_success = True
        for group_name in manifest['groups']:
            success = deploy_group(manifest, group_name, args.image, args.service, args.dry_run)
            all_success = all_success and success
        
        sys.exit(0 if all_success else 1)


if __name__ == "__main__":
    main()
