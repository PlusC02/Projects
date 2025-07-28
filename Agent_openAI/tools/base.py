"""Base tool definition for the agent framework"""

from dataclasses import dataclass
from typing import Any, Dict, List

@dataclass
class Tool:
    """Base class for all tools"""

    name: str
    description: str
    input_schema: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert tool to dictionary format for OpenAI API"""
        function = {
            "name": self.name,
            "description": self.description,
            "parameters": self.input_schema,
        }
        
        return {
            "type": "function",
            "function": function,
        }
    
    async def execute(self, **kwargs: Any) -> Any:
        """Execute the tool with the given arguments"""
        raise NotImplementedError("Subclasses must implement execute method")