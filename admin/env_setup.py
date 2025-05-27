#!/usr/bin/env python
"""
Environment setup and validation script for the Azure Components Foundry.
This script helps set up and validate local development environments.
"""

import argparse
import logging
import os
import platform
import shutil
import subprocess
import sys
import json
from pathlib import Path


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


def check_system_requirements():
    """
    Check basic system requirements for development.
    
    Returns:
        A dictionary with check results.
    """
    requirements = {
        "os": {
            "name": platform.system(),
            "version": platform.version(),
            "status": "ok"
        },
        "python": {
            "version": platform.python_version(),
            "path": sys.executable,
            "status": "ok" if sys.version_info >= (3, 8) else "warning"
        }
    }
    
    # Python version warning
    if requirements["python"]["status"] == "warning":
        logging.warning(
            f"Python version {requirements['python']['version']} detected. "
            "Version 3.8 or higher is recommended."
        )
    
    return requirements


def check_tool_availability():
    """
    Check if essential tools are available.
    
    Returns:
        A dictionary with tool check results.
    """
    tools = {}
    
    # Check for Poetry
    try:
        result = subprocess.run(
            ["poetry", "--version"], 
            capture_output=True, text=True, check=True
        )
        output = result.stdout.strip()
        version = output.split()[-1]
        tools["poetry"] = {"available": True, "version": version}
        logging.info(f"Poetry found: {output}")
    except (subprocess.SubprocessError, FileNotFoundError):
        tools["poetry"] = {"available": False}
        logging.warning("Poetry not found. Please install Poetry.")
    
    # Check for Azure CLI
    try:
        result = subprocess.run(
            ["az", "--version"], 
            capture_output=True, text=True, check=True
        )
        # Extract version - first line typically contains the main CLI version
        first_line = result.stdout.split("\n")[0]
        version = first_line.split()[-1]
        tools["azure_cli"] = {"available": True, "version": version}
        logging.info(f"Azure CLI found: {version}")
        
        # Check if logged in
        login_result = subprocess.run(
            ["az", "account", "show"], 
            capture_output=True, text=True, check=False
        )
        tools["azure_cli"]["logged_in"] = login_result.returncode == 0
        
        if not tools["azure_cli"]["logged_in"]:
            logging.warning("Azure CLI not logged in. Run 'az login' to authenticate.")
    
    except (subprocess.SubprocessError, FileNotFoundError):
        tools["azure_cli"] = {"available": False}
        logging.warning("Azure CLI not found. Please install Azure CLI.")
    
    # Check for Git
    try:
        result = subprocess.run(
            ["git", "--version"], 
            capture_output=True, text=True, check=True
        )
        output = result.stdout.strip()
        tools["git"] = {"available": True, "version": output}
        logging.info(f"Git found: {output}")
    except (subprocess.SubprocessError, FileNotFoundError):
        tools["git"] = {"available": False}
        logging.warning("Git not found. Please install Git.")
    
    # Check for Docker if necessary
    if shutil.which("docker"):
        try:
            result = subprocess.run(
                ["docker", "--version"], 
                capture_output=True, text=True, check=True
            )
            output = result.stdout.strip()
            tools["docker"] = {"available": True, "version": output}
            logging.info(f"Docker found: {output}")
        except subprocess.SubprocessError:
            tools["docker"] = {"available": False}
            logging.warning("Docker found but not working properly.")
    else:
        tools["docker"] = {"available": False}
        logging.info("Docker not found. Required only for container deployments.")
    
    return tools


def setup_poetry():
    """
    Install Poetry if not available.
    
    Returns:
        True if successful, False otherwise.
    """
    try:
        # Check if Poetry is already installed
        result = subprocess.run(
            ["poetry", "--version"], 
            capture_output=True, text=True, check=False
        )
        
        if result.returncode == 0:
            logging.info(f"Poetry already installed: {result.stdout.strip()}")
            return True
        
        # Install Poetry
        logging.info("Installing Poetry...")
        
        # Use the official Poetry installer
        installer_cmd = [
            "curl", "-sSL", 
            "https://install.python-poetry.org", 
            "-o", "/tmp/install-poetry.py"
        ]
        subprocess.run(installer_cmd, check=True)
        
        # Run the installer
        subprocess.run([sys.executable, "/tmp/install-poetry.py"], check=True)
        
        # Check installation
        result = subprocess.run(
            ["poetry", "--version"], 
            capture_output=True, text=True, check=True
        )
        logging.info(f"Poetry installed successfully: {result.stdout.strip()}")
        return True
    
    except Exception as e:
        logging.error(f"Failed to install Poetry: {str(e)}")
        return False


def setup_azure_cli():
    """
    Install Azure CLI if not available.
    
    Returns:
        True if successful, False otherwise.
    """
    try:
        # Check if Azure CLI is already installed
        result = subprocess.run(
            ["az", "--version"], 
            capture_output=True, text=True, check=False
        )
        
        if result.returncode == 0:
            logging.info(f"Azure CLI already installed")
            return True
        
        # Install Azure CLI - instructions vary by OS
        system = platform.system().lower()
        
        if system == "linux":
            # For Linux, we'll use the package manager if possible
            if os.path.exists("/etc/debian_version"):  # Debian, Ubuntu, etc.
                logging.info("Installing Azure CLI (Debian/Ubuntu)...")
                subprocess.run([
                    "curl", "-sL", "https://aka.ms/InstallAzureCLIDeb", 
                    "-o", "/tmp/install-azure-cli.sh"
                ], check=True)
                subprocess.run(["sudo", "bash", "/tmp/install-azure-cli.sh"], check=True)
            else:
                logging.error("Automatic Azure CLI installation not supported on this Linux distribution.")
                logging.error("Please install manually: https://docs.microsoft.com/en-us/cli/azure/install-azure-cli")
                return False
        
        elif system == "darwin":  # macOS
            # Try using Homebrew if available
            if shutil.which("brew"):
                logging.info("Installing Azure CLI using Homebrew...")
                subprocess.run(["brew", "update"], check=True)
                subprocess.run(["brew", "install", "azure-cli"], check=True)
            else:
                logging.error("Homebrew not found, cannot install Azure CLI automatically.")
                logging.error("Please install manually: https://docs.microsoft.com/en-us/cli/azure/install-azure-cli-macos")
                return False
        
        elif system == "windows":
            logging.info("For Windows, please install Azure CLI from the official Microsoft installer")
            logging.info("Download URL: https://aka.ms/installazurecliwindows")
            logging.error("Cannot automatically install Azure CLI on Windows")
            return False
            
        else:
            logging.error(f"Automatic Azure CLI installation not supported on {system}")
            logging.error("Please install manually: https://docs.microsoft.com/en-us/cli/azure/install-azure-cli")
            return False
        
        # Check installation
        result = subprocess.run(
            ["az", "--version"], 
            capture_output=True, text=True, check=True
        )
        logging.info("Azure CLI installed successfully")
        return True
    
    except Exception as e:
        logging.error(f"Failed to install Azure CLI: {str(e)}")
        return False


def setup_root_environment():
    """
    Set up the root project environment using Poetry.
    
    Returns:
        True if successful, False otherwise.
    """
    repo_root = get_repo_root()
    pyproject_path = repo_root / "pyproject.toml"
    
    if not pyproject_path.exists():
        logging.error(f"No pyproject.toml found at {pyproject_path}")
        return False
    
    try:
        # Change to repo root directory
        os.chdir(repo_root)
        
        # Install dependencies using Poetry
        logging.info("Installing project dependencies using Poetry...")
        subprocess.run(["poetry", "install"], check=True)
        
        logging.info("Root environment setup complete")
        return True
    
    except subprocess.CalledProcessError as e:
        logging.error(f"Poetry command failed: {e}")
        return False
    
    except Exception as e:
        logging.error(f"Failed to set up root environment: {str(e)}")
        return False


def validate_environment():
    """
    Validate the development environment.
    
    Returns:
        A dictionary with validation results.
    """
    repo_root = get_repo_root()
    results = {
        "system": check_system_requirements(),
        "tools": check_tool_availability(),
        "project_structure": validate_project_structure(repo_root),
        "passed": True
    }
    
    # Check if any major issue exists
    if not results["tools"].get("poetry", {}).get("available", False):
        results["passed"] = False
    
    return results


def validate_project_structure(repo_root):
    """
    Validate the basic project structure.
    
    Args:
        repo_root: Path to repository root
    
    Returns:
        A dictionary with validation results.
    """
    structure = {
        "root_files": {
            "pyproject.toml": {
                "exists": (repo_root / "pyproject.toml").exists(),
                "status": "ok" if (repo_root / "pyproject.toml").exists() else "error"
            },
            "README.md": {
                "exists": (repo_root / "README.md").exists(),
                "status": "ok" if (repo_root / "README.md").exists() else "warning"
            }
        },
        "directories": {
            "components": {
                "exists": (repo_root / "components").exists() and (repo_root / "components").is_dir(),
                "status": "ok" if (repo_root / "components").exists() and (repo_root / "components").is_dir() else "error"
            },
            "scripts": {
                "exists": (repo_root / "scripts").exists() and (repo_root / "scripts").is_dir(),
                "status": "ok" if (repo_root / "scripts").exists() and (repo_root / "scripts").is_dir() else "warning"
            },
            "admin": {
                "exists": (repo_root / "admin").exists() and (repo_root / "admin").is_dir(),
                "status": "ok" if (repo_root / "admin").exists() and (repo_root / "admin").is_dir() else "warning"
            }
        }
    }
    
    # Check if any required directory or file is missing
    structure["status"] = "ok"
    for category in ["root_files", "directories"]:
        for item, info in structure[category].items():
            if info["status"] == "error":
                structure["status"] = "error"
                logging.error(f"Required {category.replace('_', ' ')} '{item}' not found")
            elif info["status"] == "warning":
                if structure["status"] != "error":
                    structure["status"] = "warning"
                logging.warning(f"Recommended {category.replace('_', ' ')} '{item}' not found")
    
    return structure


def setup_component_environments():
    """
    Set up environments for all components using the manage_dependencies.py script.
    
    Returns:
        A dictionary with results.
    """
    repo_root = get_repo_root()
    manage_dependencies_script = repo_root / "scripts" / "manage_dependencies.py"
    
    if not manage_dependencies_script.exists():
        logging.error(f"manage_dependencies.py script not found at {manage_dependencies_script}")
        return {"status": "error", "message": "Script not found"}
    
    try:
        # Run the script to set up all component environments
        logging.info("Setting up environments for all components...")
        result = subprocess.run(
            [sys.executable, str(manage_dependencies_script), "env", "--all"],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            logging.error(f"Failed to set up component environments: {result.stderr}")
            return {"status": "error", "message": result.stderr}
        
        logging.info("Component environments setup complete")
        return {"status": "ok", "output": result.stdout}
    
    except Exception as e:
        logging.error(f"Error setting up component environments: {str(e)}")
        return {"status": "error", "message": str(e)}


def install_azure_extensions(extensions=None, upgrade=False):
    """
    Install or update specified Azure CLI extensions.
    
    Args:
        extensions: List of extension names to install, or None for common extensions
        upgrade: Whether to upgrade existing extensions
        
    Returns:
        A dictionary with results of extension operations.
    """
    if not shutil.which("az"):
        logging.error("Azure CLI not found. Please install Azure CLI first.")
        return {"status": "error", "message": "Azure CLI not found"}
        
    # Default common extensions if none specified
    if not extensions:
        extensions = ["azure-devops", "storage-preview"]
        
    results = {
        "installed": [],
        "updated": [],
        "failed": [],
        "status": "ok"
    }
    
    try:
        # List existing extensions
        list_result = subprocess.run(
            ["az", "extension", "list", "--output", "json"],
            capture_output=True, text=True, check=True
        )
        installed_extensions = json.loads(list_result.stdout)
        installed_names = [ext["name"] for ext in installed_extensions]
        
        # Update existing extensions if requested
        if upgrade:
            logging.info("Upgrading Azure CLI extensions...")
            upgrade_result = subprocess.run(
                ["az", "extension", "update", "--all"],
                capture_output=True, text=True, check=False
            )
            if upgrade_result.returncode == 0:
                results["updated"] = installed_names
                logging.info(f"Successfully updated extensions: {', '.join(installed_names)}")
            else:
                logging.warning(f"Failed to update extensions: {upgrade_result.stderr}")
                results["status"] = "warning"
        
        # Install requested extensions
        for extension in extensions:
            if extension in installed_names:
                logging.info(f"Extension '{extension}' is already installed")
                continue
                
            logging.info(f"Installing Azure CLI extension: {extension}")
            install_result = subprocess.run(
                ["az", "extension", "add", "--name", extension, "--output", "json"],
                capture_output=True, text=True, check=False
            )
            
            if install_result.returncode == 0:
                results["installed"].append(extension)
                logging.info(f"Successfully installed extension: {extension}")
            else:
                results["failed"].append({
                    "name": extension,
                    "error": install_result.stderr.strip()
                })
                logging.error(f"Failed to install extension '{extension}': {install_result.stderr}")
                results["status"] = "error"
                
        return results
            
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to manage Azure extensions: {e}")
        if e.stderr:
            logging.error(e.stderr)
        return {"status": "error", "message": str(e), "stderr": e.stderr}
        
    except Exception as e:
        logging.error(f"Error managing Azure extensions: {str(e)}")
        return {"status": "error", "message": str(e)}


def setup_azure_environment(subscription_id=None, resource_group=None):
    """
    Configure the Azure environment for the project.
    
    Args:
        subscription_id: Azure subscription ID to use
        resource_group: Resource group to use
    
    Returns:
        A dictionary with results.
    """
    if not shutil.which("az"):
        logging.error("Azure CLI not found. Please install Azure CLI first.")
        return {"status": "error", "message": "Azure CLI not found"}
    
    try:
        # Check if logged in
        login_result = subprocess.run(
            ["az", "account", "show"],
            capture_output=True,
            text=True,
            check=False
        )
        
        if login_result.returncode != 0:
            logging.warning("Not logged into Azure. Initiating login...")
            login_process = subprocess.run(["az", "login"], check=True)
            if login_process.returncode != 0:
                return {"status": "error", "message": "Failed to log in to Azure"}
        
        # Set subscription if provided
        if subscription_id:
            logging.info(f"Setting Azure subscription to {subscription_id}")
            subprocess.run(
                ["az", "account", "set", "--subscription", subscription_id],
                check=True
            )
        
        # Get current subscription info
        sub_result = subprocess.run(
            ["az", "account", "show"],
            capture_output=True,
            text=True,
            check=True
        )
        sub_info = json.loads(sub_result.stdout)
        
        # Check if resource group exists
        if resource_group:
            rg_exists = subprocess.run(
                ["az", "group", "exists", "--name", resource_group],
                capture_output=True,
                text=True,
                check=True
            ).stdout.strip()
            
            if rg_exists.lower() == "false":
                logging.warning(f"Resource group '{resource_group}' does not exist")
        
        return {
            "status": "ok",
            "subscription": {
                "id": sub_info["id"],
                "name": sub_info["name"]
            },
            "resource_group": resource_group,
            "resource_group_exists": rg_exists.lower() == "true" if resource_group else None
        }
    
    except Exception as e:
        logging.error(f"Error setting up Azure environment: {str(e)}")
        return {"status": "error", "message": str(e)}


def main():
    """Main entry point for the environment setup script."""
    parser = argparse.ArgumentParser(
        description="Set up and validate local development environments"
    )
    
    # Commands
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Validate command
    validate_parser = subparsers.add_parser(
        "validate", help="Validate the development environment"
    )
    
    # Install command
    install_parser = subparsers.add_parser(
        "install", help="Install required tools and dependencies"
    )
    install_parser.add_argument(
        "--poetry", action="store_true", help="Install Poetry"
    )
    install_parser.add_argument(
        "--azure-cli", action="store_true", help="Install Azure CLI"
    )
    install_parser.add_argument(
        "--azure-extensions", nargs="*", metavar="EXT",
        help="Install specific Azure CLI extensions (space-separated list)"
    )
    install_parser.add_argument(
        "--upgrade-extensions", action="store_true", 
        help="Upgrade installed Azure extensions"
    )
    install_parser.add_argument(
        "--all", action="store_true", help="Install all required tools"
    )
    
    # Setup root command
    root_parser = subparsers.add_parser(
        "setup-root", help="Set up the root project environment"
    )
    
    # Setup components command
    components_parser = subparsers.add_parser(
        "setup-components", help="Set up environments for all components"
    )
    
    # Setup Azure environment
    azure_parser = subparsers.add_parser(
        "setup-azure", help="Configure Azure environment"
    )
    azure_parser.add_argument(
        "--subscription", help="Azure subscription ID to use"
    )
    azure_parser.add_argument(
        "--resource-group", help="Resource group to use"
    )
    
    # Setup all command
    all_parser = subparsers.add_parser(
        "setup-all", help="Set up the complete development environment"
    )
    all_parser.add_argument(
        "--subscription", help="Azure subscription ID to use"
    )
    all_parser.add_argument(
        "--resource-group", help="Resource group to use"
    )
    
    # Global arguments
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")
    
    args = parser.parse_args()
    
    # Configure logging
    setup_logging(args.verbose)
    
    # Default command if none specified
    if not args.command:
        args.command = "validate"
    
    # Execute requested command
    if args.command == "validate":
        results = validate_environment()
        print(json.dumps(results, indent=2))
        
        if results["passed"]:
            logging.info("Environment validation passed")
            sys.exit(0)
        else:
            logging.warning("Environment validation found issues")
            sys.exit(1)
    
    elif args.command == "install":
        if args.all or args.poetry:
            setup_poetry()
        
        if args.all or args.azure_cli:
            setup_azure_cli()
            
        if args.all or args.azure_extensions is not None or args.upgrade_extensions:
            # Only try to install extensions if they're explicitly requested or --all is specified
            if shutil.which("az"):
                extensions_result = install_azure_extensions(
                    extensions=args.azure_extensions,
                    upgrade=args.upgrade_extensions or args.all
                )
                if extensions_result["status"] != "ok":
                    logging.warning("Some Azure extensions could not be installed or updated")
            else:
                logging.error("Azure CLI not found. Cannot install extensions.")
                if not args.azure_cli and not args.all:
                    logging.error("Use --azure-cli to install the Azure CLI first")
    
    elif args.command == "setup-root":
        if setup_root_environment():
            logging.info("Root environment setup successful")
        else:
            logging.error("Root environment setup failed")
            sys.exit(1)
    
    elif args.command == "setup-components":
        result = setup_component_environments()
        if result["status"] == "ok":
            logging.info("Component environments setup successful")
        else:
            logging.error(f"Component environments setup failed: {result['message']}")
            sys.exit(1)
    
    elif args.command == "setup-azure":
        result = setup_azure_environment(args.subscription, args.resource_group)
        if result["status"] == "ok":
            logging.info(f"Using Azure subscription: {result['subscription']['name']} ({result['subscription']['id']})")
            if args.resource_group:
                if result.get("resource_group_exists"):
                    logging.info(f"Resource group '{args.resource_group}' exists")
                else:
                    logging.warning(f"Resource group '{args.resource_group}' does not exist")
        else:
            logging.error(f"Azure environment setup failed: {result['message']}")
            sys.exit(1)
    
    elif args.command == "setup-all":
        # Install required tools
        setup_poetry()
        setup_azure_cli()
        
        # Install common Azure extensions if CLI is available
        if shutil.which("az"):
            logging.info("Installing common Azure CLI extensions...")
            install_azure_extensions(upgrade=True)
        
        # Set up root environment
        if not setup_root_environment():
            logging.error("Root environment setup failed")
            sys.exit(1)
        
        # Set up component environments
        comp_result = setup_component_environments()
        if comp_result["status"] != "ok":
            logging.error(f"Component environments setup failed: {comp_result['message']}")
            sys.exit(1)
        
        # Set up Azure environment if tools are available
        if shutil.which("az"):
            azure_result = setup_azure_environment(args.subscription, args.resource_group)
            if azure_result["status"] == "ok":
                logging.info(f"Using Azure subscription: {azure_result['subscription']['name']}")
            else:
                logging.warning(f"Azure environment setup issue: {azure_result['message']}")
        
        logging.info("All environment setup tasks completed")
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()