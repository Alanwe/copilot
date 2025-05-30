#!/bin/bash
# Azure environment configuration helper script
# This script helps users configure Azure directory mounting in the devcontainer

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="${SCRIPT_DIR}/../.devcontainer/devcontainer.env"

echo -e "\n=== Azure Directory Configuration Helper ===\n"

if [ ! -f "${ENV_FILE}" ]; then
  echo "❌ Could not find devcontainer.env file at: ${ENV_FILE}"
  exit 1
fi

# Detect OS and suggest appropriate paths
if [[ "$OSTYPE" == "darwin"* ]]; then
  # macOS
  SUGGESTED_PATH="${HOME}/.azure"
  OS_TYPE="macOS"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
  # Linux, check if WSL
  if grep -q Microsoft /proc/version 2>/dev/null; then
    # WSL
    DEFAULT_USER=$(cmd.exe /c echo %USERNAME% 2>/dev/null | tr -d '\r')
    SUGGESTED_PATH="/mnt/c/Users/${DEFAULT_USER}/.azure"
    OS_TYPE="Windows WSL"
  else
    # Regular Linux
    SUGGESTED_PATH="${HOME}/.azure"
    OS_TYPE="Linux"
  fi
elif [[ "$OSTYPE" == "msys"* ]] || [[ "$OSTYPE" == "cygwin"* ]]; then
  # Windows Git Bash or similar
  SUGGESTED_PATH="C:/Users/${USERNAME}/.azure"
  OS_TYPE="Windows"
else
  SUGGESTED_PATH="${HOME}/.azure"
  OS_TYPE="Unknown"
fi

# Check if Azure CLI is installed and if the directory exists
echo "Checking for Azure CLI configuration..."
if [ -d "${SUGGESTED_PATH}" ]; then
  echo "✅ Azure CLI configuration found at: ${SUGGESTED_PATH}"
  FILE_COUNT=$(find "${SUGGESTED_PATH}" -type f | wc -l)
  if [ "${FILE_COUNT}" -gt 0 ]; then
    echo "   Found ${FILE_COUNT} file(s) in the Azure configuration directory"
  else
    echo "⚠️ Azure directory exists but appears to be empty"
    echo "   You may need to run 'az login' on your host machine first"
  fi
else
  echo "⚠️ Azure CLI configuration directory not found at: ${SUGGESTED_PATH}"
  echo "   You may need to run 'az login' on your host machine first"
  # Create directory to prevent mount errors
  mkdir -p "${SUGGESTED_PATH}"
  echo "   Created directory: ${SUGGESTED_PATH}"
fi

echo -e "\nDetected OS: ${OS_TYPE}"
echo "Suggested path: ${SUGGESTED_PATH}"
echo ""

read -p "Would you like to update devcontainer.env with this path? (y/n) " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
  # Update the devcontainer.env file
  if grep -q "HOST_AZURE_DIR=" "${ENV_FILE}"; then
    # Replace existing line
    sed -i "s|HOST_AZURE_DIR=.*|HOST_AZURE_DIR=${SUGGESTED_PATH}|" "${ENV_FILE}"
  else
    # Add new line if not found
    echo "HOST_AZURE_DIR=${SUGGESTED_PATH}" >> "${ENV_FILE}"
  fi
  echo "✅ Updated HOST_AZURE_DIR in ${ENV_FILE}"
  echo ""
  echo "For these changes to take effect, you need to rebuild the devcontainer:"
  echo "1. From VS Code Command Palette (Ctrl+Shift+P or Cmd+Shift+P)"
  echo "2. Run 'Remote-Containers: Rebuild Container'"
else
  echo ""
  echo "You can manually update the HOST_AZURE_DIR value in ${ENV_FILE}"
fi

echo ""
echo "After rebuilding the container, run ./scripts/check_azure_mount.sh"
echo "to verify that the Azure directory is properly mounted."
echo "
