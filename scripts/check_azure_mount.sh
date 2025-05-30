#!/bin/bash
# Azure directory mounting helper script
# This script is used to explain the Azure directory mounting in the devcontainer.json

echo -e "\n=== Azure Directory Mounting Information ===\n"

if [ -d "/home/vscode/.azure" ]; then
  echo "✅ Azure configuration directory successfully mounted from host"
  
  # Count files to verify it's not empty
  file_count=$(find /home/vscode/.azure -type f | wc -l)
  
  if [ "$file_count" -gt 0 ]; then
    echo "✅ Azure configuration contains $file_count file(s)"
    echo "   Host Azure credentials are available in the container"
  else
    echo "⚠️ Azure configuration directory is empty"
    echo "   You may need to run 'az login' on your host machine first"
  fi
else
  echo "❌ Azure configuration directory not mounted from host"
  echo "   Check your devcontainer.json configuration"
fi

echo -e "\nHow Azure credential sharing works:\n"
echo "1. The devcontainer.json file mounts your host's .azure directory"
echo "   into the container at /home/vscode/.azure"
echo ""
echo "2. This makes your Azure CLI authentication from the host"
echo "   available inside the container without re-authenticating"
echo ""
echo "3. The mounting uses this pattern in devcontainer.json:"
echo '   "source=${localEnv:HOME}${localEnv:USERPROFILE}/.azure,target=/home/vscode/.azure,type=bind"'
echo ""
echo "4. This works across different host OS types:"
echo "   - Linux/macOS: \$HOME/.azure is used"
echo "   - Windows: \$USERPROFILE/.azure is used" 
echo ""
echo "If you're experiencing issues:"
echo "1. Ensure you've logged in to Azure on your host machine"
echo "2. Check that the devcontainer has access to your host's .azure directory"
echo "3. Rebuild the devcontainer if you've just fixed the configuration"
