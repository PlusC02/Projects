"""Agent Implmentation with OpenAI API, no MCP and caching Yet"""

import asyncio
import os
from dataclasses import dataclass
from contextlib import AsyncExitStack

from sys import api_version
from typing import Any, Dict, List

from httpx import stream
from openai import OpenAI

from utils.history_util import MessageHistory
from tools.base import Tool
from utils.tool_util import execute_tools
from utils.connection import setup_mcp_connections

from tools.fake_get_weather import FakeGetWeather

from loguru import logger

from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
api_version = os.getenv("OPENAI_API_VERSION")
api_base = os.getenv("OPENAI_API_BASE")

client = OpenAI(
    api_key=api_key,
    api_version=api_version,
    base_url=api_base,
)

@dataclass
class ModelConfig:
    """Model configuration for the agent"""
    
    model: str = "gpt-4o-mini"
    max_tokens: int = 4096
    temperature: float = 0.7
    context_window_tokens: int = 8192
    
class Agent:
    """Agent class for the agent framework"""
    
    def __init__(
        self,
        name: str,
        system: str,
        verbose: bool = False,
        mcp_servers: List[Dict[str, Any]] | None = None,
        tools: List[Tool] | None = None,
        config: ModelConfig | None = None,
        client: OpenAI | None = None,
        history: MessageHistory | None = None,
    ):  
        
        self.name = name
        self.system = system
        self.config = config or ModelConfig()
        self.verbose = verbose
        self.mcp_servers = mcp_servers or []
        self.tools = list(tools or [])
        self.client = client or OpenAI(
            api_key=api_key,
            api_version=api_version,
            base_url=api_base,
        )
        self.history = history or MessageHistory(
            model=self.config.model,
            system=system,
            context_window_tokens=self.config.context_window_tokens,
            client=self.client, # May not be needed
        )
        
    def _prepare_message_params(self) -> Dict[str, Any]:
        """Prepare the message parameters for the OpenAI ChatCompletion API"""
        
        messages = self.history.format_for_api()
        messages.insert(0, {
            "role": "system",
            "content": self.system,
        })
        
        result = {
            "model": self.config.model,
            "messages": messages,
            "max_tokens": self.config.max_tokens,
            "temperature": self.config.temperature,
        }
        
        if self.tools:
            result["tools"] = [tool.to_dict() for tool in self.tools]
            
        return result

    async def _agent_loop(self, user_input: str) -> List[Dict[str, Any]]:
        "Process user input and handole tool calls in a loop"
        
        logger.info(f"{self.name}: Received {user_input}")
            
        tool_dict = {tool.name: tool for tool in self.tools}
        
        await self.history.add_message("user", user_input)
        
        while True:
            self.history.truncate()
            
            params = self._prepare_message_params()
            
            response = await self.client.chat.completions.create(**params)
            
            logger.info(f"{self.name}: Response: {response.choices[0].message.content}")
            
            if response.choices[0].message.tool_calls:
                await self.history.add_message("assistant", response.choices[0].message,response.usage)
                
                tool_calls = response.choices[0].message.tool_calls
                tool_results = await execute_tools(tool_calls, tool_dict)
                
                for tool_result in tool_results:
                    await self.history.add_message("tool", tool_result)
                    
            else:
                await self.history.add_message("assistant", response.choices[0].message.content, response.usage)
                
                return response.choices[0].message.content
            
    async def run_async(self, user_input: str) -> List[Dict[str, Any]]:
        """Run the agent asynchronously with MCP tools (Not implemented yet)"""
        # Would need to extend our tool set
        tools = list(self.tools)
        async with AsyncExitStack() as stack:
            try:
                mcp_tools = await setup_mcp_connections(self.mcp_servers, stack)
                self.tools.extend(mcp_tools)
                return await self._agent_loop(user_input)
            finally:
                self.tools = tools

    async def run(self, user_input: str) -> List[Dict[str, Any]]:
        """Run the agent synchronously"""
        
        return asyncio.run(self.run_async(user_input))
    

if __name__ == "__main__":
    calculator_server_path = os.path.join(os.path.dirname(__file__), "tools", "calculator_mcp.py")
    calculator_server = {
        "type": "stdio",
        "command": "python",
        "args": [calculator_server_path],
    }
    
    print(f"Loaded MCP tools: {"Yes" if calculator_server else "No"}")
    
    agent = Agent(
        name="Two tools Agent",
        system="You are a helpful assistant",
        tools = [FakeGetWeather()],
        mcp_servers=[calculator_server],
    )
    
    result = agent.run("What is the weather in Tokyo?")
    print(f"Result: {result}")
    