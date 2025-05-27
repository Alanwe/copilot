#!/bin/bash
set -e

echo "Running post-creation setup..."

# Check if Poetry is installed, install if not available
if ! command -v poetry &> /dev/null; then
  echo "Poetry not found, installing..."
  curl -sSL https://install.python-poetry.org | python3 -
  export PATH="$HOME/.local/bin:$PATH"
  echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
fi

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
  cat > ~/.azure/workspacedefaults/config.json << EOFMARKER
{
  "defaults": {
    "subscription": "$SUBSCRIPTION_ID"
  }
}
EOFMARKER

  echo "Azure workspace defaults configured."
else
  echo "Azure CLI is not authenticated. Please run 'az login' to authenticate."
  echo "For more information, see docs/Azure_Setup.md"
fi
