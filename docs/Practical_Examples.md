# Azure Components Foundry - Practical Examples

This document provides step-by-step examples for the most common tasks in the Azure Components Foundry.

## Table of Contents
1. [Creating New Components](#1-creating-new-components)
2. [Configuring Deployment Groups](#2-configuring-deployment-groups)
3. [Connecting to Azure](#3-connecting-to-azure)
4. [Deploying Components](#4-deploying-components)
5. [Listing Azure Resources](#5-listing-azure-resources)

## 1. Creating New Components

### Example: Creating a Text Summarizer Component

```bash
# Create the component directory structure
mkdir -p components/text_summarizer/src
mkdir -p components/text_summarizer/tests
touch components/text_summarizer/__init__.py
```

#### 1.1 Create the component.py file

Create a file at `components/text_summarizer/src/component.py`:

```python
"""
Text Summarizer Component for Azure Components Foundry.
Summarizes text input using extractive summarization.
"""

import logging
from typing import Dict, Any, Union, List
import re
from collections import Counter

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def predict(input_data: Union[Dict[str, Any], List[Dict[str, Any]], str]) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
    """
    Summarize the provided text.
    
    Args:
        input_data: Can be:
            - A dictionary with a "text" key
            - A list of dictionaries for batch processing
            - A raw string
            
    Returns:
        - Dictionary with summary results, or
        - List of dictionaries for batch processing results
    """
    logger.info(f"Processing input of type {type(input_data)}")
    
    # Handle batch processing
    if isinstance(input_data, list):
        logger.info(f"Processing batch of {len(input_data)} items")
        results = []
        for item in input_data:
            text = item.get("text", "") if isinstance(item, dict) else str(item)
            results.append(summarize_text(text))
        return results
    
    # Handle single item (dict or string)
    elif isinstance(input_data, dict):
        text = input_data.get("text", "")
        return summarize_text(text)
    
    # Handle raw string input
    else:
        text = str(input_data)
        return summarize_text(text)
    
def summarize_text(text: str) -> Dict[str, Any]:
    """Summarize a single text input using extractive summarization."""
    if not text.strip():
        return {"summary": "", "original_length": 0, "summary_length": 0}
    
    # Split text into sentences
    sentences = re.split(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?)\s', text)
    
    # Score sentences based on word frequency
    word_frequencies = Counter()
    for sentence in sentences:
        words = re.findall(r'\w+', sentence.lower())
        word_frequencies.update(words)
    
    # Calculate sentence scores
    sentence_scores = {}
    for i, sentence in enumerate(sentences):
        words = re.findall(r'\w+', sentence.lower())
        score = sum(word_frequencies[word] for word in words) / max(1, len(words))
        sentence_scores[i] = score
    
    # Select top 30% of sentences
    num_sentences = max(1, len(sentences) // 3)
    top_sentences = sorted(sentence_scores.items(), key=lambda x: x[1], reverse=True)[:num_sentences]
    top_indices = sorted([idx for idx, _ in top_sentences])
    
    # Combine top sentences in original order
    summary = ' '.join(sentences[idx] for idx in top_indices)
    
    return {
        "summary": summary,
        "original_length": len(text),
        "summary_length": len(summary),
        "compression_ratio": round(len(summary) / max(1, len(text)), 2)
    }
```

#### 1.2 Create the requirements.txt file

Create a file at `components/text_summarizer/requirements.txt`:

```
# No additional requirements for this component
```

#### 1.3 Create a simple test script

Create a file at `components/text_summarizer/simple_test.py`:

```python
"""
Simple test script for the Text Summarizer component.
"""

import sys
from pathlib import Path

# Add the src directory to path
sys.path.append(str(Path(__file__).parent / "src"))

from component import predict

# Test text
test_text = """
Artificial intelligence (AI) is intelligence demonstrated by machines, as opposed to natural intelligence displayed by animals including humans. 
AI research has been defined as the field of study of intelligent agents, which refers to any system that perceives its environment and takes actions that maximize its chance of achieving its goals.
The term "artificial intelligence" had previously been used to describe machines that mimic and display "human" cognitive skills that are associated with the human mind, such as "learning" and "problem-solving". 
This definition has since been rejected by major AI researchers who now describe AI in terms of rationality and acting rationally, which does not limit how intelligence can be articulated.
AI applications include advanced web search engines, recommendation systems, understanding human speech, self-driving cars, automated decision-making and competing at the highest level in strategic game systems.
As machines become increasingly capable, tasks considered to require "intelligence" are often removed from the definition of AI, a phenomenon known as the AI effect. For instance, optical character recognition is frequently excluded from things considered to be AI, having become a routine technology.
"""

# Test with a single item
result = predict({"text": test_text})
print(f"Original length: {result['original_length']} characters")
print(f"Summary length: {result['summary_length']} characters")
print(f"Compression ratio: {result['compression_ratio']}")
print(f"Summary: {result['summary']}")

# Test with batch input
batch_result = predict([
    {"text": "This is the first test sentence. It contains important information."},
    {"text": "This is the second test. Not as important as the first one. Just some filler."}
])

print("\nBatch results:")
for i, res in enumerate(batch_result):
    print(f"Item {i+1}: {res['summary']}")
```

#### 1.4 Create a README.md file

Create a file at `components/text_summarizer/README.md`:

```markdown
# Text Summarizer Component

This component provides extractive text summarization capabilities for the Azure Components Foundry.

## Input Schema

The component accepts the following inputs:

- **Single input**: JSON object with a `text` key containing the text to summarize
- **Batch input**: List of JSON objects, each with a `text` key
- **Raw string input**: Plain text to summarize

Example input:
```json
{
    "text": "This is a long text that needs to be summarized. It contains multiple sentences with different information. The summary should extract the most important parts."
}
```

## Output Schema

The component returns a JSON object with:

- `summary`: The summarized text
- `original_length`: Length of the original text in characters
- `summary_length`: Length of the summary in characters
- `compression_ratio`: Ratio of summary length to original length

Example output:
```json
{
    "summary": "This is a long text that needs to be summarized.",
    "original_length": 130,
    "summary_length": 45,
    "compression_ratio": 0.35
}
```

## Configuration Options

No additional configuration options are required.

## Dependencies

This component uses only Python standard libraries.

## Example Usage

```python
from runtime.dispatcher import predict

result = predict({"text": "Your long text here..."})
print(f"Summary: {result['summary']}")
```
```

#### 1.5 Create a Dockerfile

Create a file at `components/text_summarizer/Dockerfile`:

```dockerfile
# Use the base image from the Azure Components Foundry
FROM base-runtime:latest

# Set the component handler
ENV HANDLER=components.text_summarizer.src.component:predict

# Copy the component code
COPY . /app/components/text_summarizer/

# No additional dependencies to install for this component

# The entrypoint is inherited from the base image
```

#### 1.6 Create a defaults.yaml file

Create a file at `components/text_summarizer/defaults.yaml`:

```yaml
# Default configuration for text_summarizer component
name: text_summarizer
version: 0.1.0
description: "Extractive text summarization component"
tags:
  - nlp
  - summarization
  - text-processing

# Resource requirements
resources:
  cpu: 1
  memory: 1Gi

# Default container configuration
container:
  image: ${acr}/azure-components-foundry:${tag}
  env:
    - name: HANDLER
      value: components.text_summarizer.src.component:predict
```

## 2. Configuring Deployment Groups

### Example: Adding New Deployment Groups

Edit the `/deploy/manifest.yaml` file to add new deployment groups:

```yaml
# Azure Components Foundry Deployment Manifest
# Single source of truth for all component deployments

# Container registry configuration
acr: mycompany.azurecr.io
imageName: azure-components-foundry
imageTag: latest

# Global defaults (can be overridden per group/deployment)
defaults:
  instance_type: Standard_DS3_v2
  instance_count: 1
  request_timeout_ms: 60000
  max_concurrent_requests: 10
  target_port: 8000
  min_replicas: 0
  max_replicas: 10

# Deployment groups - organize by environment/region
groups:
  # Development environment
  dev-eastus:
    subscription: "sub-dev-12345678-1234-1234-1234-123456789012"
    resourceGroup: "rg-components-dev"
    region: "eastus"
    deployments:
      - component: text_summarizer
        services: [containerapp]
        overrides:
          min_replicas: 1
          max_replicas: 3
      
      - component: word_count
        services: [aml_online, function]
        overrides:
          instance_type: Standard_DS2_v2
          instance_count: 1

  # Testing environment  
  test-westus:
    subscription: "sub-test-12345678-1234-1234-1234-123456789012"
    resourceGroup: "rg-components-test"
    region: "westus"
    deployments:
      - component: text_summarizer
        services: [aml_online, containerapp]
        overrides:
          instance_type: Standard_DS3_v2
          instance_count: 2
      
      - component: word_count
        services: [aml_batch]
        
  # Production environment
  prod-eastus:
    subscription: "sub-prod-12345678-1234-1234-1234-123456789012"
    resourceGroup: "rg-components-prod"
    region: "eastus"
    deployments:
      - component: text_summarizer
        services: [aml_online, containerapp]
        overrides:
          instance_type: Standard_DS4_v2
          instance_count: 3
          min_replicas: 2
          max_replicas: 10
          request_timeout_ms: 30000
```

### Example: Configure Resource Overrides

To specify custom resource requirements for different environments:

```yaml
deployments:
  - component: text_summarizer
    services: [aml_online]
    overrides:
      # Override compute resource settings
      instance_type: Standard_DS4_v2
      instance_count: 2
      
      # Override scaling settings
      min_replicas: 1
      max_replicas: 5
      
      # Override performance settings
      request_timeout_ms: 30000
      max_concurrent_requests: 20
      
      # Override container settings
      container_port: 8080
      env:
        - name: DEBUG_LEVEL
          value: "INFO"
        - name: BATCH_SIZE
          value: "32"
```

## 3. Connecting to Azure

### Example: Setting up Azure Authentication

#### 3.1 Login with Azure CLI

```bash
# Interactive login
az login

# Or login with a device code (useful for remote terminals)
az login --use-device-code

# Verify the current account
az account show
```

#### 3.2 Create a Service Principal for CI/CD

```bash
# Create a service principal with contributor access to a resource group
az ad sp create-for-rbac \
  --name "components-foundry-automation" \
  --role contributor \
  --scopes /subscriptions/your-subscription-id/resourceGroups/your-resource-group \
  --sdk-auth

# The output JSON contains the credentials needed for GitHub Actions
```

#### 3.3 Set up Azure Resources

```bash
# Create a resource group
az group create --name rg-components-dev --location eastus

# Create an Azure Container Registry
az acr create \
  --resource-group rg-components-dev \
  --name companycomponentsacr \
  --sku Standard \
  --admin-enabled true

# Create an Azure Key Vault for secrets
az keyvault create \
  --resource-group rg-components-dev \
  --name components-kv \
  --location eastus

# Create an Azure ML workspace
az ml workspace create \
  --resource-group rg-components-dev \
  --name components-ml-workspace

# Create a Container Apps environment
az containerapp env create \
  --resource-group rg-components-dev \
  --name components-env \
  --location eastus
```

#### 3.4 Using the Azure Setup Script

For a more streamlined setup, use the provided scripts:

```bash
# Run the Azure setup script
python admin/azure_setup.py setup \
  --subscription "your-subscription-id" \
  --resource-group "rg-components-dev" \
  --location "eastus" \
  --create-acr \
  --create-keyvault

# Check Azure connectivity
python admin/check_azure_connectivity.py
```

## 4. Deploying Components

### Example: Building and Deploying Components

#### 4.1 Build and Push Container Images

```bash
# Build and push all components to ACR
python admin/deploy_components.py build \
  --acr companycomponentsacr.azurecr.io \
  --tag latest

# Build a specific component
python admin/deploy_components.py build \
  --component text_summarizer \
  --acr companycomponentsacr.azurecr.io \
  --tag v1.0.0
```

#### 4.2 Deploy to Multiple Services

```bash
# Deploy all components in a group
python admin/deploy_components.py deploy \
  --group dev-eastus

# Deploy a specific component to all services
python admin/deploy_components.py deploy \
  --group dev-eastus \
  --component text_summarizer

# Deploy a component to a specific service
python admin/deploy_components.py deploy \
  --group dev-eastus \
  --component text_summarizer \
  --service aml_online
```

#### 4.3 Using Deployment Templates

The deployment process automatically uses the templates in `/deploy/templates/` to create appropriate resources for each service type.

For example, to deploy to Azure ML Online:

```bash
python admin/deploy_components.py deploy \
  --group dev-eastus \
  --component text_summarizer \
  --service aml_online \
  --template deploy/templates/custom-aml-online.yml
```

## 5. Listing Azure Resources

### Example: Discovering Deployed Components

#### 5.1 List All Resources in a Resource Group

```bash
# List all resources created by Components Foundry
python admin/discover_components.py list-resources \
  --subscription "your-subscription-id" \
  --resource-group "rg-components-dev"
```

This outputs:

```
Discovered Resources in rg-components-dev:
+----------------------+------------------+------------+--------------------------+------------+
| Component            | Service Type     | Location   | Endpoint                 | Status     |
+----------------------+------------------+------------+--------------------------+------------+
| text_summarizer      | Container App    | eastus     | https://text-sum...      | Running    |
| word_count           | AML Online       | eastus     | https://word-count...    | Running    |
| word_count           | Function App     | eastus     | https://word-count...    | Running    |
+----------------------+------------------+------------+--------------------------+------------+
```

#### 5.2 Find Resources by Component Name

```bash
# Find all resources for a specific component
python admin/discover_components.py find-component --name "text_summarizer"
```

This outputs:

```
Resources for component 'text_summarizer':
+------------------+------------+--------------------------+------------+------------------+
| Service Type     | Location   | Endpoint                 | Status     | Resource Group   |
+------------------+------------+--------------------------+------------+------------------+
| Container App    | eastus     | https://text-sum...      | Running    | rg-components-dev|
| AML Online       | westus     | https://text-sum...      | Running    | rg-components-test|
| AML Online       | eastus     | https://text-sum...      | Running    | rg-components-prod|
| Container App    | eastus     | https://text-sum...      | Running    | rg-components-prod|
+------------------+------------+--------------------------+------------+------------------+
```

#### 5.3 List Resources Using Azure CLI

```bash
# List all resources in a resource group
az resource list \
  --resource-group rg-components-dev \
  --output table

# Filter resources by tag
az resource list \
  --tag component=text_summarizer \
  --output table

# Get detailed information about a specific resource
az containerapp show \
  --name text-summarizer \
  --resource-group rg-components-dev
```
