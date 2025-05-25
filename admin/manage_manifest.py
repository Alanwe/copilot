#!/usr/bin/env python
"""
Manifest management script for the Azure Components Foundry.
This script helps manage the component manifest.
"""

import argparse
import json
import logging
import os
import sys
import re
from pathlib import Path
from datetime import datetime


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
        import subprocess
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, check=True
        )
        return Path(result.stdout.strip())
    except Exception:
        # Fallback: assume script is in admin directory
        return Path(__file__).parent.parent


def get_manifest_path(manifest_path=None):
    """Get the path to the manifest file."""
    if manifest_path:
        return Path(manifest_path)
    else:
        return get_repo_root() / "manifest.json"


def load_manifest(manifest_path=None):
    """
    Load the component manifest.
    
    Args:
        manifest_path: Path to manifest file (optional)
    
    Returns:
        The manifest as a dictionary.
    """
    manifest_path = get_manifest_path(manifest_path)
    
    if not manifest_path.exists():
        logging.warning(f"Manifest not found at {manifest_path}, creating empty manifest")
        return {
            "version": "1.0",
            "last_updated": datetime.utcnow().isoformat(),
            "components": []
        }
    
    try:
        with open(manifest_path, 'r') as f:
            manifest = json.load(f)
        logging.info(f"Loaded manifest from {manifest_path}")
        return manifest
    except json.JSONDecodeError as e:
        logging.error(f"Failed to parse manifest: {str(e)}")
        raise ValueError(f"Invalid JSON in manifest file: {str(e)}")
    except Exception as e:
        logging.error(f"Failed to load manifest: {str(e)}")
        raise


def save_manifest(manifest, manifest_path=None):
    """
    Save the manifest to disk.
    
    Args:
        manifest: The manifest dictionary
        manifest_path: Path to save the manifest to (optional)
    
    Returns:
        True if successful, False otherwise.
    """
    manifest_path = get_manifest_path(manifest_path)
    
    # Update timestamp
    manifest["last_updated"] = datetime.utcnow().isoformat()
    
    try:
        with open(manifest_path, 'w') as f:
            json.dump(manifest, f, indent=2, sort_keys=True)
        logging.info(f"Saved manifest to {manifest_path}")
        return True
    except Exception as e:
        logging.error(f"Failed to save manifest: {str(e)}")
        return False


def validate_manifest(manifest):
    """
    Validate the manifest structure and content.
    
    Args:
        manifest: The manifest dictionary
    
    Returns:
        Tuple of (is_valid, errors)
    """
    errors = []
    
    # Check basic structure
    if not isinstance(manifest, dict):
        errors.append("Manifest must be a dictionary")
        return False, errors
    
    # Check required top-level fields
    required_fields = ["version", "components"]
    for field in required_fields:
        if field not in manifest:
            errors.append(f"Missing required field: {field}")
    
    # Validate version format
    if "version" in manifest:
        version = manifest["version"]
        if not isinstance(version, str):
            errors.append("Field 'version' must be a string")
        elif not re.match(r"^\d+\.\d+$", version):
            errors.append(f"Invalid version format: {version} (expected format: X.Y)")
    
    # Validate components
    if "components" in manifest:
        if not isinstance(manifest["components"], list):
            errors.append("Field 'components' must be a list")
        else:
            # Check each component
            for i, component in enumerate(manifest["components"]):
                if not isinstance(component, dict):
                    errors.append(f"Component at index {i} must be a dictionary")
                    continue
                
                # Required fields in each component
                component_required = ["id", "name", "service", "path"]
                for field in component_required:
                    if field not in component:
                        errors.append(f"Component at index {i} missing required field: {field}")
                
                # Check component ID format
                if "id" in component:
                    id_value = component["id"]
                    if not isinstance(id_value, str):
                        errors.append(f"Component ID must be a string: {id_value}")
            
            # Check for duplicate IDs
            component_ids = [c.get("id") for c in manifest["components"] if "id" in c]
            duplicate_ids = set([x for x in component_ids if component_ids.count(x) > 1])
            if duplicate_ids:
                errors.append(f"Duplicate component IDs found: {', '.join(duplicate_ids)}")
    
    return len(errors) == 0, errors


def get_component_by_id(manifest, component_id):
    """
    Get a component by its ID.
    
    Args:
        manifest: The manifest dictionary
        component_id: Component ID to find
    
    Returns:
        The component dictionary or None if not found.
    """
    for component in manifest.get("components", []):
        if component.get("id") == component_id:
            return component
    return None


def add_component(manifest, component):
    """
    Add a new component to the manifest.
    
    Args:
        manifest: The manifest dictionary
        component: The component dictionary to add
    
    Returns:
        Updated manifest dictionary.
    """
    # Check if component with this ID already exists
    existing = get_component_by_id(manifest, component.get("id"))
    
    if existing:
        logging.warning(f"Component with ID {component.get('id')} already exists, updating")
        index = manifest["components"].index(existing)
        manifest["components"][index] = component
    else:
        logging.info(f"Adding new component with ID {component.get('id')}")
        manifest["components"].append(component)
    
    # Update the component count
    manifest["component_count"] = len(manifest["components"])
    
    return manifest


def remove_component(manifest, component_id):
    """
    Remove a component from the manifest.
    
    Args:
        manifest: The manifest dictionary
        component_id: ID of the component to remove
    
    Returns:
        Updated manifest dictionary and removed component (or None).
    """
    for i, component in enumerate(manifest.get("components", [])):
        if component.get("id") == component_id:
            removed = manifest["components"].pop(i)
            logging.info(f"Removed component with ID {component_id}")
            
            # Update the component count
            manifest["component_count"] = len(manifest["components"])
            
            return manifest, removed
    
    logging.warning(f"Component with ID {component_id} not found")
    return manifest, None


def update_component(manifest, component_id, updates):
    """
    Update a component in the manifest.
    
    Args:
        manifest: The manifest dictionary
        component_id: ID of the component to update
        updates: Dictionary of fields to update
    
    Returns:
        Updated manifest dictionary and a boolean indicating success.
    """
    for i, component in enumerate(manifest.get("components", [])):
        if component.get("id") == component_id:
            # Update the component
            for key, value in updates.items():
                component[key] = value
            
            logging.info(f"Updated component with ID {component_id}")
            return manifest, True
    
    logging.warning(f"Component with ID {component_id} not found")
    return manifest, False


def search_components(manifest, criteria):
    """
    Search for components matching specified criteria.
    
    Args:
        manifest: The manifest dictionary
        criteria: Dictionary of field:value pairs to match
    
    Returns:
        List of matching components.
    """
    results = []
    
    for component in manifest.get("components", []):
        match = True
        
        for field, value in criteria.items():
            # Handle nested fields with dot notation (e.g., "tags.owner")
            if "." in field:
                parts = field.split(".")
                current = component
                for part in parts:
                    if part not in current:
                        match = False
                        break
                    current = current[part]
                
                if match and current != value:
                    match = False
            
            # Simple field match
            elif field not in component or component[field] != value:
                match = False
        
        if match:
            results.append(component)
    
    return results


def list_components(manifest, format_output=False):
    """
    List all components in the manifest.
    
    Args:
        manifest: The manifest dictionary
        format_output: Whether to format the output as a readable table
    
    Returns:
        List of components or formatted string.
    """
    components = manifest.get("components", [])
    
    if not format_output:
        return components
    
    # Format as a table
    if not components:
        return "No components found in manifest."
    
    # Determine fields to include
    headers = ["ID", "Service", "Name", "Version"]
    rows = []
    
    for component in components:
        row = [
            component.get("id", ""),
            component.get("service", ""),
            component.get("name", ""),
            component.get("version", "")
        ]
        rows.append(row)
    
    # Calculate column widths
    col_widths = [max(len(str(row[i])) for row in [headers] + rows) for i in range(len(headers))]
    
    # Format the table
    result = []
    
    # Add header
    header_row = " | ".join(f"{headers[i]:<{col_widths[i]}}" for i in range(len(headers)))
    result.append(header_row)
    result.append("-" * len(header_row))
    
    # Add data rows
    for row in rows:
        result.append(" | ".join(f"{str(row[i]):<{col_widths[i]}}" for i in range(len(headers))))
    
    return "\n".join(result)


def generate_summary(manifest):
    """
    Generate a summary of the manifest.
    
    Args:
        manifest: The manifest dictionary
    
    Returns:
        Dictionary with summary information.
    """
    components = manifest.get("components", [])
    
    # Count by service
    services = {}
    for component in components:
        service = component.get("service", "unknown")
        if service in services:
            services[service] += 1
        else:
            services[service] = 1
    
    # Count by deployment status
    deployment_status = {
        "deployed": 0,
        "not_deployed": 0,
        "unknown": 0
    }
    
    for component in components:
        status = component.get("deployment_status", "unknown")
        if status == "deployed":
            deployment_status["deployed"] += 1
        elif status == "not_deployed":
            deployment_status["not_deployed"] += 1
        else:
            deployment_status["unknown"] += 1
    
    return {
        "total_components": len(components),
        "services": services,
        "deployment_status": deployment_status,
        "last_updated": manifest.get("last_updated", "unknown")
    }


def print_summary(manifest):
    """Print a summary of the manifest."""
    summary = generate_summary(manifest)
    
    print("\n===== Manifest Summary =====")
    print(f"Total Components: {summary['total_components']}")
    print(f"Last Updated: {summary['last_updated']}")
    
    print("\nComponents by Service:")
    for service, count in summary["services"].items():
        print(f"  {service}: {count}")
    
    print("\nDeployment Status:")
    for status, count in summary["deployment_status"].items():
        print(f"  {status}: {count}")
    
    print("============================\n")


def main():
    """Main entry point for the manifest management script."""
    parser = argparse.ArgumentParser(
        description="Manage the component manifest for Azure Components Foundry"
    )
    
    # Commands
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Validate command
    validate_parser = subparsers.add_parser(
        "validate", help="Validate the manifest structure and content"
    )
    validate_parser.add_argument(
        "--manifest", help="Path to manifest file (default: manifest.json at repo root)"
    )
    
    # List command
    list_parser = subparsers.add_parser(
        "list", help="List components in the manifest"
    )
    list_parser.add_argument(
        "--manifest", help="Path to manifest file (default: manifest.json at repo root)"
    )
    list_parser.add_argument(
        "--format", action="store_true", help="Format output as a readable table"
    )
    
    # Get command
    get_parser = subparsers.add_parser(
        "get", help="Get a specific component by ID"
    )
    get_parser.add_argument(
        "component_id", help="ID of the component to retrieve"
    )
    get_parser.add_argument(
        "--manifest", help="Path to manifest file (default: manifest.json at repo root)"
    )
    
    # Add command
    add_parser = subparsers.add_parser(
        "add", help="Add a component to the manifest"
    )
    add_parser.add_argument(
        "--manifest", help="Path to manifest file (default: manifest.json at repo root)"
    )
    add_parser.add_argument(
        "--id", required=True, help="Component ID"
    )
    add_parser.add_argument(
        "--service", required=True, help="Service name"
    )
    add_parser.add_argument(
        "--name", required=True, help="Component name"
    )
    add_parser.add_argument(
        "--path", required=True, help="Path to component directory"
    )
    add_parser.add_argument(
        "--version", help="Component version"
    )
    add_parser.add_argument(
        "--description", help="Component description"
    )
    
    # Remove command
    remove_parser = subparsers.add_parser(
        "remove", help="Remove a component from the manifest"
    )
    remove_parser.add_argument(
        "component_id", help="ID of the component to remove"
    )
    remove_parser.add_argument(
        "--manifest", help="Path to manifest file (default: manifest.json at repo root)"
    )
    
    # Update command
    update_parser = subparsers.add_parser(
        "update", help="Update a component in the manifest"
    )
    update_parser.add_argument(
        "component_id", help="ID of the component to update"
    )
    update_parser.add_argument(
        "--manifest", help="Path to manifest file (default: manifest.json at repo root)"
    )
    update_parser.add_argument(
        "--service", help="Service name"
    )
    update_parser.add_argument(
        "--name", help="Component name"
    )
    update_parser.add_argument(
        "--path", help="Path to component directory"
    )
    update_parser.add_argument(
        "--version", help="Component version"
    )
    update_parser.add_argument(
        "--description", help="Component description"
    )
    update_parser.add_argument(
        "--deployment-status", choices=["deployed", "not_deployed", "unknown"],
        help="Deployment status"
    )
    
    # Search command
    search_parser = subparsers.add_parser(
        "search", help="Search for components in the manifest"
    )
    search_parser.add_argument(
        "--manifest", help="Path to manifest file (default: manifest.json at repo root)"
    )
    search_parser.add_argument(
        "--service", help="Filter by service name"
    )
    search_parser.add_argument(
        "--name", help="Filter by component name"
    )
    search_parser.add_argument(
        "--version", help="Filter by version"
    )
    search_parser.add_argument(
        "--deployment-status", choices=["deployed", "not_deployed", "unknown"],
        help="Filter by deployment status"
    )
    search_parser.add_argument(
        "--format", action="store_true", help="Format output as a readable table"
    )
    
    # Summary command
    summary_parser = subparsers.add_parser(
        "summary", help="Generate a summary of the manifest"
    )
    summary_parser.add_argument(
        "--manifest", help="Path to manifest file (default: manifest.json at repo root)"
    )
    
    # Global arguments
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")
    
    args = parser.parse_args()
    
    # Configure logging
    setup_logging(args.verbose)
    
    # Default to help if no command
    if not args.command:
        parser.print_help()
        return
    
    try:
        if args.command == "validate":
            manifest = load_manifest(args.manifest)
            is_valid, errors = validate_manifest(manifest)
            if is_valid:
                logging.info("Manifest validation passed")
                print("Manifest is valid.")
            else:
                logging.error("Manifest validation failed")
                print("Manifest validation failed with the following errors:")
                for error in errors:
                    print(f" - {error}")
                sys.exit(1)
        
        elif args.command == "list":
            manifest = load_manifest(args.manifest)
            formatted_list = list_components(manifest, args.format)
            if args.format:
                print(formatted_list)
            else:
                print(json.dumps(formatted_list, indent=2))
        
        elif args.command == "get":
            manifest = load_manifest(args.manifest)
            component = get_component_by_id(manifest, args.component_id)
            if component:
                print(json.dumps(component, indent=2))
            else:
                logging.error(f"Component with ID {args.component_id} not found")
                sys.exit(1)
        
        elif args.command == "add":
            manifest = load_manifest(args.manifest)
            
            # Create component dictionary
            component = {
                "id": args.id,
                "service": args.service,
                "name": args.name,
                "path": args.path
            }
            
            # Add optional fields
            if args.version:
                component["version"] = args.version
            
            if args.description:
                component["description"] = args.description
            
            # Add discovery timestamp
            component["discovered_at"] = datetime.utcnow().isoformat()
            
            # Add the component
            manifest = add_component(manifest, component)
            
            # Save the updated manifest
            if save_manifest(manifest, args.manifest):
                print(f"Component {args.id} added to manifest.")
            else:
                logging.error("Failed to save manifest")
                sys.exit(1)
        
        elif args.command == "remove":
            manifest = load_manifest(args.manifest)
            manifest, removed = remove_component(manifest, args.component_id)
            
            if removed:
                # Save the updated manifest
                if save_manifest(manifest, args.manifest):
                    print(f"Component {args.component_id} removed from manifest.")
                else:
                    logging.error("Failed to save manifest")
                    sys.exit(1)
            else:
                logging.error(f"Component with ID {args.component_id} not found")
                sys.exit(1)
        
        elif args.command == "update":
            manifest = load_manifest(args.manifest)
            
            # Create updates dictionary with only provided fields
            updates = {}
            if args.service:
                updates["service"] = args.service
            
            if args.name:
                updates["name"] = args.name
            
            if args.path:
                updates["path"] = args.path
            
            if args.version:
                updates["version"] = args.version
            
            if args.description:
                updates["description"] = args.description
            
            if hasattr(args, "deployment_status") and args.deployment_status:
                updates["deployment_status"] = args.deployment_status
            
            # Update last updated timestamp
            updates["last_updated"] = datetime.utcnow().isoformat()
            
            # Update the component
            manifest, success = update_component(manifest, args.component_id, updates)
            
            if success:
                # Save the updated manifest
                if save_manifest(manifest, args.manifest):
                    print(f"Component {args.component_id} updated in manifest.")
                else:
                    logging.error("Failed to save manifest")
                    sys.exit(1)
            else:
                logging.error(f"Component with ID {args.component_id} not found")
                sys.exit(1)
        
        elif args.command == "search":
            manifest = load_manifest(args.manifest)
            
            # Build criteria dictionary from provided arguments
            criteria = {}
            if args.service:
                criteria["service"] = args.service
            
            if args.name:
                criteria["name"] = args.name
            
            if args.version:
                criteria["version"] = args.version
            
            if hasattr(args, "deployment_status") and args.deployment_status:
                criteria["deployment_status"] = args.deployment_status
            
            # Search for matching components
            results = search_components(manifest, criteria)
            
            if args.format:
                # Create a temporary manifest with only the search results
                temp_manifest = {"components": results}
                formatted = list_components(temp_manifest, True)
                print(formatted)
            else:
                print(json.dumps(results, indent=2))
            
            logging.info(f"Search found {len(results)} component(s)")
        
        elif args.command == "summary":
            manifest = load_manifest(args.manifest)
            print_summary(manifest)
        
        else:
            parser.print_help()
    
    except Exception as e:
        logging.error(f"Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()