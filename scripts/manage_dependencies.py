#!/usr/bin/env python
"""
Dependency management script for Azure Components Foundry.
This script helps manage dependencies across multiple components.
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path


def find_components():
    """Find all components in the repository."""
    components_dir = Path(__file__).parent.parent / "components"
    components = []
    
    # Check if components directory exists
    if not components_dir.exists():
        return components
    
    # Find all components with a pyproject.toml file
    for service_dir in components_dir.iterdir():
        if not service_dir.is_dir():
            continue
            
        for component_dir in service_dir.iterdir():
            if not component_dir.is_dir():
                continue
                
            pyproject_path = component_dir / "pyproject.toml"
            if pyproject_path.exists():
                components.append((service_dir.name, component_dir.name))
    
    return components


def create_component_env(service_name, component_name, force=False):
    """Create a virtual environment for a component."""
    component_path = Path(__file__).parent.parent / "components" / service_name / component_name
    
    if not component_path.exists():
        print(f"Component {service_name}/{component_name} not found.")
        return False
    
    pyproject_path = component_path / "pyproject.toml"
    if not pyproject_path.exists():
        print(f"No pyproject.toml found for component {service_name}/{component_name}.")
        return False
    
    # Execute poetry commands
    try:
        os.chdir(component_path)
        
        # Install dependencies using Poetry
        print(f"Creating environment for {service_name}/{component_name}...")
        subprocess.run(
            ["poetry", "install"] + (["--force"] if force else []),
            check=True,
        )
        
        # Generate requirements.txt for compatibility with other tools
        print("Generating requirements.txt...")
        with open("requirements.txt", "w") as req_file:
            subprocess.run(
                ["poetry", "export", "--format", "requirements.txt", "--without-hashes"],
                stdout=req_file,
                check=True,
            )
        
        print(f"Environment for {service_name}/{component_name} created successfully.")
        return True
    
    except subprocess.CalledProcessError as e:
        print(f"Failed to create environment: {e}")
        return False


def create_all_environments(force=False):
    """Create environments for all components."""
    components = find_components()
    
    if not components:
        print("No components found with pyproject.toml files.")
        return
    
    success = 0
    failed = 0
    
    for service_name, component_name in components:
        if create_component_env(service_name, component_name, force):
            success += 1
        else:
            failed += 1
    
    print(f"Created {success} environments, {failed} failed.")


def init_new_component(service_name, component_name):
    """Initialize a new component with a basic pyproject.toml."""
    component_path = Path(__file__).parent.parent / "components" / service_name / component_name
    
    if not component_path.exists():
        print(f"Component directory {service_name}/{component_name} not found.")
        return False
    
    pyproject_path = component_path / "pyproject.toml"
    if pyproject_path.exists():
        print(f"pyproject.toml already exists for {service_name}/{component_name}.")
        return False
    
    # Create basic pyproject.toml
    basic_pyproject = f"""[tool.poetry]
name = "{service_name}-{component_name}"
version = "0.1.0"
description = "Azure Components Foundry component"
authors = ["Your Organization <info@example.com>"]

[tool.poetry.dependencies]
python = "^3.8"
# Add component-specific dependencies here

# Include shared foundry libraries
azure-components-foundry = {{path = "../../../", develop = true}}

[tool.poetry.group.dev.dependencies]
pytest = "^7.4.0"
pytest-cov = "^4.1.0"

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"
"""
    
    try:
        os.makedirs(component_path, exist_ok=True)
        with open(pyproject_path, "w") as f:
            f.write(basic_pyproject)
        
        print(f"Created pyproject.toml for {service_name}/{component_name}.")
        return True
    
    except Exception as e:
        print(f"Failed to create pyproject.toml: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Manage dependencies for Azure Components Foundry"
    )
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Create environment command
    env_parser = subparsers.add_parser("env", help="Create virtual environments")
    env_parser.add_argument(
        "--all", action="store_true", help="Create environments for all components"
    )
    env_parser.add_argument(
        "--service", help="Service name for specific component"
    )
    env_parser.add_argument(
        "--component", help="Component name for specific component"
    )
    env_parser.add_argument(
        "--force", action="store_true", help="Force recreation of environments"
    )
    
    # Init component command
    init_parser = subparsers.add_parser(
        "init", help="Initialize a new component with pyproject.toml"
    )
    init_parser.add_argument(
        "--service", required=True, help="Service name for new component"
    )
    init_parser.add_argument(
        "--component", required=True, help="Component name for new component"
    )
    
    # List components command
    subparsers.add_parser("list", help="List all components with pyproject.toml")
    
    args = parser.parse_args()
    
    # Execute requested command
    if args.command == "env":
        if args.all:
            create_all_environments(force=args.force)
        elif args.service and args.component:
            create_component_env(args.service, args.component, force=args.force)
        else:
            parser.error("Please specify --all or both --service and --component")
    
    elif args.command == "init":
        init_new_component(args.service, args.component)
    
    elif args.command == "list":
        components = find_components()
        if components:
            print("Found components:")
            for service_name, component_name in components:
                print(f"  - {service_name}/{component_name}")
        else:
            print("No components found with pyproject.toml files.")
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()