#!/bin/bash
# Azure directory mounting guide

echo -e "\n=== Azure Directory Mounting Guide ===\n"
echo "This guide explains how to mount your host machine's Azure configuration directory"
echo "into the devcontainer for sharing Azure CLI authentication."
echo 

echo -e "1. Open .devcontainer/devcontainer.env in your editor\n"

echo "2. Add or update the HOST_AZURE_DIR variable with your host's .azure directory path:"
echo "   For example:"
echo "   - Windows WSL: HOST_AZURE_DIR=/mnt/c/Users/yourusername/.azure"
echo "   - Windows Docker: HOST_AZURE_DIR=C:/Users/yourusername/.azure"
echo "   - macOS: HOST_AZURE_DIR=/Users/yourusername/.azure"
echo "   - Linux: HOST_AZURE_DIR=/home/yourusername/.azure"
echo 

echo "3. Rebuild the devcontainer"
echo "   - From VS Code Command Palette (Ctrl+Shift+P or Cmd+Shift+P)"
echo "   - Select 'Remote-Containers: Rebuild Container'"
echo 

echo "For more detailed instructions, see:"
echo "docs/Azure_Directory_Mounting.md"
echo
