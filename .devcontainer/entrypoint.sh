#!/bin/bash
set -e

# Azure CLI login using environment variables if available
if [[ -n "${AZURE_CLIENT_ID}" && -n "${AZURE_CLIENT_SECRET}" && -n "${AZURE_TENANT_ID}" ]]; then
  echo "Logging in to Azure using service principal credentials..."
  az login --service-principal \
    --username "${AZURE_CLIENT_ID}" \
    --password "${AZURE_CLIENT_SECRET}" \
    --tenant "${AZURE_TENANT_ID}" > /dev/null

  if [[ -n "${AZURE_SUBSCRIPTION_ID}" ]]; then
    echo "Setting default subscription..."
    az account set --subscription "${AZURE_SUBSCRIPTION_ID}" > /dev/null
  fi
elif [[ -n "${AZURE_CREDENTIALS}" ]]; then
  # Extract credentials from AZURE_CREDENTIALS JSON
  echo "Extracting credentials from AZURE_CREDENTIALS..."
  CLIENT_ID=$(echo "${AZURE_CREDENTIALS}" | jq -r '.clientId')
  CLIENT_SECRET=$(echo "${AZURE_CREDENTIALS}" | jq -r '.clientSecret')
  TENANT_ID=$(echo "${AZURE_CREDENTIALS}" | jq -r '.tenantId')
  SUBSCRIPTION_ID=$(echo "${AZURE_CREDENTIALS}" | jq -r '.subscriptionId')
  
  echo "Logging in to Azure using extracted service principal credentials..."
  az login --service-principal \
    --username "${CLIENT_ID}" \
    --password "${CLIENT_SECRET}" \
    --tenant "${TENANT_ID}" > /dev/null
    
  if [[ -n "${SUBSCRIPTION_ID}" ]]; then
    echo "Setting default subscription..."
    az account set --subscription "${SUBSCRIPTION_ID}" > /dev/null
  fi
fi

# Execute the provided command or default command
if [[ $# -gt 0 ]]; then
  exec "$@"
else
  exec sleep infinity
fi