"""
Azure CLI authentication utilities for Azure Components Foundry.
This module provides utilities for authenticating with Azure using the Azure CLI.
"""

import json
import logging
import os
import subprocess
from typing import Optional, Dict, Any, Tuple


def is_devcontainer() -> bool:
    """
    Check if running in a devcontainer environment.
    
    Returns:
        bool: True if running in a devcontainer, False otherwise.
    """
    return os.environ.get("REMOTE_CONTAINERS", "") == "true" or os.path.exists("/.dockerenv")


def is_github_actions() -> bool:
    """
    Check if running in a GitHub Actions environment.
    
    Returns:
        bool: True if running in GitHub Actions, False otherwise.
    """
    return os.environ.get("GITHUB_ACTIONS", "") == "true"


def is_azure_authenticated() -> bool:
    """
    Check if Azure CLI is authenticated.
    
    Returns:
        bool: True if authenticated, False otherwise.
    """
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


def get_current_subscription() -> Optional[Dict[str, Any]]:
    """
    Get the current Azure subscription information.
    
    Returns:
        Optional[Dict[str, Any]]: Subscription information, or None if not authenticated.
    """
    try:
        result = subprocess.run(
            ["az", "account", "show", "--output", "json"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True
        )
        return json.loads(result.stdout)
    except (subprocess.SubprocessError, json.JSONDecodeError, FileNotFoundError):
        return None


def login_with_service_principal(client_id: str, client_secret: str, 
                                tenant_id: str, subscription_id: Optional[str] = None) -> bool:
    """
    Login to Azure using service principal credentials.
    
    Args:
        client_id (str): Service principal client ID
        client_secret (str): Service principal client secret
        tenant_id (str): Azure tenant ID
        subscription_id (Optional[str]): Optional subscription ID to set as default
        
    Returns:
        bool: True if login was successful, False otherwise
    """
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


def login_with_managed_identity(client_id: Optional[str] = None) -> bool:
    """
    Login to Azure using managed identity.
    
    Args:
        client_id (Optional[str]): Optional client ID for the managed identity
        
    Returns:
        bool: True if login was successful, False otherwise
    """
    try:
        cmd = ["az", "login", "--identity", "--output", "none"]
        if client_id:
            cmd.extend(["--username", client_id])
            
        subprocess.run(cmd, check=True)
        logging.info("Successfully authenticated with Azure using managed identity")
        return True
    except subprocess.SubprocessError as e:
        logging.error(f"Failed to authenticate with Azure using managed identity: {str(e)}")
        return False


def login_with_device_code() -> bool:
    """
    Login to Azure using device code flow (for environments without a browser).
    
    Returns:
        bool: True if login was successful, False otherwise
    """
    try:
        subprocess.run(["az", "login", "--use-device-code"], check=True)
        logging.info("Successfully authenticated with Azure using device code")
        return True
    except subprocess.SubprocessError as e:
        logging.error(f"Failed to authenticate with Azure using device code: {str(e)}")
        return False


def ensure_authenticated(subscription_id: Optional[str] = None) -> bool:
    """
    Ensure Azure CLI is authenticated, attempting login if required.
    
    This function will try various authentication methods based on the environment:
    1. Check if already authenticated
    2. Try service principal credentials from environment variables
    3. Try managed identity if running in Azure
    4. Prompt for interactive login as a last resort
    
    Args:
        subscription_id (Optional[str]): Optional subscription ID to set as default
        
    Returns:
        bool: True if authentication was successful, False otherwise
    """
    # Check if already authenticated
    if is_azure_authenticated():
        current_sub = get_current_subscription()
        
        # If no specific subscription requested or already on the right subscription
        if not subscription_id or (current_sub and current_sub.get("id") == subscription_id):
            logging.info(f"Already authenticated to Azure subscription: {current_sub.get('name')}")
            return True
            
        # If authenticated but need to switch subscription
        if subscription_id:
            try:
                subprocess.run(
                    ["az", "account", "set", "--subscription", subscription_id, "--output", "none"],
                    check=True
                )
                logging.info(f"Switched to subscription ID: {subscription_id}")
                return True
            except subprocess.SubprocessError:
                logging.warning(f"Failed to switch to subscription ID: {subscription_id}")
                # Continue with re-authentication attempts
    
    # Try service principal from environment variables
    sp_env_vars = (
        os.environ.get("AZURE_CLIENT_ID"),
        os.environ.get("AZURE_CLIENT_SECRET"),
        os.environ.get("AZURE_TENANT_ID")
    )
    
    if all(sp_env_vars):
        if login_with_service_principal(
            sp_env_vars[0], sp_env_vars[1], sp_env_vars[2],
            subscription_id or os.environ.get("AZURE_SUBSCRIPTION_ID")
        ):
            return True
    
    # Try AZURE_CREDENTIALS JSON format (used by GitHub Actions)
    azure_creds = os.environ.get("AZURE_CREDENTIALS")
    if azure_creds:
        try:
            creds = json.loads(azure_creds)
            if login_with_service_principal(
                creds.get("clientId"),
                creds.get("clientSecret"),
                creds.get("tenantId"),
                subscription_id or creds.get("subscriptionId")
            ):
                return True
        except json.JSONDecodeError:
            logging.warning("Failed to parse AZURE_CREDENTIALS as JSON")
    
    # Try managed identity (when running in Azure)
    if "IDENTITY_ENDPOINT" in os.environ:
        client_id = os.environ.get("AZURE_CLIENT_ID")  # Optional client ID
        if login_with_managed_identity(client_id):
            if subscription_id:
                try:
                    subprocess.run(
                        ["az", "account", "set", "--subscription", subscription_id, "--output", "none"],
                        check=True
                    )
                except subprocess.SubprocessError:
                    logging.warning(f"Authenticated with managed identity but failed to set subscription: {subscription_id}")
                    return False
            return True
    
    # If we're in a non-interactive environment, we can't proceed
    if is_github_actions() or is_devcontainer() or not os.isatty(0):
        logging.error("No valid authentication method available for non-interactive environment")
        return False
    
    # Last resort: interactive login
    logging.info("No automatic authentication method available, attempting interactive login")
    print("Please log in to your Azure account:")
    
    # Choose the right interactive login method
    if os.environ.get("DISPLAY") or not is_devcontainer():
        # Use standard login if display is available
        try:
            subprocess.run(["az", "login"], check=True)
            logging.info("Interactive login successful")
            
            # Set subscription if needed
            if subscription_id:
                subprocess.run(
                    ["az", "account", "set", "--subscription", subscription_id, "--output", "none"],
                    check=True
                )
            return True
        except subprocess.SubprocessError:
            logging.error("Interactive login failed")
            return False
    else:
        # Use device code login for environments without a browser
        return login_with_device_code()