"""
Azure Blob Storage integration for Azure Components Foundry.
This module provides utilities for working with Azure Blob Storage.
"""

import logging
import os
from typing import Optional, List

from ..authentication.managed_identity import get_credentials


def create_client(account_name: str, credentials=None, client_id: Optional[str] = None):
    """
    Create a Blob Storage client.
    
    Args:
        account_name: Storage account name
        credentials: Azure credentials object, or None to use managed identity
        client_id: Optional client ID for managed identity
        
    Returns:
        BlobServiceClient
    """
    try:
        from azure.storage.blob import BlobServiceClient
        
        if not credentials:
            credentials = get_credentials(client_id)
            
        account_url = f"https://{account_name}.blob.core.windows.net/"
        logging.info(f"Creating Blob Storage client for account: {account_name}")
        
        return BlobServiceClient(account_url=account_url, credential=credentials)
        
    except ImportError:
        logging.error("Azure Storage package not installed. Install with 'pip install azure-storage-blob'")
        raise


def upload_file(client, container_name: str, local_path: str, blob_name: Optional[str] = None) -> str:
    """
    Upload a file to Blob Storage.
    
    Args:
        client: BlobServiceClient
        container_name: Name of the container
        local_path: Path to the local file
        blob_name: Name for the blob (if None, uses local file name)
        
    Returns:
        URL of the uploaded blob
    """
    if not blob_name:
        blob_name = os.path.basename(local_path)
        
    container_client = client.get_container_client(container_name)
    
    # Create container if it doesn't exist
    try:
        if not container_client.exists():
            logging.info(f"Creating container: {container_name}")
            container_client.create_container()
    except Exception as e:
        logging.warning(f"Error checking/creating container: {str(e)}")
    
    # Upload the file
    blob_client = container_client.get_blob_client(blob_name)
    logging.info(f"Uploading file {local_path} to {container_name}/{blob_name}")
    
    with open(local_path, "rb") as data:
        blob_client.upload_blob(data, overwrite=True)
        
    return blob_client.url


def download_file(client, container_name: str, blob_name: str, local_path: str) -> str:
    """
    Download a file from Blob Storage.
    
    Args:
        client: BlobServiceClient
        container_name: Name of the container
        blob_name: Name of the blob
        local_path: Local path to save the file
        
    Returns:
        Path of the downloaded file
    """
    container_client = client.get_container_client(container_name)
    blob_client = container_client.get_blob_client(blob_name)
    
    logging.info(f"Downloading blob {container_name}/{blob_name} to {local_path}")
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(os.path.abspath(local_path)), exist_ok=True)
    
    with open(local_path, "wb") as file:
        download_stream = blob_client.download_blob()
        file.write(download_stream.readall())
    
    return local_path


def list_blobs(client, container_name: str, prefix: Optional[str] = None) -> List[str]:
    """
    List blobs in a container.
    
    Args:
        client: BlobServiceClient
        container_name: Name of the container
        prefix: Optional prefix filter
        
    Returns:
        List of blob names
    """
    container_client = client.get_container_client(container_name)
    blobs = container_client.list_blobs(name_starts_with=prefix)
    
    return [blob.name for blob in blobs]