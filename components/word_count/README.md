# Word Count Component

A simple component that counts words in text inputs using the unified Azure Components Foundry architecture.

## Features

- Counts total words in the provided text
- Measures total character count
- Calculates average word length
- Generates distribution of word lengths

## Usage

The component accepts inputs in the following formats:

### Single text input as a string
```python
result = predict("Hello world")
```

### Single input as a dictionary with "text" key
```python
result = predict({"text": "Hello world"})
```

### Batch input as a list of dictionaries
```python
batch_result = predict([
    {"text": "First input"},
    {"text": "Second longer input"}
])
```

## Output Format

The component returns a dictionary (or list of dictionaries for batch processing) with:

```json
{
    "text": "original text",
    "word_count": 5,
    "character_count": 25,
    "average_word_length": 4.6,
    "length_distribution": {"1": 1, "4": 2, "5": 1, "8": 1}
}
```

## Deployment

This component can be deployed to:
- Azure Machine Learning (online/batch)
- Azure Functions
- Azure Container Apps
- Model Context Protocol (MCP)

via the unified deployment orchestrator.
