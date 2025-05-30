#!/usr/bin/env python
"""
Azure environment initialization script.
This script is designed to be run during container startup to check Azure connectivity
and initialize the environment if needed.
"""

import os
import sys
import time
import json
import logging
import subprocess
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s",
)

def print_status(message, status="info"):
    """Print a status message with appropriate formatting."""
    if status == "success":
        print(f"✓ {message}")
    elif status == "error":
        print(f"❌ {message}")
    elif status == "warning":
        print(f"⚠️ {message}")
    else:
        print(f"  {message}")

def run_command(cmd, timeout=30, check=False):
    """Run a command and return the result."""
    try:
        result = subprocess.run(
            cmd, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            text=True, 
            timeout=timeout, 
            check=check
        )
        return result
    except (subprocess.SubprocessError, subprocess.TimeoutExpired) as e:
        return None

def check_azure_cli():
    """Check if Azure CLI is installed and working."""
    result = run_command(["az", "--version"])
    return result is not None and result.returncode == 0

def check_az_connectivity():
    """
    Check if we can connect to Azure services.
    
    Returns:
        tuple: (success, message)
    """
    # Simple connectivity check using az cli
    result = run_command(["az", "cloud", "list", "--output", "none"], timeout=10)
    if result is None or result.returncode != 0:
        return False, "Cannot connect to Azure services. Network connectivity issues detected."
    return True, "Successfully connected to Azure services"

def check_azure_auth():
    """Check if already authenticated with Azure."""
    result = run_command(["az", "account", "show"], timeout=10)
    return result is not None and result.returncode == 0

def main():
    print("\n=== Azure Environment Setup ===\n")
    
    # Check if Azure CLI is installed
    if not check_azure_cli():
        print_status("Azure CLI not installed or not working properly", "error")
        return 1
    
    print_status("Azure CLI is installed", "success")
    
    # Check network connectivity
    connectivity_ok, message = check_az_connectivity()
    if not connectivity_ok:
        print_status(message, "error")
        print_status("Network connectivity to Azure services is required for Azure operations", "warning")
        print_status("This could be due to network restrictions in your environment", "info")
        print_status("Please check your network connection and proxy settings", "info")
        print()
        print_status("For more information, see docs/Azure_Setup.md", "info")
        print()
        print_status("Continuing without Azure authentication...", "info")
        return 0  # Return success to allow container to start
    
    # Check authentication
    if check_azure_auth():
        print_status("Already authenticated with Azure", "success")
        return 0
    
    print_status("Not authenticated with Azure", "warning")
    
    # Load service principal credentials if available
    repo_root = Path(__file__).parent.parent
    devcontainer_env_path = repo_root / ".devcontainer" / "devcontainer.env"
    
    if not devcontainer_env_path.exists():
        print_status("No devcontainer.env file found for service principal credentials", "warning")
        print_status("For authentication instructions, see docs/Azure_Setup.md", "info")
        return 0
    
    # Basic attempt to use service principal if available
    print_status("Service principal credentials found in devcontainer.env", "info")
    print_status("Attempting to authenticate with service principal...", "info")
    
    # Run the authentication script with extra time allowed
    auth_script = repo_root / "admin" / "check_azure_connectivity.py"
    
    if auth_script.exists():
        result = run_command(["python", str(auth_script)])
        if result and result.returncode == 0:
            print_status("Successfully authenticated with Azure", "success")
        else:
            print_status("Failed to authenticate with service principal", "warning")
            print_status("For manual authentication, run 'az login'", "info")
    else:
        print_status("Authentication script not found", "error")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
