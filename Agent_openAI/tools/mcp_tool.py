"""Tools that interact with the MCP server"""

from typing import Any, Dict, List
from tools.base import Tool

class MCPTool(Tool):
    def __init__(self, name:str, description:str, input_schema:Dict[str, Any], connection: "MCPConnection"):
        super().__init__(name, description, input_schema)
        self.connection = connection

    async def execute(self, **kwargs: Any) -> Any:
        """Execute the tool with the given arguments"""
        try:
            result = await self.connection.call_tool(self.name, arguments=kwargs)
            
            if hasattr(result, "content") and result.content:
                for item in result.content:
                    if getattr(item, "type", None) == "text":
                        return item.text
            
            return "No text content found in the tool response"
        except Exception as e:
            return f"Error executing tool{self.name}: {str(e)}"

    async def list_tools(self, **kwargs: Any) -> List[str]:
        """List all tools available on the MCP server
        Mainly for providing the list of tools to the agent
        """
        return await self.connection.list_tools()
    
    async def call_tool(self, name:str, arguments:Dict[str, Any]) -> Any:
        return await self.connection.call_tool(name, arguments=arguments)
