"""
Key Vault integration for Azure Components Foundry.
This module provides utilities for working with Azure Key Vault.
"""

import logging
from typing import Optional, Dict, Any

from .managed_identity import get_credentials


def get_secret(vault_name: str, secret_name: str, client_id: Optional[str] = None) -> str:
    """
    Get a secret from Azure Key Vault.
    
    Args:
        vault_name: Name of the Key Vault
        secret_name: Name of the secret to retrieve
        client_id: Optional client ID for managed identity
        
    Returns:
        Secret value as a string
    """
    try:
        from azure.keyvault.secrets import SecretClient
        from azure.core.exceptions import ResourceNotFoundError
        
        credentials = get_credentials(client_id)
        vault_url = f"https://{vault_name}.vault.azure.net/"
        
        logging.info(f"Getting secret '{secret_name}' from Key Vault '{vault_name}'")
        client = SecretClient(vault_url=vault_url, credential=credentials)
        
        try:
            secret = client.get_secret(secret_name)
            return secret.value
        except ResourceNotFoundError:
            logging.error(f"Secret '{secret_name}' not found in Key Vault '{vault_name}'")
            raise
            
    except ImportError:
        logging.error("Azure Key Vault package not installed. Install with 'pip install azure-keyvault-secrets'")
        raise


def get_secrets(vault_name: str, secret_names: list, client_id: Optional[str] = None) -> Dict[str, str]:
    """
    Get multiple secrets from Azure Key Vault.
    
    Args:
        vault_name: Name of the Key Vault
        secret_names: List of secret names to retrieve
        client_id: Optional client ID for managed identity
        
    Returns:
        Dictionary of secret names and values
    """
    secrets = {}
    for name in secret_names:
        secrets[name] = get_secret(vault_name, name, client_id)
    return secrets


def set_secret(vault_name: str, secret_name: str, secret_value: str, client_id: Optional[str] = None) -> None:
    """
    Set a secret in Azure Key Vault.
    
    Args:
        vault_name: Name of the Key Vault
        secret_name: Name of the secret
        secret_value: Value of the secret
        client_id: Optional client ID for managed identity
    """
    try:
        from azure.keyvault.secrets import SecretClient
        
        credentials = get_credentials(client_id)
        vault_url = f"https://{vault_name}.vault.azure.net/"
        
        logging.info(f"Setting secret '{secret_name}' in Key Vault '{vault_name}'")
        client = SecretClient(vault_url=vault_url, credential=credentials)
        client.set_secret(secret_name, secret_value)
        
    except ImportError:
        logging.error("Azure Key Vault package not installed. Install with 'pip install azure-keyvault-secrets'")
        raise