"""Tool Execution with parallel execution support"""

import asyncio
from typing import Any, Dict, List

import json

async def _execute_single_tool(
    call:Any,
    tool_dict: Dict[str,Any]
) -> Dict[str, Any]:
    """Execute a single tool and handle errors"""
    response = {"role": "tool","tool_call_id": call.id, "name": call.function.name, "content": None}
    
    try:
        result = await tool_dict[call.function.name].execute(**json.loads(call.function.arguments))
        response["content"] = result
    except KeyError:
        response["content"] = f"Tool {call.function.name} not found"
    except Exception as e:
        response["content"] = f"Error executing tool {call.function.name}: {str(e)}"
    
    return response

async def execute_tools(
    calls: List[Any],
    tool_dict: Dict[str, Any],
    parallel: bool = True,
) -> List[Dict[str, Any]]:
    """Execute a list of tool calls in parallel or sequentially"""
    if parallel:
        return await asyncio.gather(
            *[_execute_single_tool(call, tool_dict) for call in calls]
        )
    else:
        return [
            await _execute_single_tool(call, tool_dict)
            for call in calls
        ]