# Authentication utilities for Azure Components Foundry

from .azure_cli import (
    ensure_authenticated,
    get_current_subscription,
    is_azure_authenticated,
    login_with_device_code,
    login_with_managed_identity,
    login_with_service_principal,
    is_devcontainer,
    is_github_actions
)

from .key_vault import (
    get_secret,
    get_secrets,
    set_secret
)

from .managed_identity import (
    get_credentials,
    get_token
)

__all__ = [
    # Azure CLI authentication
    'ensure_authenticated',
    'get_current_subscription',
    'is_azure_authenticated',
    'login_with_device_code',
    'login_with_managed_identity',
    'login_with_service_principal',
    'is_devcontainer',
    'is_github_actions',
    
    # Key Vault
    'get_secret',
    'get_secrets',
    'set_secret',
    
    # Managed Identity
    'get_credentials',
    'get_token',
]