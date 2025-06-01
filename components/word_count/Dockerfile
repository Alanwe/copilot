# Unified Azure Components Foundry Dockerfile
# Single container image that can be deployed to multiple Azure services
FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy entire project
COPY . .

# Create directory structure needed for various adapters
RUN mkdir -p /home/site/wwwroot

# Set environment variables
ENV PYTHONPATH=/app
ENV PORT=8000
ENV HANDLER=components.word_count.src.component:predict

# Default to the FastAPI/REST adapter
EXPOSE 8000
CMD ["uvicorn", "runtime.rest_adapter:app", "--host", "0.0.0.0", "--port", "8000"]
