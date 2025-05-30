"""
Base component implementation for Azure Components Foundry.
This module defines the core BaseComponent that all components should inherit from.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class BaseComponent(ABC):
    """
    Base component interface that all components should implement.
    This ensures consistent behavior across different deployment targets.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the component with configuration.
        
        Args:
            config: A dictionary containing component configuration
        """
        self.config = config or {}
        self.initialize()
    
    def initialize(self):
        """
        Initialize resources needed by the component.
        Override this method for resource setup that's independent of deployment target.
        """
        pass
    
    @abstractmethod
    def run(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run the component's core logic.
        
        Args:
            inputs: Input data dictionary
            
        Returns:
            Dictionary containing the output data
        """
        pass
    
    def cleanup(self):
        """
        Clean up any resources used by the component.
        Override if your component needs to release resources.
        """
        pass