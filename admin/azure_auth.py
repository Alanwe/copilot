#!/usr/bin/env python
"""
Azure authentication script to attempt authentication from devcontainer.env credentials
and gracefully handle authentication failures.
"""

import os
import sys
import json
import logging
import subprocess
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

# Add the project root to sys.path to import common modules
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from common.authentication.azure_cli import (
        is_azure_authenticated,
        login_with_service_principal,
        ensure_authenticated,
    )
except ImportError:
    logging.warning("Could not import authentication modules, falling back to internal implementation")
    
    def is_azure_authenticated() -> bool:
        """Check if Azure CLI is authenticated."""
        try:
            subprocess.run(
                ["az", "account", "show"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True
            )
            return True
        except (subprocess.SubprocessError, FileNotFoundError):
            return False

    def login_with_service_principal(client_id, client_secret, tenant_id, subscription_id=None) -> bool:
        """Login to Azure using service principal credentials."""
        try:
            # Login using service principal
            subprocess.run(
                [
                    "az", "login",
                    "--service-principal",
                    "--username", client_id,
                    "--password", client_secret,
                    "--tenant", tenant_id,
                    "--output", "none"
                ],
                check=True
            )
            
            # Set subscription if provided
            if subscription_id:
                subprocess.run(
                    ["az", "account", "set", "--subscription", subscription_id, "--output", "none"],
                    check=True
                )
            
            logging.info("Successfully authenticated with Azure using service principal")
            return True
        except subprocess.SubprocessError as e:
            logging.error(f"Failed to authenticate with Azure using service principal: {str(e)}")
            return False

    def ensure_authenticated(subscription_id=None) -> bool:
        """Ensure Azure CLI is authenticated."""
        if is_azure_authenticated():
            return True
        return False


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
                    
                key, value = line.split('=', 1)
                env_vars[key.strip()] = value.strip()
                
        return env_vars
    except Exception as e:
        logging.error(f"Failed to parse environment file: {str(e)}")
        return {}


def try_authenticate_with_devcontainer_env():
    """
    Try to authenticate with Azure using credentials from devcontainer.env
    and gracefully handle failures.
    """
    # Check if already authenticated
    if is_azure_authenticated():
        logging.info("Already authenticated to Azure")
        return True
        
    # Find and load devcontainer.env
    repo_root = Path(__file__).parent.parent  # Assumes script is in admin/ directory
    devcontainer_env_path = repo_root / ".devcontainer" / "devcontainer.env"
    
    env_vars = load_env_file(devcontainer_env_path)
    
    # First try AZURE_CREDENTIALS JSON format
    azure_creds = env_vars.get("AZURE_CREDENTIALS")
    if azure_creds:
        try:
            # Strip quotes if present
            if azure_creds.startswith('"') and azure_creds.endswith('"'):
                azure_creds = azure_creds[1:-1]
                
            creds = json.loads(azure_creds)
            logging.info("Attempting to authenticate using AZURE_CREDENTIALS from devcontainer.env")
            if login_with_service_principal(
                creds.get("clientId"),
                creds.get("clientSecret"),
                creds.get("tenantId"),
                creds.get("subscriptionId")
            ):
                return True
        except json.JSONDecodeError:
            logging.warning("Failed to parse AZURE_CREDENTIALS as JSON")
    
    # Try individual service principal environment variables
    client_id = env_vars.get("AZURE_CLIENT_ID")
    client_secret = env_vars.get("AZURE_CLIENT_SECRET")
    tenant_id = env_vars.get("AZURE_TENANT_ID")
    subscription_id = env_vars.get("AZURE_SUBSCRIPTION_ID")
    
    if all([client_id, client_secret, tenant_id]):
        logging.info("Attempting to authenticate using service principal from devcontainer.env")
        if login_with_service_principal(
            client_id,
            client_secret,
            tenant_id,
            subscription_id
        ):
            return True
    
    # If all automatic methods failed, inform the user
    logging.warning("Azure CLI is not authenticated")
    print("\nAzure CLI is not authenticated or credentials in devcontainer.env are invalid.")
    print("Please authenticate manually using one of these methods:")
    print("  1. Run 'az login' in a terminal")
    print("  2. Run 'az login --use-device-code' if no browser is available")
    print("  3. Update the credentials in .devcontainer/devcontainer.env")
    print("\nFor more information, see docs/Azure_Setup.md\n")
    
    return False


if __name__ == "__main__":
    success = try_authenticate_with_devcontainer_env()
    sys.exit(0 if success else 1)
