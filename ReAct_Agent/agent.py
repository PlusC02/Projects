"""ReAct Agent"""

from typing import Any, Dict, List
from loguru import logger
from openai import OpenAI
from dataclasses import dataclass

from utils.history_util import MessageHistory
from utils.tool_util import execute_tools
from tools import Tool, FakeGetWeather

import asyncio
import os
import re
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY") or "Your API Key"
base_url = os.getenv("OPENAI_URL") or "Your Base URL"

# Please change model name if you are using different model
@dataclass
class ModelConfig:
    """Model Configuration"""

    model: str = "gpt-4o"
    max_tokens: int = 2048
    temperature: float = 0.7
    context_window_size: int = 10

class ReActAgent:
    """ReAct Agent instance"""

    def __init__(
        self,
        name: str,
        system: str | None = None,
        tools: List[Tool] | None = None,
        config: ModelConfig | None = None,
        client: OpenAI | None = None,
        history: MessageHistory | None = None,
        message_param: Dict[str, Any] | None = None,
    ):
        self.name = name
        self.system = system
        self.tools = tools
        self.config = config or ModelConfig()
        self.client = client or OpenAI(
            base_url=base_url,
            api_key=api_key,
        )
        self.history = history or MessageHistory(
            model=self.config.model,
            system=self.system,
            context_window_size=self.config.context_window_size,
        )
        self.message_param = message_param or {}

        if not self.system:
            self.system = f"""
            You are a helpful ReAct Agent.

            You run in a loop of Thought, Action, Observation.
            At the end of the loop, you return an Answer.
            Use Thought to describe your thought about the question you have been asked.
            Use Action to run one of the actions available to you.
            Observation will be the result of running those actions.

            Your available actions are:
            {", ".join([tool.name for tool in self.tools])}

            Example:
            Question: What is the weather in Tokyo?
            Thought: I need to use the get weather tool to get the weather in Tokyo.
            Action: get_weather(city="Tokyo")
            Observation: The weather in Tokyo is sunny.
            Answer: The weather in Tokyo is sunny.
            """.strip()

        if not self.tools:
            self.tools = [FakeGetWeather()]

        if not self.history.model:
            self.history.model = self.config.model

    def _prepare_message_params(self) -> Dict[str, Any]:
        """Prepare message parameters for the model API"""

        return {
            "model": self.config.model,
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens,
            "messages": self.history.format_for_api(),
            **self.message_param,
        }
    
    async def _agent_loop(self, user_input: str) ->str:
        """Main agent loop"""

        user_input = "Question: " + user_input.strip()
        logger.info(f"[{self.name}] Received: {user_input.strip()}")
        await self.history.add_message("user", user_input.strip(), None)

        tool_dict = {tool.name: tool for tool in self.tools}
        
        while True:
            self.history.truncate()
            params = self._prepare_message_params()

            response = await self.client.chat.completions.create(**params)
            content = response.choices[0].message.content
            usage = response.usage

            if "Action: " in content:
                logger.info(f"[{self.name}] Action: {content}")
                tool_call = self.parse_response(content)

                await self.history.add_message("assistant", content, usage)

                observation = await execute_tools([tool_call], tool_dict)
                logger.info(f"[{self.name}] Observation: {observation}")

                await self.history.add_message("user", observation, None)
            
            elif "Answer: " in content:
                logger.info(f"[{self.name}] Answer: {content}")
                await self.history.add_message("assistant", content, usage)
                return content.split("Answer: ")[1].strip()
            
            else:
                logger.warning(f"[{self.name}] Unknown response: {content}")
                raise ValueError(
                    (
                        f"[{self.name}] Error: No available action taken in Chatbot with ReAct Agent)"
                        f"Please check the response: \n{content}"
                    )
                )

    def parse_response(self, response: str) -> Dict[str, str]:
        if not (action_function_match:= re.search(r"(?<=Action: )[\w_]*", response)):
            raise ValueError("No action function found in response")
        
        function_name = action_function_match.group(0)
        pattern = r'(\w+)="([^"]*)"'
        matches = re.findall(pattern, response)
        action_args = dict(matches)
        return {
            "name": function_name,
            "args": action_args,
        }
    

    async def run_async(self, user_input: str) -> str:
        """Should extend with MCP bur simplfied for now"""
        return await self._agent_loop(user_input)

    def run(self, user_input: str) -> str:
        """Run the agent asynchronously"""
        return asyncio.run(self.run_async(user_input))

if __name__ == "__main__":
    agent = ReActAgent(
        "ReAct Agent",
        tools=[FakeGetWeather()],
    )

    response = agent.run("What is the weather in Beijing?")
    print(response)



