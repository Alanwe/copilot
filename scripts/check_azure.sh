#!/bin/bash
# Azure connection helper script
# Run this script to check Azure connectivity and attempt authentication

echo -e "\n=== Azure Connectivity and Authentication Helper ===\n"

echo "Checking Azure connectivity..."
python "$(dirname "$0")/../admin/check_azure_connectivity.py"

status=$?

if [ $status -eq 0 ]; then
    echo -e "\nSuccessfully connected and authenticated with Azure."
    echo "You can now use Azure CLI commands."
else
    echo -e "\n🔄 If you continue having issues, you can try the following:"
    echo "1. Check network connectivity and proxy settings"
    echo "2. Update credentials in .devcontainer/devcontainer.env"
    echo "3. Run 'az login' manually when network connection is available"
    echo -e "\nFor more information, see docs/Azure_Setup.md"
fi
