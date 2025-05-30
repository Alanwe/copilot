"""
Managed Identity authentication for Azure Components Foundry.
This module provides utilities for authenticating with Azure using managed identities.
"""

import logging
from typing import Optional


def get_credentials(client_id: Optional[str] = None):
    """
    Get credentials using managed identity.
    
    Args:
        client_id: Optional client ID for the managed identity
        
    Returns:
        Azure credentials object
    """
    try:
        from azure.identity import DefaultAzureCredential, ManagedIdentityCredential
        
        logging.info("Getting managed identity credentials")
        
        if client_id:
            return ManagedIdentityCredential(client_id=client_id)
        else:
            # DefaultAzureCredential tries multiple authentication methods including managed identity
            return DefaultAzureCredential()
            
    except ImportError:
        logging.error("Azure Identity package not installed. Install with 'pip install azure-identity'")
        raise


def get_token(resource_uri: str, client_id: Optional[str] = None):
    """
    Get authentication token for a specific resource.
    
    Args:
        resource_uri: URI of the resource to get a token for
        client_id: Optional client ID for the managed identity
        
    Returns:
        Authentication token
    """
    try:
        credentials = get_credentials(client_id)
        token = credentials.get_token(resource_uri)
        return token.token
    except Exception as e:
        logging.error(f"Error getting token: {str(e)}")
        raise