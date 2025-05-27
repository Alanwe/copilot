"""
Service adaptors for Azure Components Foundry.
This module provides adaptors for running components in different Azure services.
"""

import json
import logging
from typing import Dict, Any


class AzureMLComponentAdaptor:
    """Adaptor for Azure ML Components/Pipelines"""
    
    @staticmethod
    def init():
        """Initialize the Azure ML component environment"""
        # Setup Azure ML specific environment
        logging.info("Initializing AzureML component environment")
        
    @staticmethod
    def run(component_instance, args):
        """
        Run the component in Azure ML context
        
        Args:
            component_instance: Instance of a BaseComponent
            args: Arguments from Azure ML component call
            
        Returns:
            Properly formatted Azure ML outputs
        """
        # Convert Azure ML inputs to component format
        logging.info("Processing AzureML component inputs")
        inputs = {k: v.read() for k, v in args.items()}
        
        # Run the component
        logging.info("Running component")
        outputs = component_instance.run(inputs)
        
        # Convert outputs to Azure ML format
        logging.info("Processing AzureML component outputs")
        return outputs


class AzureFunctionAdaptor:
    """Adaptor for Azure Functions"""
    
    @staticmethod
    def init():
        """Initialize the Azure Function environment"""
        # Setup Azure Function specific environment
        logging.info("Initializing Azure Function environment")
    
    @staticmethod
    def run(component_instance, req):
        """
        Run the component in Azure Function context
        
        Args:
            component_instance: Instance of a BaseComponent
            req: HTTP request object
            
        Returns:
            HTTP response
        """
        import azure.functions as func
        
        # Convert HTTP request to component inputs
        logging.info("Processing HTTP request")
        try:
            req_body = req.get_json()
        except ValueError:
            req_body = {}
            logging.warning("Request body contains invalid JSON")
            
        # Run the component
        logging.info("Running component")
        try:
            outputs = component_instance.run(req_body)
            
            # Return as HTTP response
            return func.HttpResponse(
                json.dumps(outputs),
                status_code=200,
                mimetype="application/json"
            )
        except Exception as e:
            logging.error(f"Error running component: {str(e)}")
            return func.HttpResponse(
                json.dumps({"error": str(e)}),
                status_code=500,
                mimetype="application/json"
            )


class AzureBatchAdaptor:
    """Adaptor for Azure Batch inference"""
    
    @staticmethod
    def init():
        """Initialize the Azure Batch environment"""
        logging.info("Initializing Azure Batch environment")
        
    @staticmethod
    def run(component_instance, batch_data):
        """
        Run the component in Azure Batch context
        
        Args:
            component_instance: Instance of a BaseComponent
            batch_data: Batch data to process
            
        Returns:
            Processed batch results
        """
        # Prepare batch inputs
        logging.info("Processing batch inputs")
        inputs = {"batch": batch_data}
        
        # Run the component
        logging.info("Running component in batch mode")
        return component_instance.run(inputs)


class AzureEndpointAdaptor:
    """Adaptor for Azure ML Endpoints"""
    
    @staticmethod
    def init():
        """Initialize the Azure ML Endpoint environment"""
        logging.info("Initializing Azure ML Endpoint environment")
        
    @staticmethod
    def run(component_instance, request_data):
        """
        Run the component in Azure ML Endpoint context
        
        Args:
            component_instance: Instance of a BaseComponent
            request_data: Request data
            
        Returns:
            Response for the endpoint
        """
        # Convert request to component inputs
        logging.info("Processing endpoint request")
        
        # Run the component
        logging.info("Running component")
        try:
            return component_instance.run(request_data)
        except Exception as e:
            logging.error(f"Error in endpoint execution: {str(e)}")
            return {"error": str(e)}


class RESTMCPAdaptor:
    """Adaptor for REST/OpenAI/Swagger MCP"""
    
    @staticmethod
    def init():
        """Initialize the REST/OpenAI/Swagger MCP environment"""
        logging.info("Initializing REST/OpenAI/Swagger MCP environment")
        
    @staticmethod
    def run(component_instance, request_data):
        """
        Run the component in REST/OpenAI/Swagger MCP context
        
        Args:
            component_instance: Instance of a BaseComponent
            request_data: Request data from API call
            
        Returns:
            Response for the API
        """
        # Convert REST API request to component inputs
        logging.info("Processing REST/OpenAI/Swagger request")
        
        # Run the component
        logging.info("Running component")
        try:
            result = component_instance.run(request_data)
            return result
        except Exception as e:
            logging.error(f"Error in REST/OpenAI/Swagger execution: {str(e)}")
            return {"error": str(e), "status_code": 500}