#!/usr/bin/env python
"""
Azure setup script for the Azure Components Foundry.
This script helps set up and configure Azure resources required by the foundry.
"""

import argparse
import logging
import os
import subprocess
import sys
import json
from pathlib import Path
import re


def setup_logging(verbose=False):
    """Configure logging based on verbosity level."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )


def validate_name(name, resource_type):
    """Validate resource name according to Azure naming conventions."""
    patterns = {
        "resource_group": r"^[a-zA-Z0-9]([a-zA-Z0-9_-]*[a-zA-Z0-9])?$",
        "key_vault": r"^[a-zA-Z]([a-zA-Z0-9-]{1,21}[a-zA-Z0-9])?$",
        "storage": r"^[a-z0-9]{3,24}$",
        "service_principal": r"^[a-zA-Z0-9]([a-zA-Z0-9_-]*[a-zA-Z0-9])?$"
    }
    
    if resource_type not in patterns:
        logging.error(f"Unknown resource type: {resource_type}")
        return False
    
    pattern = patterns[resource_type]
    if re.match(pattern, name):
        return True
    else:
        logging.error(f"Invalid {resource_type} name '{name}'. Must match pattern: {pattern}")
        return False


def check_az_cli():
    """Check if Azure CLI is installed and logged in."""
    try:
        # Check if Azure CLI is installed
        subprocess.run(["az", "--version"], check=True, capture_output=True)
        
        # Check if already logged in
        result = subprocess.run(
            ["az", "account", "show"],
            check=False, capture_output=True, text=True
        )
        
        if result.returncode != 0:
            logging.warning("Not logged into Azure CLI. Please log in.")
            subprocess.run(["az", "login"], check=True)
        else:
            account = json.loads(result.stdout)
            logging.info(f"Using Azure account: {account['name']} (Subscription: {account['id']})")
        
        return True
    
    except subprocess.CalledProcessError:
        logging.error(
            "Azure CLI not installed or not working properly. "
            "Please install from https://docs.microsoft.com/cli/azure/install-azure-cli"
        )
        return False
    
    except Exception as e:
        logging.error(f"Error checking Azure CLI: {str(e)}")
        return False


def create_resource_group(name, location, tags=None, dry_run=False):
    """Create an Azure resource group."""
    if not validate_name(name, "resource_group"):
        return False
    
    logging.info(f"Creating resource group {name} in {location}")
    
    if dry_run:
        logging.info("[DRY RUN] Would create resource group")
        return True
    
    try:
        cmd = ["az", "group", "create", "--name", name, "--location", location]
        
        # Add tags if provided
        if tags:
            tag_list = [f"{k}={v}" for k, v in tags.items()]
            cmd.extend(["--tags"] + tag_list)
        
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        data = json.loads(result.stdout)
        logging.info(f"Resource group created: {data['name']} (Location: {data['location']})")
        return True
    
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to create resource group: {e}")
        if e.stderr:
            logging.error(e.stderr)
        return False
    
    except Exception as e:
        logging.error(f"Error creating resource group: {str(e)}")
        return False


def create_key_vault(name, resource_group, location, tags=None, dry_run=False):
    """Create an Azure Key Vault."""
    if not validate_name(name, "key_vault"):
        return False
    
    logging.info(f"Creating key vault {name} in {resource_group}")
    
    if dry_run:
        logging.info("[DRY RUN] Would create key vault")
        return True
    
    try:
        cmd = [
            "az", "keyvault", "create",
            "--name", name,
            "--resource-group", resource_group,
            "--location", location
        ]
        
        # Add tags if provided
        if tags:
            tag_list = [f"{k}={v}" for k, v in tags.items()]
            cmd.extend(["--tags"] + tag_list)
        
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        data = json.loads(result.stdout)
        logging.info(f"Key vault created: {data['name']} (Resource Group: {resource_group})")
        return True
    
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to create key vault: {e}")
        if e.stderr:
            logging.error(e.stderr)
        return False
    
    except Exception as e:
        logging.error(f"Error creating key vault: {str(e)}")
        return False


def create_service_principal(name, role="Contributor", scope=None, dry_run=False):
    """Create a service principal for GitHub Actions or other integrations."""
    if not validate_name(name, "service_principal"):
        return False
    
    logging.info(f"Creating service principal {name} with role {role}")
    
    if dry_run:
        logging.info("[DRY RUN] Would create service principal")
        return {}
    
    try:
        cmd = ["az", "ad", "sp", "create-for-rbac", "--name", name, "--role", role]
        
        # Add scope if provided
        if scope:
            cmd.extend(["--scopes", scope])
        
        # Add SDK auth format for GitHub Actions
        cmd.append("--sdk-auth")
        
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        credentials = json.loads(result.stdout)
        
        logging.info(f"Service principal created: {name}")
        logging.warning("IMPORTANT: Store these credentials securely!")
        return credentials
    
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to create service principal: {e}")
        if e.stderr:
            logging.error(e.stderr)
        return {}
    
    except Exception as e:
        logging.error(f"Error creating service principal: {str(e)}")
        return {}


def grant_keyvault_access(vault_name, service_principal_id, permissions=None, dry_run=False):
    """Grant a service principal access to a Key Vault."""
    if not permissions:
        permissions = ["get", "list", "set", "delete"]
    
    logging.info(f"Granting {service_principal_id} access to Key Vault {vault_name}")
    
    if dry_run:
        logging.info("[DRY RUN] Would grant Key Vault access")
        return True
    
    try:
        cmd = [
            "az", "keyvault", "set-policy",
            "--name", vault_name,
            "--spn", service_principal_id,
            "--secret-permissions"
        ] + permissions
        
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        logging.info(f"Key Vault access granted to {service_principal_id}")
        return True
    
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to grant Key Vault access: {e}")
        if e.stderr:
            logging.error(e.stderr)
        return False
    
    except Exception as e:
        logging.error(f"Error granting Key Vault access: {str(e)}")
        return False


def interactive_setup(dry_run=False):
    """Interactive guided setup for Azure resources."""
    logging.info("Starting interactive Azure setup...")
    
    # Check if logged in to Azure CLI
    if not check_az_cli():
        logging.error("Azure CLI check failed. Please install and log in.")
        return False
    
    print("\n=== Resource Group Setup ===")
    rg_name = input("Resource Group Name: ").strip()
    location = input("Location (e.g., eastus): ").strip() or "eastus"
    
    if not rg_name:
        logging.error("Resource Group name cannot be empty")
        return False
    
    # Tags are optional
    tags = {}
    add_tags = input("Add tags? (y/n): ").lower() == 'y'
    if add_tags:
        print("Enter tags (format: key=value), empty line to finish:")
        while True:
            tag = input().strip()
            if not tag:
                break
            if '=' in tag:
                key, value = tag.split('=', 1)
                tags[key] = value
    
    # Create resource group
    if not create_resource_group(rg_name, location, tags, dry_run):
        return False
    
    # Key Vault setup is optional
    create_kv = input("\nCreate a Key Vault? (y/n): ").lower() == 'y'
    if create_kv:
        print("\n=== Key Vault Setup ===")
        kv_name = input("Key Vault Name: ").strip()
        if not kv_name:
            logging.error("Key Vault name cannot be empty")
        else:
            create_key_vault(kv_name, rg_name, location, tags, dry_run)
    
    # Service Principal setup is optional
    create_sp = input("\nCreate a Service Principal for GitHub Actions? (y/n): ").lower() == 'y'
    if create_sp:
        print("\n=== Service Principal Setup ===")
        sp_name = input("Service Principal Name: ").strip()
        role = input("Role (default: Contributor): ").strip() or "Contributor"
        
        # Construct scope
        subscription_id = input("Subscription ID (empty for current): ").strip()
        if not subscription_id:
            result = subprocess.run(["az", "account", "show", "--query", "id", "-o", "tsv"], 
                                   capture_output=True, text=True, check=True)
            subscription_id = result.stdout.strip()
        
        scope = f"/subscriptions/{subscription_id}"
        if rg_name:
            use_rg_scope = input("Limit scope to just created Resource Group? (y/n): ").lower() == 'y'
            if use_rg_scope:
                scope = f"{scope}/resourceGroups/{rg_name}"
        
        # Create the service principal
        if sp_name:
            credentials = create_service_principal(sp_name, role, scope, dry_run)
            
            # Store credentials to file if requested
            if credentials and input("Save credentials to file? (y/n): ").lower() == 'y':
                filename = input("Filename (default: sp-credentials.json): ").strip() or "sp-credentials.json"
                try:
                    with open(filename, 'w') as f:
                        json.dump(credentials, f, indent=2)
                    logging.info(f"Credentials saved to {filename}")
                    logging.warning(f"IMPORTANT: Keep {filename} secure and add it to .gitignore!")
                except Exception as e:
                    logging.error(f"Error saving credentials: {str(e)}")
            
            # Grant Key Vault access if a vault was created
            if create_kv and kv_name and credentials.get("clientId"):
                if input(f"Grant the service principal access to Key Vault {kv_name}? (y/n): ").lower() == 'y':
                    permissions = input("Secret permissions (comma-separated, default: get,list,set,delete): ").strip()
                    permissions = [p.strip() for p in permissions.split(',')] if permissions else ["get", "list", "set", "delete"]
                    grant_keyvault_access(kv_name, credentials.get("clientId"), permissions, dry_run)
    
    logging.info("Azure setup completed successfully")
    return True


def setup_all_resources(resource_group, location, key_vault=None, service_principal=None, tags=None, dry_run=False):
    """Set up all resources in a single command."""
    if not check_az_cli():
        logging.error("Azure CLI check failed. Please install and log in.")
        return False
    
    # Create resource group
    if not create_resource_group(resource_group, location, tags, dry_run):
        return False
    
    # Create key vault if name provided
    if key_vault:
        create_key_vault(key_vault, resource_group, location, tags, dry_run)
    
    # Create service principal if name provided
    credentials = {}
    if service_principal:
        # Get current subscription for scope
        result = subprocess.run(["az", "account", "show", "--query", "id", "-o", "tsv"], 
                               capture_output=True, text=True, check=True)
        subscription_id = result.stdout.strip()
        scope = f"/subscriptions/{subscription_id}/resourceGroups/{resource_group}"
        
        credentials = create_service_principal(service_principal, "Contributor", scope, dry_run)
        
        # Grant key vault access if both are specified
        if key_vault and credentials.get("clientId"):
            grant_keyvault_access(key_vault, credentials["clientId"], ["get", "list", "set", "delete"], dry_run)
    
    logging.info("Azure resources setup completed successfully")
    return credentials


def main():
    """Main entry point for Azure setup script."""
    parser = argparse.ArgumentParser(
        description="Set up Azure resources for the Azure Components Foundry"
    )
    
    # Command subparsers
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Interactive setup
    interactive_parser = subparsers.add_parser(
        "interactive", help="Interactive guided setup"
    )
    interactive_parser.add_argument(
        "--dry-run", action="store_true", help="Perform a dry run without creating resources"
    )
    
    # Resource group command
    rg_parser = subparsers.add_parser(
        "resource-group", help="Create an Azure resource group"
    )
    rg_parser.add_argument("--name", required=True, help="Resource group name")
    rg_parser.add_argument("--location", required=True, help="Azure region (e.g., eastus)")
    rg_parser.add_argument("--tags", help="Tags in key=value,key=value format")
    rg_parser.add_argument(
        "--dry-run", action="store_true", help="Perform a dry run without creating resources"
    )
    
    # Key vault command
    kv_parser = subparsers.add_parser(
        "key-vault", help="Create an Azure Key Vault"
    )
    kv_parser.add_argument("--name", required=True, help="Key Vault name")
    kv_parser.add_argument("--resource-group", required=True, help="Resource group name")
    kv_parser.add_argument("--location", required=True, help="Azure region (e.g., eastus)")
    kv_parser.add_argument("--tags", help="Tags in key=value,key=value format")
    kv_parser.add_argument(
        "--dry-run", action="store_true", help="Perform a dry run without creating resources"
    )
    
    # Service principal command
    sp_parser = subparsers.add_parser(
        "service-principal", help="Create a service principal for GitHub Actions"
    )
    sp_parser.add_argument("--name", required=True, help="Service principal name")
    sp_parser.add_argument("--role", default="Contributor", help="Role to assign (default: Contributor)")
    sp_parser.add_argument("--scope", help="Scope of role assignment (e.g., subscription or resource group)")
    sp_parser.add_argument("--output-file", help="Save credentials to this file")
    sp_parser.add_argument(
        "--dry-run", action="store_true", help="Perform a dry run without creating resources"
    )
    
    # Setup all resources command
    all_parser = subparsers.add_parser(
        "all", help="Set up all required resources"
    )
    all_parser.add_argument("--resource-group", required=True, help="Resource group name")
    all_parser.add_argument("--location", required=True, help="Azure region (e.g., eastus)")
    all_parser.add_argument("--key-vault", help="Key Vault name (optional)")
    all_parser.add_argument("--service-principal", help="Service principal name (optional)")
    all_parser.add_argument("--tags", help="Tags in key=value,key=value format")
    all_parser.add_argument("--output-file", help="Save service principal credentials to this file")
    all_parser.add_argument(
        "--dry-run", action="store_true", help="Perform a dry run without creating resources"
    )
    
    # Global arguments
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")
    
    args = parser.parse_args()
    
    # Configure logging
    setup_logging(args.verbose)
    
    # Parse tags if provided
    tags = {}
    if hasattr(args, 'tags') and args.tags:
        for tag_pair in args.tags.split(','):
            if '=' in tag_pair:
                key, value = tag_pair.split('=', 1)
                tags[key] = value
    
    # Execute requested command
    if args.command == "interactive":
        interactive_setup(args.dry_run)
    
    elif args.command == "resource-group":
        create_resource_group(args.name, args.location, tags, args.dry_run)
    
    elif args.command == "key-vault":
        create_key_vault(args.name, args.resource_group, args.location, tags, args.dry_run)
    
    elif args.command == "service-principal":
        credentials = create_service_principal(args.name, args.role, args.scope, args.dry_run)
        
        # Save credentials if output file specified
        if credentials and args.output_file:
            try:
                with open(args.output_file, 'w') as f:
                    json.dump(credentials, f, indent=2)
                logging.info(f"Service principal credentials saved to {args.output_file}")
            except Exception as e:
                logging.error(f"Failed to save credentials: {str(e)}")
    
    elif args.command == "all":
        credentials = setup_all_resources(
            args.resource_group, 
            args.location,
            args.key_vault,
            args.service_principal,
            tags,
            args.dry_run
        )
        
        # Save credentials if output file specified and service principal was created
        if credentials and args.output_file:
            try:
                with open(args.output_file, 'w') as f:
                    json.dump(credentials, f, indent=2)
                logging.info(f"Service principal credentials saved to {args.output_file}")
            except Exception as e:
                logging.error(f"Failed to save credentials: {str(e)}")
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()