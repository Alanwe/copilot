#!/usr/bin/env python
"""
Component discovery script for the Azure Components Foundry.
This script discovers and registers components, updating the component manifest.
"""

import argparse
import json
import logging
import os
import sys
import re
from pathlib import Path
import subprocess
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
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, check=True
        )
        return Path(result.stdout.strip())
    except Exception:
        # Fallback: assume script is in admin directory
        return Path(__file__).parent.parent


def discover_local_components():
    """
    Discover components in the local filesystem.
    
    Returns:
        A list of component dictionaries.
    """
    repo_root = get_repo_root()
    components_dir = repo_root / "components"
    components = []

    logging.info(f"Scanning for components in {components_dir}")
    
    # Check if components directory exists
    if not components_dir.exists():
        logging.warning(f"Components directory not found: {components_dir}")
        return components

    # Scan for components
    for service_dir in components_dir.iterdir():
        if not service_dir.is_dir():
            continue
        
        service_name = service_dir.name
        logging.debug(f"Scanning service: {service_name}")
        
        for component_dir in service_dir.iterdir():
            if not component_dir.is_dir():
                continue
            
            component_name = component_dir.name
            component_info = process_component(service_name, component_name, component_dir)
            
            if component_info:
                components.append(component_info)
                logging.info(f"Discovered component: {service_name}/{component_name}")
    
    logging.info(f"Discovered {len(components)} component(s) in the local filesystem")
    return components


def process_component(service_name, component_name, component_dir):
    """
    Process a single component directory and extract metadata.
    
    Args:
        service_name: The service name (parent directory)
        component_name: The component name (directory name)
        component_dir: Path object to the component directory
    
    Returns:
        A dictionary with component metadata or None if not a valid component
    """
    # Required files for a valid component
    required_files = [
        "pyproject.toml",  # For dependency management
    ]
    
    # Optional files with metadata
    metadata_files = {
        "pyproject.toml": extract_pyproject_metadata,
        "README.md": extract_readme_metadata,
    }
    
    # Check for required files
    for required_file in required_files:
        if not (component_dir / required_file).exists():
            logging.debug(f"Skipping {service_name}/{component_name}: Missing {required_file}")
            return None
    
    # Basic component info
    component_info = {
        "id": f"{service_name}-{component_name}",
        "service": service_name,
        "name": component_name,
        "path": str(component_dir.relative_to(get_repo_root())),
        "discovered_at": datetime.utcnow().isoformat(),
    }
    
    # Extract metadata from available files
    for metadata_file, extractor in metadata_files.items():
        file_path = component_dir / metadata_file
        if file_path.exists():
            try:
                file_metadata = extractor(file_path)
                component_info.update(file_metadata)
            except Exception as e:
                logging.warning(f"Error processing {metadata_file} for {service_name}/{component_name}: {str(e)}")
    
    # Look for deployment capabilities
    deployment_info = detect_deployment_capabilities(component_dir)
    if deployment_info:
        component_info.update(deployment_info)
    
    return component_info


def extract_pyproject_metadata(pyproject_path):
    """Extract metadata from a pyproject.toml file."""
    try:
        import toml
        with open(pyproject_path, 'r') as f:
            data = toml.load(f)
        
        metadata = {}
        
        # Extract basic info
        if "tool" in data and "poetry" in data["tool"]:
            poetry_data = data["tool"]["poetry"]
            
            if "name" in poetry_data:
                metadata["package_name"] = poetry_data["name"]
            
            if "version" in poetry_data:
                metadata["version"] = poetry_data["version"]
            
            if "description" in poetry_data:
                metadata["description"] = poetry_data["description"]
            
            if "authors" in poetry_data:
                metadata["authors"] = poetry_data["authors"]
            
            if "dependencies" in poetry_data:
                metadata["dependencies"] = list(poetry_data["dependencies"].keys())
        
        return metadata
    
    except ImportError:
        logging.warning("toml package not installed, skipping pyproject.toml parsing")
        return {}
    
    except Exception as e:
        logging.warning(f"Error parsing {pyproject_path}: {str(e)}")
        return {}


def extract_readme_metadata(readme_path):
    """Extract metadata from a README.md file."""
    try:
        with open(readme_path, 'r') as f:
            content = f.read()
        
        metadata = {}
        
        # Extract title from first heading
        title_match = re.search(r'^# (.+)$', content, re.MULTILINE)
        if title_match:
            metadata["title"] = title_match.group(1).strip()
        
        # Extract first paragraph as description if not too long
        desc_match = re.search(r'^# .+\n\n(.+?)(\n\n|\n#|$)', content, re.DOTALL)
        if desc_match:
            desc = desc_match.group(1).strip()
            # Only use if it's reasonably short
            if len(desc) <= 200:
                metadata["short_description"] = desc
        
        return metadata
    
    except Exception as e:
        logging.warning(f"Error parsing {readme_path}: {str(e)}")
        return {}


def detect_deployment_capabilities(component_dir):
    """Detect deployment capabilities of the component."""
    capabilities = {
        "deployment_targets": []
    }
    
    # Check for deployment directory
    deploy_dir = component_dir / "deployment"
    if not deploy_dir.exists() or not deploy_dir.is_dir():
        return capabilities
    
    # Check for deployment script
    deploy_script = deploy_dir / "deploy.py"
    if deploy_script.exists():
        capabilities["has_deployment_script"] = True
        
        # Try to determine deployment targets by parsing script
        try:
            with open(deploy_script, 'r') as f:
                content = f.read()
            
            if "deploy_to_aml" in content:
                capabilities["deployment_targets"].append("azure_ml")
            
            if "deploy_to_functions" in content:
                capabilities["deployment_targets"].append("azure_functions")
            
            if "deploy_to_aci" in content or "deploy_to_container" in content:
                capabilities["deployment_targets"].append("container")
        
        except Exception as e:
            logging.debug(f"Error parsing deployment script: {str(e)}")
    
    # Check for Dockerfile
    if (component_dir / "Dockerfile").exists():
        if "container" not in capabilities["deployment_targets"]:
            capabilities["deployment_targets"].append("container")
    
    # Check for Azure ML YAML definition
    aml_yaml_files = list(component_dir.glob("*.yaml"))
    if aml_yaml_files:
        if "azure_ml" not in capabilities["deployment_targets"]:
            capabilities["deployment_targets"].append("azure_ml")
    
    return capabilities


def discover_azure_resources(subscription_id=None, tag_name="foundry-component", tag_service=None):
    """
    Discover components deployed to Azure by querying resources with specific tags.
    
    Args:
        subscription_id: Azure subscription ID (optional)
        tag_name: Tag name to filter by (default: foundry-component)
        tag_service: Additional tag for filtering by service (optional)
    
    Returns:
        A list of component dictionaries from Azure.
    """
    components = []
    
    # Check if Azure CLI is available
    try:
        subprocess.run(["az", "--version"], check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        logging.error("Azure CLI not available. Cannot discover Azure resources.")
        return components
    
    logging.info("Discovering components in Azure...")
    
    try:
        # Build the Azure CLI command
        cmd = ["az", "resource", "list", "--tag", tag_name]
        
        if subscription_id:
            cmd.extend(["--subscription", subscription_id])
        
        if tag_service:
            cmd.extend(["--tag", f"{tag_service}"])
        
        # Run the Azure CLI command
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        resources = json.loads(result.stdout)
        
        # Process each resource
        for resource in resources:
            component_info = {
                "id": resource.get("name", "unknown"),
                "azure_resource_id": resource.get("id"),
                "resource_type": resource.get("type"),
                "location": resource.get("location"),
                "discovered_at": datetime.utcnow().isoformat(),
                "deployment_status": "deployed",
                "tags": resource.get("tags", {}),
            }
            
            # Extract component name and service from tags if available
            tags = resource.get("tags", {})
            if "foundry-component" in tags:
                component_info["name"] = tags["foundry-component"]
            
            if "foundry-service" in tags:
                component_info["service"] = tags["foundry-service"]
            
            components.append(component_info)
            logging.info(f"Discovered Azure resource: {component_info['id']} ({component_info['resource_type']})")
    
    except subprocess.CalledProcessError as e:
        logging.error(f"Error querying Azure resources: {e}")
        if e.stderr:
            logging.error(e.stderr)
    
    except Exception as e:
        logging.error(f"Error discovering Azure resources: {str(e)}")
    
    logging.info(f"Discovered {len(components)} component(s) in Azure")
    return components


def load_manifest(manifest_path=None):
    """
    Load the existing component manifest.
    
    Args:
        manifest_path: Path to the manifest file (optional)
    
    Returns:
        The manifest data as a dictionary.
    """
    # Default manifest path
    if manifest_path is None:
        manifest_path = get_repo_root() / "manifest.json"
    
    # Create default manifest if it doesn't exist
    if not manifest_path.exists():
        logging.warning(f"Manifest file not found at {manifest_path}, creating new one")
        return {
            "version": "1.0",
            "last_updated": datetime.utcnow().isoformat(),
            "components": []
        }
    
    # Load existing manifest
    try:
        with open(manifest_path, 'r') as f:
            manifest = json.load(f)
        logging.info(f"Loaded existing manifest with {len(manifest.get('components', []))} component(s)")
        return manifest
    
    except json.JSONDecodeError:
        logging.error(f"Manifest file {manifest_path} is not valid JSON")
        return {
            "version": "1.0",
            "last_updated": datetime.utcnow().isoformat(),
            "components": []
        }
    
    except Exception as e:
        logging.error(f"Error loading manifest: {str(e)}")
        return {
            "version": "1.0",
            "last_updated": datetime.utcnow().isoformat(),
            "components": []
        }


def update_manifest(manifest, new_components, azure_components=None):
    """
    Update the manifest with newly discovered components.
    
    Args:
        manifest: The current manifest dictionary
        new_components: List of newly discovered local components
        azure_components: List of components discovered in Azure (optional)
    
    Returns:
        The updated manifest dictionary.
    """
    # Create component map for quicker lookup
    component_map = {comp.get("id"): comp for comp in manifest.get("components", [])}
    
    # Update with local components
    for component in new_components:
        component_id = component.get("id")
        
        if component_id in component_map:
            # Update existing component
            logging.debug(f"Updating existing component: {component_id}")
            existing = component_map[component_id]
            
            # Preserve deployment information
            if "deployment_status" in existing:
                component["deployment_status"] = existing["deployment_status"]
            
            if "azure_resource_id" in existing:
                component["azure_resource_id"] = existing["azure_resource_id"]
            
            # Update in the map
            component_map[component_id] = component
        else:
            # Add new component
            logging.info(f"Adding new component to manifest: {component_id}")
            component_map[component_id] = component
    
    # Update with Azure components if provided
    if azure_components:
        for azure_component in azure_components:
            component_id = azure_component.get("id")
            
            if component_id in component_map:
                # Update existing component with Azure info
                logging.debug(f"Updating component with Azure info: {component_id}")
                existing = component_map[component_id]
                existing.update({
                    "deployment_status": "deployed",
                    "azure_resource_id": azure_component.get("azure_resource_id"),
                    "resource_type": azure_component.get("resource_type"),
                    "location": azure_component.get("location"),
                    "azure_tags": azure_component.get("tags", {})
                })
            else:
                # Add new component from Azure
                logging.info(f"Adding Azure component to manifest: {component_id}")
                component_map[component_id] = azure_component
    
    # Update manifest
    manifest["components"] = list(component_map.values())
    manifest["last_updated"] = datetime.utcnow().isoformat()
    manifest["component_count"] = len(manifest["components"])
    
    return manifest


def save_manifest(manifest, manifest_path=None, pretty=True):
    """
    Save the manifest to disk.
    
    Args:
        manifest: The manifest dictionary to save
        manifest_path: Path to save the manifest to (optional)
        pretty: Whether to format JSON with indentation
    
    Returns:
        True if successful, False otherwise
    """
    # Default manifest path
    if manifest_path is None:
        manifest_path = get_repo_root() / "manifest.json"
    
    try:
        with open(manifest_path, 'w') as f:
            if pretty:
                json.dump(manifest, f, indent=2)
            else:
                json.dump(manifest, f)
        
        logging.info(f"Manifest saved with {len(manifest.get('components', []))} component(s) to {manifest_path}")
        return True
    
    except Exception as e:
        logging.error(f"Error saving manifest: {str(e)}")
        return False


def validate_manifest(manifest):
    """
    Validate the manifest structure and content.
    
    Args:
        manifest: The manifest dictionary to validate
    
    Returns:
        (is_valid, errors) tuple with validation status and error messages
    """
    errors = []
    
    # Check basic structure
    if not isinstance(manifest, dict):
        errors.append("Manifest must be a JSON object")
        return False, errors
    
    # Check required fields
    if "version" not in manifest:
        errors.append("Missing required field: version")
    
    if "components" not in manifest:
        errors.append("Missing required field: components")
    elif not isinstance(manifest["components"], list):
        errors.append("Field 'components' must be a list")
    
    # Check component entries
    for i, component in enumerate(manifest.get("components", [])):
        if not isinstance(component, dict):
            errors.append(f"Component at index {i} must be a JSON object")
            continue
        
        # Required fields for each component
        for field in ["id", "name", "service"]:
            if field not in component:
                errors.append(f"Component at index {i} is missing required field: {field}")
    
    is_valid = len(errors) == 0
    return is_valid, errors


def main():
    """Main entry point for the component discovery script."""
    parser = argparse.ArgumentParser(
        description="Discover and register components in the Azure Components Foundry"
    )
    
    # Commands
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Local discovery
    local_parser = subparsers.add_parser(
        "local", help="Discover components in the local filesystem"
    )
    local_parser.add_argument(
        "--manifest", help="Path to manifest file (default: manifest.json at repo root)"
    )
    local_parser.add_argument(
        "--save", action="store_true", help="Save discovered components to manifest"
    )
    
    # Azure discovery
    azure_parser = subparsers.add_parser(
        "azure", help="Discover components deployed in Azure"
    )
    azure_parser.add_argument(
        "--subscription", help="Azure subscription ID (uses default if not specified)"
    )
    azure_parser.add_argument(
        "--tag-name", default="foundry-component", help="Tag name for components (default: foundry-component)"
    )
    azure_parser.add_argument(
        "--tag-service", help="Filter by service tag"
    )
    azure_parser.add_argument(
        "--manifest", help="Path to manifest file (default: manifest.json at repo root)"
    )
    azure_parser.add_argument(
        "--save", action="store_true", help="Save discovered components to manifest"
    )
    
    # All discovery (local + Azure)
    all_parser = subparsers.add_parser(
        "all", help="Discover components both locally and in Azure"
    )
    all_parser.add_argument(
        "--subscription", help="Azure subscription ID (uses default if not specified)"
    )
    all_parser.add_argument(
        "--tag-name", default="foundry-component", help="Tag name for components (default: foundry-component)"
    )
    all_parser.add_argument(
        "--tag-service", help="Filter by service tag"
    )
    all_parser.add_argument(
        "--manifest", help="Path to manifest file (default: manifest.json at repo root)"
    )
    all_parser.add_argument(
        "--save", action="store_true", help="Save discovered components to manifest"
    )
    
    # Validate manifest
    validate_parser = subparsers.add_parser(
        "validate", help="Validate the component manifest"
    )
    validate_parser.add_argument(
        "--manifest", help="Path to manifest file (default: manifest.json at repo root)"
    )
    
    # Global arguments
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")
    
    args = parser.parse_args()
    
    # Configure logging
    setup_logging(args.verbose)
    
    # Default command if none specified
    if not args.command:
        args.command = "local"
    
    # Resolve manifest path
    manifest_path = None
    if hasattr(args, "manifest") and args.manifest:
        manifest_path = Path(args.manifest)
    else:
        manifest_path = get_repo_root() / "manifest.json"
    
    # Execute requested command
    if args.command == "local":
        # Discover local components
        components = discover_local_components()
        
        # Print or save results
        if args.save:
            manifest = load_manifest(manifest_path)
            manifest = update_manifest(manifest, components)
            save_manifest(manifest, manifest_path)
        else:
            print(json.dumps(components, indent=2))
    
    elif args.command == "azure":
        # Discover Azure components
        azure_components = discover_azure_resources(
            subscription_id=args.subscription,
            tag_name=args.tag_name,
            tag_service=args.tag_service
        )
        
        # Print or save results
        if args.save:
            manifest = load_manifest(manifest_path)
            # Update with empty local components list to preserve structure but prioritize Azure info
            manifest = update_manifest(manifest, [], azure_components)
            save_manifest(manifest, manifest_path)
        else:
            print(json.dumps(azure_components, indent=2))
    
    elif args.command == "all":
        # Discover both local and Azure components
        local_components = discover_local_components()
        azure_components = discover_azure_resources(
            subscription_id=args.subscription,
            tag_name=args.tag_name,
            tag_service=args.tag_service
        )
        
        # Print or save results
        if args.save:
            manifest = load_manifest(manifest_path)
            manifest = update_manifest(manifest, local_components, azure_components)
            save_manifest(manifest, manifest_path)
        else:
            combined = {
                "local_components": local_components,
                "azure_components": azure_components
            }
            print(json.dumps(combined, indent=2))
    
    elif args.command == "validate":
        # Validate manifest
        manifest = load_manifest(manifest_path)
        is_valid, errors = validate_manifest(manifest)
        
        if is_valid:
            logging.info("Manifest validation successful")
            print("Manifest is valid.")
        else:
            logging.error("Manifest validation failed")
            print("Manifest is invalid. Errors:")
            for error in errors:
                print(f"- {error}")
            sys.exit(1)
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()