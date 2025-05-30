#!/bin/bash
set -e

echo "Running post-creation setup..."

# Check Azure directory mount
echo "Checking Azure directory mount..."
if [ -d "/home/vscode/.azure" ]; then
    echo "✅ Azure directory is mounted successfully"
else
    echo "❌ Warning: Azure directory is not mounted"
    echo "Expected location: /home/vscode/.azure"
fi


# Install Poetry
echo "Installing Poetry..."
curl -sSL https://install.python-poetry.org | python3 -

# Add Poetry to PATH
export PATH="/root/.local/bin:$HOME/.local/bin:$PATH"

# Now install project dependencies with Poetry
echo "Installing project dependencies with Poetry..."
poetry install

# Additional setup steps can go here
echo "Post-creation setup complete."

# Install project dependencies
if [ -f "pyproject.toml" ]; then
  echo "Installing project dependencies with Poetry..."
  poetry install
fi

# Set up Azure environment with improved connectivity and authentication handling
echo "Initializing Azure environment..."
python "$(dirname "$0")/azure_init.py"

# Set up Azure CLI workspace defaults if now authenticated
if az account show > /dev/null 2>&1; then
  echo "Azure CLI is authenticated. Setting up workspace defaults..."
  
  # Get account info
  SUBSCRIPTION_NAME=$(az account show --query name -o tsv 2>/dev/null || echo "Unknown")
  SUBSCRIPTION_ID=$(az account show --query id -o tsv 2>/dev/null || echo "Unknown")
  
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
  echo "No dependencies to install or update"
  echo "Azure CLI is not authenticated. Network connectivity issues may prevent authentication."
  echo "To authenticate manually when network is available, run 'az login'"
  echo "For more information, see docs/Azure_Setup.md"
fi