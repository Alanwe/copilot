#!/bin/bash
set -e

echo "Running post-creation setup..."

# Install project dependencies
if [ -f "pyproject.toml" ]; then
  echo "Installing project dependencies with Poetry..."
  poetry install
fi

# Set up Azure CLI workspace defaults if credentials are available
if az account show > /dev/null 2>&1; then
  echo "Azure CLI is authenticated. Setting up workspace defaults..."
  
  # Get account info
  SUBSCRIPTION_NAME=$(az account show --query name -o tsv)
  SUBSCRIPTION_ID=$(az account show --query id -o tsv)
  
  echo "Using subscription: $SUBSCRIPTION_NAME ($SUBSCRIPTION_ID)"
  
  # Create directory for workspace config
  mkdir -p ~/.azure/workspacedefaults
  
  # Create workspace config file
  cat > ~/.azure/workspacedefaults/config.json << EOF
{
  "defaults": {
    "subscription": "$SUBSCRIPTION_ID"
  }
}
EOF

  echo "Azure workspace defaults configured."
else
  echo "Azure CLI is not authenticated. Please run 'az login' to authenticate."
  echo "For more information, see docs/Azure_Setup.md"
fi