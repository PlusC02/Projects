"""Tool Utlity for Executing Tools with Parallel or Sequential Execution"""
# For ReAct agent, only sequential execution is possible

import asyncio
from typing import List, Dict, Any

async def _execute_tool(tool_call: Dict[str, Any], tool_dict: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Execute tools in parallel or sequentially based on the tool_calls.
    """
    response = {
        "role" : "user",
        "content" : ""
    }

    try:
        result = await tool_dict[tool_call["name"]].execute(**tool_call["args"])
        response["content"] = result
    except KeyError:
        response["content"] = f"Tool {tool_call['name']} not found"
    except Exception as e:
        response["content"] = f"Error executing tool {tool_call['name']}: {str(e)}"
    
    return response

async def execute_tools(tool_calls: List[Dict[str, Any]], tool_dict: Dict[str, Any], parallel: bool = True) -> List[Dict[str, Any]]:
    """
    Execute tools in parallel or sequentially based on the tool_calls.
    """
    
    if parallel:
        return await asyncio.gather(*[_execute_tool(tool_call, tool_dict) for tool_call in tool_calls])
    else:
        return [await _execute_tool(tool_call, tool_dict) for tool_call in tool_calls]