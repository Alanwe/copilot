#!/bin/bash
# Post container creation script
# Runs after the container is created to initialize the environment

echo "Running post-creation setup tasks..."

# Run Azure initialization script
echo "Checking Azure environment..."
python "$(dirname "$0")/azure_init.py"

echo "Initialization complete!"
