'''
Instrumented version of rest_adapter.py for coverage testing.
'''
import sys
import os
import json
import logging
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

# Create measurement file
with open(os.path.join(os.path.dirname(__file__), 'coverage_lines.txt'), 'w') as f:
    f.write('Module loaded\n')

# Track executed lines
executed_lines = set()
def track(line):
    executed_lines.add(line)
    with open(os.path.join(os.path.dirname(__file__), 'coverage_lines.txt'), 'a') as f:
        f.write(f"Line {line}\n")
    return True

# Original content below
"""
Container Apps / REST API adapter for the unified runtime system.
"""
import json
import logging
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from runtime.dispatcher import predict, health_check

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Azure Components Foundry",
    description="Unified runtime for Azure components",
    version="1.0.0"
)


class ContainerAppAdapter:
    """Adapter for Container Apps and general REST API deployment."""
    
    @staticmethod
    def init():
        """Initialize Container Apps environment."""
        logger.info("Initializing Container Apps adapter")


@app.get("/health")
async def health():
    """Health check endpoint."""
    return health_check()


@app.post("/predict")
async def predict_endpoint(request: Request):
    """
    Main prediction endpoint.
    
    Args:
        request: HTTP request with JSON payload
        
    Returns:
        JSON response with prediction results
    """
    try:
        # Parse request body
        payload = await request.json()
        
        # Process through dispatcher
        result = predict(payload)
        
        return JSONResponse(content=result)
        
    except json.JSONDecodeError:
        logger.error("Invalid JSON in request body")
        raise HTTPException(status_code=400, detail="Invalid JSON in request body")
    except Exception as e:
        logger.error(f"Error in prediction: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/batch")
async def batch_predict_endpoint(request: Request):
    """
    Batch prediction endpoint.
    
    Args:
        request: HTTP request with JSON array payload
        
    Returns:
        JSON response with batch prediction results
    """
    try:
        # Parse request body (should be a list)
        payload = await request.json()
        
        if not isinstance(payload, list):
            raise HTTPException(status_code=400, detail="Batch endpoint requires array input")
        
        # Process through dispatcher
        result = predict(payload)
        
        return JSONResponse(content=result)
        
    except json.JSONDecodeError:
        logger.error("Invalid JSON in request body")
        raise HTTPException(status_code=400, detail="Invalid JSON in request body")
    except Exception as e:
        logger.error(f"Error in batch prediction: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Initialize adapter on startup
ContainerAppAdapter.init()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
