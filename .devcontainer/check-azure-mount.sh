#!/bin/bash

echo "Checking Azure directory mount..."

# Check if the .azure directory is mounted
if [ -d "/home/vscode/.azure" ]; then
    echo "✅ Azure directory is mounted at /home/vscode/.azure"
    
    # Check if there are any Azure config files
    if [ -f "/home/vscode/.azure/config" ]; then
        echo "✅ Azure config file found"
    else
        echo "⚠️  Azure config file not found - you may need to run 'az login' first"
    fi
    
    # List contents of .azure directory
    echo ""
    echo "Contents of /home/vscode/.azure:"
    ls -la /home/vscode/.azure/
    
    # Check Azure CLI authentication status
    echo ""
    echo "Checking Azure CLI authentication status..."
    if az account show > /dev/null 2>&1; then
        echo "✅ Azure CLI is authenticated"
        az account show --output table
    else
        echo "❌ Azure CLI is not authenticated"
        echo "Run 'az login' to authenticate"
    fi
    
else
    echo "❌ Azure directory is NOT mounted"
    echo "Expected location: /home/vscode/.azure"
    echo ""
    echo "Troubleshooting steps:"
    echo "1. Check that c:\\users\\alanwe\\.azure exists on your Windows host"
    echo "2. Verify the mount configuration in devcontainer.json"
    echo "3. Try rebuilding the dev container"
fi
