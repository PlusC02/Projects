"""Connection handling for MCP server"""

from abc import ABC, abstractmethod
from contextlib import AsyncExitStack
from typing import Any, Dict, List

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.client.sse import sse_client
import sys

from tools.mcp_tool import MCPTool

class MCPConnection(ABC):
    """Base class for MCP connections"""
    def __init__(self):
        """
        Initialize the MCP connection
        
        Session: MCP client session
        _rw_ctx: Context manager for reading and writing to the MCP server
        _session_ctx: Context manager for the MCP client session
        """
        self.session = None
        self._rw_ctx = None
        self._session_ctx = None
        
    @abstractmethod
    async def _create_rw_context(self):
        """Create a context manager for reading and writing to the MCP server based on connection type"""
        
    async def __aenter__(self):
        """Initialize the MCP connection with context managers"""
        self._rw_ctx = await self._create_rw_context()
        read, write = await self._rw_ctx.__aenter__()
        self._session_ctx = ClientSession(read, write)
        self.session = self._session_ctx.__aenter__()
        await self.session.initialize()
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        """Clean up the MCP connection"""
        try:
            if self._session_ctx:
                await self._session_ctx.__aexit__(exc_type, exc_value, traceback)
            if self._rw_ctx:
                await self._rw_ctx.__aexit__(exc_type, exc_value, traceback)
        except Exception as e:
            print(f"Error cleaning up MCP connection: {e}")
            
    async def list_tools(self) -> List[str]:
        """List all tools available on the MCP server"""
        return await self.session.list_tools()
    
    async def call_tool(self, name:str, arguments:Dict[str, Any]) -> Any:
        """Call a tool on the MCP server"""
        return await self.session.call_tool(name, arguments=arguments)
    
class MCPConnectionStdio(MCPConnection):
    """Connection for MCP server over stdio"""
    def __init__(self, command:str, args:List[str] = [], env:Dict[str, str] = None):
        super().__init__()
        self.command = command
        self.args = args
        self.env = env

    async def _create_rw_context(self):
        """Create a context manager for reading and writing to the MCP server over stdio"""
        return stdio_client(
            StdioServerParameters(
                command=self.command,
                args=self.args,
                env=self.env
            )
        )

class MCPConnectionSSE(MCPConnection):
    """Connection for MCP server over SSE"""
    def __init__(self, url:str, headers:Dict[str, str] = None):
        super().__init__()
        self.url = url
        self.headers = headers or {}

    async def _create_rw_context(self):
        """Create a context manager for reading and writing to the MCP server over SSE"""
        return sse_client(self.url, headers=self.headers)

def create_mcp_connection(config: Dict[str, Any]) -> MCPConnection:
    # Factory function to create an MCP connection based on the configuration
    """Create an MCP connection based on the configuration"""
    if config.get("type") == "stdio":
        if not config.get("command"):
            raise ValueError("Command is required for stdio connection")
        
        return MCPConnectionStdio(
            command=config["command"],
            args=config.get("args", []),
            env=config.get("env", {})
        )
        
    elif config.get("type") == "sse":
        if not config.get("url"):
            raise ValueError("URL is required for SSE connection")
        
        return MCPConnectionSSE(
            url=config["url"],
            headers=config.get("headers", {})
        )
        
    raise ValueError(f"Invalid connection type: {config.get('type')}")

async def setup_mcp_connections(
    mcp_servers: List[Dict[str, Any]] | None,
    stack: AsyncExitStack,
) -> List[MCPTool]:
    if not mcp_servers:
        return []
    
    mcp_tools = []
    
    for config in mcp_servers:
        try:
            connection = create_mcp_connection(config)
            # Enter the context of the MCP connection
            await stack.enter_async_context(connection)
            
            # Retrieve the list of tools from the MCP server (According to MCP format)
            tools = await connection.list_tools()
            for tool in tools:
                mcp_tools.append(MCPTool(
                    name = tool.name,
                    description = tool.description or f"MCP tool {tool.name}",
                    input_schema = tool.input_schema,
                    connection = connection
                ))
        except Exception as e:
            print(f"Error setting up MCP connection: {e}")

    print(f"loaded {len(mcp_tools)} MCP tools from {len(mcp_servers)} servers")        
    return mcp_tools


