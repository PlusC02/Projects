"""Base Tool Class Implementation"""

from dataclasses import dataclass
from typing import Any, Dict

@dataclass
class Tool:
    """Base Tool Class"""

    name:str
    description:str
    input_schema:Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for Model Input"""
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.input_schema
        }
    
    def execute(self, **kwargs) -> Any:
        """Execute the tool with given parameters"""
        raise NotImplementedError("Tool must implement execute method")
    
    def __str__(self) -> str:
        """String representation of the tool"""
        return f"Tool(name={self.name}, description={self.description})"
    
    def __repr__(self) -> str:
        """Representation of the tool"""
        return self.__str__()