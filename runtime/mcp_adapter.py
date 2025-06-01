"""
Model Context Protocol (MCP) adapter for the unified runtime system.
"""
import json
import logging
from typing import Any, Dict, List
from runtime.dispatcher import predict

logger = logging.getLogger(__name__)


class MCPAdapter:
    """Adapter for MCP action server deployment."""
    
    @staticmethod
    def init():
        """Initialize MCP environment."""
        logger.info("Initializing MCP adapter")
        
    @staticmethod
    def handle_action(action_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle MCP action requests.
        
        Args:
            action_name: Name of the action to execute
            params: Parameters for the action
            
        Returns:
            Action execution results
        """
        logger.info(f"Processing MCP action: {action_name}")
        
        try:
            # For now, all actions are routed through the predict function
            # In the future, this could be expanded to support multiple actions
            if action_name in ["predict", "process", "execute"]:
                result = predict(params)
                return {
                    "success": True,
                    "result": result,
                    "action": action_name
                }
            else:
                return {
                    "success": False,
                    "error": f"Unknown action: {action_name}",
                    "action": action_name
                }
                
        except Exception as e:
            logger.error(f"Error in MCP action {action_name}: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "action": action_name
            }
    
    @staticmethod
    def list_actions() -> List[Dict[str, Any]]:
        """
        List available MCP actions.
        
        Returns:
            List of available actions with descriptions
        """
        return [
            {
                "name": "predict",
                "description": "Execute the component's prediction function",
                "parameters": {
                    "type": "object",
                    "description": "Input data for prediction"
                }
            },
            {
                "name": "process", 
                "description": "Process data through the component",
                "parameters": {
                    "type": "object",
                    "description": "Input data for processing"
                }
            }
        ]


# MCP server functions
def handle_mcp_request(request: Dict[str, Any]) -> Dict[str, Any]:
    """
    Main MCP request handler.
    
    Args:
        request: MCP request dictionary
        
    Returns:
        MCP response dictionary
    """
    action_name = request.get("action", "predict")
    params = request.get("params", {})
    
    return MCPAdapter.handle_action(action_name, params)


def get_mcp_schema() -> Dict[str, Any]:
    """
    Get MCP schema for this component.
    
    Returns:
        MCP schema dictionary
    """
    return {
        "name": "component-server",
        "version": "1.0.0",
        "description": "Azure Components Foundry MCP Server",
        "actions": MCPAdapter.list_actions()
    }
