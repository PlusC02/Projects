"""Fake Tool for getting weather for simplicity"""

from base import Tool

class FakeGetWeather(Tool):
    """Fake Tool for getting weather for simplicity"""

    def __init__(self):
        super().__init__(
            name="get_weather",
            description="Get the weather for a given city",
            input_schema={
                "type": "object",
                "properties": {
                    "city": {"type": "string", "description": "The city to get the weather for"},
                },
                "required": ["city"],
            }
        )

    async def execute(self, city: str) -> str:
        # Actual logic to handle but for simplicity, we are returning a fake weather
        """Execute the tool with given parameters"""
        return f"The weather in {city} is sunny"