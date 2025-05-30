#!/usr/bin/env python
"""
Azure connectivity checker and authentication helper.
Checks network connectivity to Azure services and attempts authentication
using service principal credentials if available.
"""

import os
import sys
import json
import socket
import subprocess
import logging
from pathlib import Path
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

# Azure endpoints to check connectivity
AZURE_ENDPOINTS = [
    ("login.microsoftonline.com", 443),  # Azure AD authentication
    ("management.azure.com", 443),        # Azure Resource Manager
    ("core.windows.net", 443)             # Azure Storage
]

def check_network_connectivity(host, port, timeout=5):
    """Check if we can connect to the specified host and port."""
    try:
        socket.setdefaulttimeout(timeout)
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((host, port))
        s.shutdown(socket.SHUT_RDWR)
        return True
    except (socket.timeout, socket.error) as e:
        logging.warning(f"Failed to connect to {host}:{port} - {str(e)}")
        return False
    finally:
        s.close()

def check_azure_connectivity():
    """
    Check connectivity to Azure endpoints.
    
    Returns:
        bool: True if all endpoints are reachable, False otherwise
        dict: Dictionary with detailed results for each endpoint
    """
    results = {}
    all_passed = True
    
    print("Checking connectivity to Azure services...")
    
    for host, port in AZURE_ENDPOINTS:
        connected = check_network_connectivity(host, port)
        results[f"{host}:{port}"] = connected
        all_passed = all_passed and connected
        
        status = "✓" if connected else "✗"
        print(f"  {status} {host}:{port}")
    
    return all_passed, results

def load_env_file(env_file_path):
    """Load environment variables from a .env file."""
    env_vars = {}
    
    if not os.path.exists(env_file_path):
        logging.warning(f"Environment file not found: {env_file_path}")
        return env_vars
    
    try:
        with open(env_file_path, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                    
                try:
                    key, value = line.split('=', 1)
                    env_vars[key.strip()] = value.strip()
                except ValueError:
                    continue
                
        return env_vars
    except Exception as e:
        logging.error(f"Failed to parse environment file: {str(e)}")
        return {}

def check_az_cli_installed():
    """Check if Azure CLI is installed."""
    try:
        subprocess.run(["az", "--version"], 
                      stdout=subprocess.PIPE,
                      stderr=subprocess.PIPE,
                      check=False)
        return True
    except FileNotFoundError:
        return False

def check_azure_authentication():
    """
    Check if already authenticated with Azure.
    
    Returns:
        bool: True if authenticated, False otherwise
    """
    try:
        result = subprocess.run(
            ["az", "account", "show"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            timeout=10
        )
        return result.returncode == 0
    except (subprocess.SubprocessError, subprocess.TimeoutExpired):
        return False

def try_authenticate_with_service_principal(client_id, client_secret, tenant_id, subscription_id=None):
    """
    Attempt to authenticate with Azure using service principal credentials.
    
    Returns:
        bool: True if authenticated successfully, False otherwise
    """
    try:
        cmd = [
            "az", "login",
            "--service-principal",
            "--username", client_id,
            "--password", client_secret,
            "--tenant", tenant_id,
            "--output", "none"
        ]
        
        # Set timeout to avoid hanging indefinitely
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            timeout=20
        )
        
        if result.returncode != 0:
            logging.warning(f"Service principal authentication failed: {result.stderr.decode('utf-8')}")
            return False
        
        # Set subscription if provided
        if subscription_id:
            subprocess.run(
                ["az", "account", "set", "--subscription", subscription_id, "--output", "none"],
                check=True,
                timeout=10
            )
        
        return True
    except (subprocess.SubprocessError, subprocess.TimeoutExpired) as e:
        logging.warning(f"Service principal authentication failed or timed out: {str(e)}")
        return False

def main():
    """Main function to check Azure connectivity and authentication."""
    # Check if Azure CLI is installed
    if not check_az_cli_installed():
        print("❌ Azure CLI not found. Please install Azure CLI first.")
        print("   See: https://docs.microsoft.com/en-us/cli/azure/install-azure-cli")
        return 1
    
    # Check Azure connectivity
    connectivity_ok, details = check_azure_connectivity()
    
    if not connectivity_ok:
        print("\n❌ Connectivity issues detected with Azure services.")
        print("   This may be due to network restrictions in your environment.")
        print("   Please check your network connection and proxy settings.")
        print("\nPossible solutions:")
        print("   1. Check if your network allows HTTPS connections to Azure services")
        print("   2. Configure proxy settings if your environment requires a proxy")
        print("   3. If using a VPN, ensure it allows connections to Azure services")
        print("\nFor more information, see docs/Azure_Setup.md")
        return 1
    
    print("\n✓ Network connectivity to Azure services looks good.")
    
    # Check if already authenticated
    if check_azure_authentication():
        print("✓ Already authenticated with Azure.")
        return 0
    
    print("\nNot currently authenticated with Azure. Checking for credentials...")
    
    # Look for service principal credentials in devcontainer.env
    repo_root = Path(__file__).parent.parent  # Assumes script is in admin/ directory
    devcontainer_env_path = repo_root / ".devcontainer" / "devcontainer.env"
    
    env_vars = load_env_file(devcontainer_env_path)
    authentication_success = False
    
    # Try AZURE_CREDENTIALS JSON format first
    azure_creds = env_vars.get("AZURE_CREDENTIALS")
    if azure_creds:
        try:
            # Strip quotes if present
            if azure_creds.startswith('"') and azure_creds.endswith('"'):
                azure_creds = azure_creds[1:-1]
                
            creds = json.loads(azure_creds)
            print("Attempting to authenticate using AZURE_CREDENTIALS from devcontainer.env...")
            
            authentication_success = try_authenticate_with_service_principal(
                creds.get("clientId"),
                creds.get("clientSecret"),
                creds.get("tenantId"),
                creds.get("subscriptionId")
            )
        except json.JSONDecodeError:
            logging.warning("Failed to parse AZURE_CREDENTIALS as JSON")
    
    # If that didn't work, try individual service principal environment variables
    if not authentication_success:
        client_id = env_vars.get("AZURE_CLIENT_ID")
        client_secret = env_vars.get("AZURE_CLIENT_SECRET")
        tenant_id = env_vars.get("AZURE_TENANT_ID")
        subscription_id = env_vars.get("AZURE_SUBSCRIPTION_ID")
        
        if all([client_id, client_secret, tenant_id]):
            print("Attempting to authenticate using service principal credentials from devcontainer.env...")
            
            authentication_success = try_authenticate_with_service_principal(
                client_id,
                client_secret,
                tenant_id,
                subscription_id
            )
    
    if authentication_success:
        print("\n✓ Successfully authenticated with Azure using service principal.")
        return 0
    else:
        print("\n❌ Failed to authenticate with Azure.")
        print("\nTo authenticate manually, please run one of the following commands:")
        print("   az login              # Standard login (opens a browser)")
        print("   az login --use-device-code  # Login without a browser")
        print("\nFor more information, see docs/Azure_Setup.md")
        return 1

if __name__ == "__main__":
    sys.exit(main())
