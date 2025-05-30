#!/usr/bin/env python
"""
Deployment orchestration script for the Azure Components Foundry.
This script orchestrates deployment across multiple components and services.
"""

import argparse
import json
import logging
import os
import re
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor


def setup_logging(verbose=False):
    """Configure logging based on verbosity level."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )


def get_repo_root():
    """Get the repository root path."""
    try:
        # Try to get root from git
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, check=True
        )
        return Path(result.stdout.strip())
    except Exception:
        # Fallback: assume script is in admin directory
        return Path(__file__).parent.parent


def load_manifest(manifest_path=None):
    """
    Load the component manifest.
    
    Args:
        manifest_path: Path to the manifest file (optional)
    
    Returns:
        The manifest data as a dictionary.
    """
    # Default manifest path
    if manifest_path is None:
        manifest_path = get_repo_root() / "manifest.json"
    
    if not manifest_path.exists():
        logging.error(f"Manifest file not found at {manifest_path}")
        return None
    
    try:
        with open(manifest_path, 'r') as f:
            manifest = json.load(f)
        logging.info(f"Loaded manifest with {len(manifest.get('components', []))} component(s)")
        return manifest
    except json.JSONDecodeError:
        logging.error(f"Manifest file {manifest_path} is not valid JSON")
        return None
    except Exception as e:
        logging.error(f"Error loading manifest: {str(e)}")
        return None


def update_manifest(manifest, component_id, deployment_info):
    """
    Update component deployment information in the manifest.
    
    Args:
        manifest: The manifest dictionary
        component_id: Component ID to update
        deployment_info: Dictionary with deployment information
    
    Returns:
        Updated manifest dictionary.
    """
    for component in manifest.get("components", []):
        if component.get("id") == component_id:
            component.update({
                "deployment_status": "deployed",
                "last_deployed": datetime.utcnow().isoformat(),
                "deployment_info": deployment_info
            })
            logging.info(f"Updated deployment status for component {component_id}")
            return True
    
    logging.warning(f"Component {component_id} not found in manifest, not updating")
    return False


def save_manifest(manifest, manifest_path=None):
    """
    Save the manifest to disk.
    
    Args:
        manifest: The manifest dictionary
        manifest_path: Path to save the manifest to (optional)
    
    Returns:
        True if successful, False otherwise.
    """
    # Default manifest path
    if manifest_path is None:
        manifest_path = get_repo_root() / "manifest.json"
    
    try:
        with open(manifest_path, 'w') as f:
            json.dump(manifest, f, indent=2)
        
        logging.info(f"Manifest saved with {len(manifest.get('components', []))} component(s)")
        return True
    except Exception as e:
        logging.error(f"Error saving manifest: {str(e)}")
        return False


def find_deployment_script(component_path):
    """
    Find the deployment script for a component.
    
    Args:
        component_path: Path to the component directory
    
    Returns:
        Path to deployment script, if found.
    """
    component_path = Path(component_path)
    
    # Check common deployment script locations
    script_locations = [
        component_path / "deployment" / "deploy.py",
        component_path / "deploy.py",
        component_path / "deployment" / "deploy_component.py"
    ]
    
    for script_path in script_locations:
        if script_path.exists() and script_path.is_file():
            return script_path
    
    return None


def deploy_component(component, subscription_id, resource_group, dry_run=False, verbose=False):
    """
    Deploy a single component.
    
    Args:
        component: Component dictionary
        subscription_id: Azure subscription ID
        resource_group: Azure resource group
        dry_run: If True, only simulate deployment
        verbose: If True, use verbose output
    
    Returns:
        Deployment result dictionary.
    """
    component_id = component.get("id", "unknown")
    service_name = component.get("service", "unknown")
    component_name = component.get("name", "unknown")
    
    logging.info(f"Deploying component: {service_name}/{component_name}")
    
    # Get component path
    repo_root = get_repo_root()
    component_path = repo_root / component.get("path", f"components/{service_name}/{component_name}")
    
    if not component_path.exists():
        logging.error(f"Component directory not found: {component_path}")
        return {
            "component_id": component_id,
            "status": "error",
            "error": f"Component directory not found: {component_path}",
            "timestamp": datetime.utcnow().isoformat()
        }
    
    # Find deployment script
    deploy_script = find_deployment_script(component_path)
    
    if not deploy_script:
        logging.error(f"Deployment script not found for component: {component_id}")
        return {
            "component_id": component_id,
            "status": "error",
            "error": "Deployment script not found",
            "timestamp": datetime.utcnow().isoformat()
        }
    
    # Identify deployment target(s)
    deployment_targets = component.get("deployment_targets", [])
    if not deployment_targets and "deployment_targets" in component:
        # Extract from component info if available
        deployment_targets = component["deployment_targets"]
    
    # Default to "all" if not specified
    target = "all" if not deployment_targets else None
    
    # Execute deployment
    try:
        # Change to component directory
        os.chdir(component_path)
        
        # Build command
        cmd = [sys.executable, str(deploy_script)]
        cmd.extend(["--subscription", subscription_id])
        cmd.extend(["--resource-group", resource_group])
        
        # Add target if specified
        if target:
            cmd.extend(["--target", target])
        
        # Add dry-run flag if specified
        if dry_run:
            cmd.append("--dry-run")
        
        # Add workspace name if target is aml
        if target == "aml" or "azure_ml" in deployment_targets:
            cmd.extend(["--workspace", f"{component_name}-workspace"])
        
        # Add function app name if target is functions
        if target == "functions" or "azure_functions" in deployment_targets:
            cmd.extend(["--function-app", f"{component_name}-function-app"])
        
        logging.debug(f"Executing command: {' '.join(cmd)}")
        
        # Execute deployment command
        start_time = time.time()
        result = subprocess.run(cmd, capture_output=True, text=True)
        duration = time.time() - start_time
        
        if result.returncode == 0:
            logging.info(f"Deployment successful for component: {component_id}")
            deployment_result = {
                "component_id": component_id,
                "status": "success",
                "duration_seconds": round(duration, 2),
                "timestamp": datetime.utcnow().isoformat(),
                "targets": deployment_targets or [target],
                "subscription_id": subscription_id,
                "resource_group": resource_group
            }
            
            # Try to extract resource IDs from output for tracking
            resource_ids = extract_resource_ids(result.stdout)
            if resource_ids:
                deployment_result["resource_ids"] = resource_ids
            
            return deployment_result
        else:
            logging.error(f"Deployment failed for component: {component_id}")
            logging.error(result.stderr)
            
            return {
                "component_id": component_id,
                "status": "failed",
                "error": result.stderr,
                "duration_seconds": round(duration, 2),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    except Exception as e:
        logging.error(f"Error deploying component {component_id}: {str(e)}")
        return {
            "component_id": component_id,
            "status": "error",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


def extract_resource_ids(output):
    """
    Extract Azure resource IDs from deployment output.
    
    Args:
        output: Deployment script output
    
    Returns:
        List of detected resource IDs.
    """
    # Pattern for Azure resource IDs
    id_pattern = r'/subscriptions/[^/]+/resourceGroups/[^/]+/providers/[^/]+/[^/]+/[^/\s]+'
    resource_ids = re.findall(id_pattern, output)
    return list(set(resource_ids))  # Remove duplicates


def deploy_components(components, subscription_id, resource_group, dry_run=False, 
                      parallel=False, max_workers=4, verbose=False):
    """
    Deploy multiple components sequentially or in parallel.
    
    Args:
        components: List of component dictionaries
        subscription_id: Azure subscription ID
        resource_group: Azure resource group
        dry_run: If True, only simulate deployment
        parallel: If True, deploy components in parallel
        max_workers: Maximum number of parallel deployment workers
        verbose: If True, use verbose output
    
    Returns:
        Dictionary with deployment results.
    """
    if not components:
        logging.warning("No components to deploy")
        return {
            "status": "warning",
            "message": "No components to deploy",
            "timestamp": datetime.utcnow().isoformat()
        }
    
    results = {
        "timestamp": datetime.utcnow().isoformat(),
        "subscription_id": subscription_id,
        "resource_group": resource_group,
        "dry_run": dry_run,
        "components_total": len(components),
        "components_succeeded": 0,
        "components_failed": 0,
        "components_errored": 0,
        "component_results": []
    }
    
    start_time = time.time()
    
    if parallel:
        logging.info(f"Deploying {len(components)} component(s) in parallel (max workers: {max_workers})")
        
        # Function to deploy component with fixed parameters
        def deploy_with_params(component):
            return deploy_component(component, subscription_id, resource_group, dry_run, verbose)
        
        # Deploy components in parallel
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            component_results = list(executor.map(deploy_with_params, components))
        
        # Process results
        for result in component_results:
            results["component_results"].append(result)
            
            if result["status"] == "success":
                results["components_succeeded"] += 1
            elif result["status"] == "failed":
                results["components_failed"] += 1
            else:
                results["components_errored"] += 1
    
    else:
        logging.info(f"Deploying {len(components)} component(s) sequentially")
        
        # Deploy components sequentially
        for component in components:
            result = deploy_component(component, subscription_id, resource_group, dry_run, verbose)
            results["component_results"].append(result)
            
            if result["status"] == "success":
                results["components_succeeded"] += 1
            elif result["status"] == "failed":
                results["components_failed"] += 1
            else:
                results["components_errored"] += 1
    
    results["duration_seconds"] = round(time.time() - start_time, 2)
    logging.info(f"Deployment completed in {results['duration_seconds']} seconds")
    logging.info(f"Success: {results['components_succeeded']}, Failed: {results['components_failed']}, Error: {results['components_errored']}")
    
    return results


def verify_azure_login():
    """
    Verify that the user is logged in to Azure CLI.
    
    Returns:
        True if logged in, False otherwise.
    """
    try:
        # Check if Azure CLI is installed
        subprocess.run(["az", "--version"], check=True, capture_output=True)
        
        # Check if logged in
        result = subprocess.run(["az", "account", "show"], capture_output=True, text=True, check=False)
        
        if result.returncode != 0:
            logging.error("Not logged in to Azure CLI. Please run 'az login' first.")
            return False
        
        # Get account info
        account_info = json.loads(result.stdout)
        logging.info(f"Logged in to Azure as {account_info['user']['name']} (Subscription: {account_info['name']})")
        return True
    
    except FileNotFoundError:
        logging.error("Azure CLI not found. Please install Azure CLI.")
        return False
    except Exception as e:
        logging.error(f"Error verifying Azure login: {str(e)}")
        return False


def select_subscription(subscription_id):
    """
    Select the specified Azure subscription.
    
    Args:
        subscription_id: The subscription ID to use
    
    Returns:
        True if successful, False otherwise.
    """
    try:
        subprocess.run(
            ["az", "account", "set", "--subscription", subscription_id],
            check=True, capture_output=True
        )
        
        # Verify selection
        result = subprocess.run(
            ["az", "account", "show", "--query", "id", "-o", "tsv"],
            capture_output=True, text=True, check=True
        )
        
        selected_id = result.stdout.strip()
        if selected_id != subscription_id:
            logging.error(f"Failed to set subscription to {subscription_id}, still using {selected_id}")
            return False
        
        logging.info(f"Using Azure subscription: {subscription_id}")
        return True
    
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to set subscription: {str(e)}")
        return False
    
    except Exception as e:
        logging.error(f"Error setting subscription: {str(e)}")
        return False


def verify_resource_group(subscription_id, resource_group, location=None, create_if_missing=False):
    """
    Verify that the specified resource group exists, optionally creating it if missing.
    
    Args:
        subscription_id: Azure subscription ID
        resource_group: Resource group name to verify
        location: Azure location (required if creating)
        create_if_missing: Whether to create the resource group if it doesn't exist
    
    Returns:
        True if the resource group exists or was created, False otherwise.
    """
    try:
        # Check if resource group exists
        result = subprocess.run(
            ["az", "group", "exists", "--name", resource_group],
            capture_output=True, text=True, check=True
        )
        
        exists = result.stdout.strip().lower() == "true"
        
        if exists:
            logging.info(f"Resource group {resource_group} exists")
            return True
        elif create_if_missing and location:
            logging.warning(f"Resource group {resource_group} does not exist, creating...")
            
            # Create resource group
            create_result = subprocess.run(
                ["az", "group", "create", "--name", resource_group, "--location", location],
                capture_output=True, text=True, check=True
            )
            
            logging.info(f"Resource group {resource_group} created in {location}")
            return True
        else:
            logging.error(f"Resource group {resource_group} not found")
            return False
    
    except subprocess.CalledProcessError as e:
        logging.error(f"Error verifying resource group: {str(e)}")
        return False
    
    except Exception as e:
        logging.error(f"Error verifying resource group: {str(e)}")
        return False


def main():
    """Main entry point for the deployment orchestration script."""
    parser = argparse.ArgumentParser(
        description="Deploy components in the Azure Components Foundry"
    )
    
    # Commands
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Deploy all command
    all_parser = subparsers.add_parser(
        "all", help="Deploy all components in the manifest"
    )
    all_parser.add_argument(
        "--subscription", required=True, help="Azure subscription ID"
    )
    all_parser.add_argument(
        "--resource-group", required=True, help="Azure resource group name"
    )
    all_parser.add_argument(
        "--location", help="Azure location (for resource group creation)"
    )
    all_parser.add_argument(
        "--create-group", action="store_true", help="Create resource group if it doesn't exist"
    )
    all_parser.add_argument(
        "--manifest", help="Path to manifest file (default: manifest.json at repo root)"
    )
    all_parser.add_argument(
        "--dry-run", action="store_true", help="Perform a dry run without deploying"
    )
    all_parser.add_argument(
        "--parallel", action="store_true", help="Deploy components in parallel"
    )
    all_parser.add_argument(
        "--max-workers", type=int, default=4, help="Maximum parallel workers (default: 4)"
    )
    all_parser.add_argument(
        "--update-manifest", action="store_true", help="Update manifest with deployment results"
    )
    
    # Deploy component command
    component_parser = subparsers.add_parser(
        "component", help="Deploy a specific component"
    )
    component_parser.add_argument(
        "--component-id", required=True, help="Component ID to deploy"
    )
    component_parser.add_argument(
        "--subscription", required=True, help="Azure subscription ID"
    )
    component_parser.add_argument(
        "--resource-group", required=True, help="Azure resource group name"
    )
    component_parser.add_argument(
        "--location", help="Azure location (for resource group creation)"
    )
    component_parser.add_argument(
        "--create-group", action="store_true", help="Create resource group if it doesn't exist"
    )
    component_parser.add_argument(
        "--manifest", help="Path to manifest file (default: manifest.json at repo root)"
    )
    component_parser.add_argument(
        "--dry-run", action="store_true", help="Perform a dry run without deploying"
    )
    component_parser.add_argument(
        "--update-manifest", action="store_true", help="Update manifest with deployment results"
    )
    
    # Deploy service command
    service_parser = subparsers.add_parser(
        "service", help="Deploy all components for a specific service"
    )
    service_parser.add_argument(
        "--service", required=True, help="Service name to deploy"
    )
    service_parser.add_argument(
        "--subscription", required=True, help="Azure subscription ID"
    )
    service_parser.add_argument(
        "--resource-group", required=True, help="Azure resource group name"
    )
    service_parser.add_argument(
        "--location", help="Azure location (for resource group creation)"
    )
    service_parser.add_argument(
        "--create-group", action="store_true", help="Create resource group if it doesn't exist"
    )
    service_parser.add_argument(
        "--manifest", help="Path to manifest file (default: manifest.json at repo root)"
    )
    service_parser.add_argument(
        "--dry-run", action="store_true", help="Perform a dry run without deploying"
    )
    service_parser.add_argument(
        "--parallel", action="store_true", help="Deploy components in parallel"
    )
    service_parser.add_argument(
        "--max-workers", type=int, default=4, help="Maximum parallel workers (default: 4)"
    )
    service_parser.add_argument(
        "--update-manifest", action="store_true", help="Update manifest with deployment results"
    )
    
    # Global arguments
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose logging and output"
    )
    
    args = parser.parse_args()
    
    # Configure logging
    setup_logging(args.verbose)
    
    # Default command if none specified
    if not args.command:
        parser.print_help()
        return
    
    # Verify Azure login for all commands
    if not verify_azure_login():
        sys.exit(1)
    
    # Select subscription for all commands
    if not select_subscription(args.subscription):
        sys.exit(1)
    
    # Verify resource group for all commands
    if not verify_resource_group(
        args.subscription, args.resource_group, 
        args.location, args.create_group
    ):
        sys.exit(1)
    
    # Load manifest for all commands
    manifest = load_manifest(args.manifest)
    if manifest is None:
        sys.exit(1)
    
    # Execute requested command
    try:
        if args.command == "all":
            # Deploy all components
            components = manifest.get("components", [])
            
            if not components:
                logging.warning("No components found in manifest")
                sys.exit(0)
            
            logging.info(f"Deploying all {len(components)} component(s)")
            
            # Run deployment
            results = deploy_components(
                components=components,
                subscription_id=args.subscription,
                resource_group=args.resource_group,
                dry_run=args.dry_run,
                parallel=args.parallel,
                max_workers=args.max_workers,
                verbose=args.verbose
            )
            
            # Update manifest if requested
            if args.update_manifest and not args.dry_run:
                for result in results.get("component_results", []):
                    if result["status"] == "success":
                        update_manifest(manifest, result["component_id"], result)
                
                save_manifest(manifest, args.manifest)
            
            # Print summary
            print("\n===== Deployment Summary =====")
            print(f"Components Total: {results['components_total']}")
            print(f"Components Succeeded: {results['components_succeeded']}")
            print(f"Components Failed: {results['components_failed']}")
            print(f"Components Errored: {results['components_errored']}")
            print(f"Duration: {results['duration_seconds']:.2f} seconds")
            print("=============================\n")
            
            # Exit with error if any component deployment failed
            if results["components_failed"] > 0 or results["components_errored"] > 0:
                sys.exit(1)
        
        elif args.command == "component":
            # Deploy a specific component
            component = None
            for c in manifest.get("components", []):
                if c.get("id") == args.component_id:
                    component = c
                    break
            
            if not component:
                logging.error(f"Component {args.component_id} not found in manifest")
                sys.exit(1)
            
            logging.info(f"Deploying component {args.component_id}")
            
            # Run deployment
            result = deploy_component(
                component=component,
                subscription_id=args.subscription,
                resource_group=args.resource_group,
                dry_run=args.dry_run,
                verbose=args.verbose
            )
            
            # Update manifest if requested
            if args.update_manifest and not args.dry_run and result["status"] == "success":
                update_manifest(manifest, args.component_id, result)
                save_manifest(manifest, args.manifest)
            
            # Print result
            print("\n===== Deployment Result =====")
            print(f"Component ID: {args.component_id}")
            print(f"Status: {result['status'].upper()}")
            if result["status"] != "success":
                print(f"Error: {result.get('error', 'Unknown error')}")
            print(f"Duration: {result.get('duration_seconds', 0):.2f} seconds")
            print("============================\n")
            
            # Exit with error if deployment failed
            if result["status"] != "success":
                sys.exit(1)
        
        elif args.command == "service":
            # Deploy all components for a specific service
            components = []
            for c in manifest.get("components", []):
                if c.get("service") == args.service:
                    components.append(c)
            
            if not components:
                logging.warning(f"No components found for service {args.service}")
                sys.exit(0)
            
            logging.info(f"Deploying {len(components)} component(s) for service {args.service}")
            
            # Run deployment
            results = deploy_components(
                components=components,
                subscription_id=args.subscription,
                resource_group=args.resource_group,
                dry_run=args.dry_run,
                parallel=args.parallel,
                max_workers=args.max_workers,
                verbose=args.verbose
            )
            
            # Update manifest if requested
            if args.update_manifest and not args.dry_run:
                for result in results.get("component_results", []):
                    if result["status"] == "success":
                        update_manifest(manifest, result["component_id"], result)
                
                save_manifest(manifest, args.manifest)
            
            # Print summary
            print("\n===== Deployment Summary =====")
            print(f"Service: {args.service}")
            print(f"Components Total: {results['components_total']}")
            print(f"Components Succeeded: {results['components_succeeded']}")
            print(f"Components Failed: {results['components_failed']}")
            print(f"Components Errored: {results['components_errored']}")
            print(f"Duration: {results['duration_seconds']:.2f} seconds")
            print("=============================\n")
            
            # Exit with error if any component deployment failed
            if results["components_failed"] > 0 or results["components_errored"] > 0:
                sys.exit(1)
        
        else:
            parser.print_help()
    
    except KeyboardInterrupt:
        logging.warning("Deployment interrupted by user")
        sys.exit(130)
    
    except Exception as e:
        logging.error(f"Error during deployment: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()