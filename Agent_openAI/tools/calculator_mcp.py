"""Simple calculator tool that uses the MCP server"""

import math

from mcp.server import FastMCP

mcp = FastMCP("calculator")

@mcp.tool(name="calculator")
def calculator(number1:float, number2:float, operation:str) -> str:
    """Perform basic calculator with two numbers

    Args:
        number1 (float): First number in the calculation
        number2 (float): Second number in the calculation
        operation (str): Operation to perform (+ ,- , *, /, ^, sqrt)
                Note: Only these exact symbols are supported

    Returns:
        str: Result of the calculation
    """
    
    try:
        if operation == "+":
            result = number1 + number2
        elif operation == "-":
            result = number1 - number2
        elif operation == "*":
            result = number1 * number2
        elif operation == "/":
            if number2 == 0:
                return "Error: Division by zero"
            result = number1 / number2
        elif operation == "^":
            result = number1 ** number2
        elif operation == "sqrt":
            if number1 < 0:
                return "Error: Negative number under square root"
            result = math.sqrt(number1)
        else:
            return "Error: Invalid operation"
        
        if isinstance(result, float) and result.is_integer():
            result = int(result)
        
        return f"Result: {result}"
    except Exception as e:
        return f"Error: {str(e)}"
    
if __name__ == "__main__":
    mcp.run()