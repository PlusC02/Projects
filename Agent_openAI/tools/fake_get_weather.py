"""Fake tool for getting weather information"""

from tools.base import Tool

class FakeGetWeather(Tool):
    """Fake tool for getting weather information"""
    
    def __init__(self):
        super().__init__(
            name="get_weather",
            description="Get the weather information for a given city",
            input_schema={
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "The city to get the weather information for"
                    }
                },
                "required": ["city"],
            }
        )
        
    async def execute(self, city: str) -> str:
        # Usually it is the tool logic to handle
        """Execute the tool with the given arguments"""
        return f"The weather in {city} is sunny"