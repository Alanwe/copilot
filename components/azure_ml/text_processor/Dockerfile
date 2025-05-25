FROM python:3.10-slim

WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy component code
COPY src/ ./src/

# Set Python path
ENV PYTHONPATH=/app

# Default command
CMD ["python", "src/run.py"]