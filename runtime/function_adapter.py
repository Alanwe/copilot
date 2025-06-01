"""
Azure Functions adapter for the unified runtime system.
"""
import json
import logging
import azure.functions as func
from runtime.dispatcher import predict

logger = logging.getLogger(__name__)


class AzureFunctionAdapter:
    """Adapter for Azure Functions."""
    
    @staticmethod
    def init():
        """Initialize Azure Functions environment."""
        logger.info("Initializing Azure Functions adapter")
        
    @staticmethod
    def main(req: func.HttpRequest) -> func.HttpResponse:
        """
        Main function entry point for Azure Functions.
        
        Args:
            req: HTTP request object
            
        Returns:
            HTTP response with processed results
        """
        logger.info("Processing Azure Functions request")
        
        try:
            # Parse request body
            try:
                req_body = req.get_json()
                if req_body is None:
                    req_body = {}
            except ValueError:
                logger.warning("Invalid JSON in request body, using empty dict")
                req_body = {}
            
            # Process through dispatcher
            result = predict(req_body)
            
            # Return JSON response
            return func.HttpResponse(
                json.dumps(result, default=str),
                status_code=200,
                mimetype="application/json"
            )
            
        except Exception as e:
            logger.error(f"Error in Azure Functions adapter: {str(e)}")
            return func.HttpResponse(
                json.dumps({"error": str(e), "status": "failed"}),
                status_code=500,
                mimetype="application/json"
            )


# Main function for Azure Functions
def main(req: func.HttpRequest) -> func.HttpResponse:
    """Entry point for Azure Functions."""
    return AzureFunctionAdapter.main(req)
