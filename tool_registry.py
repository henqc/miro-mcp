from typing import Any, Dict

TOOLS: Dict[str, Dict[str, Any]] = {}


def register_tool(name: str, description: str, parameters: Dict[str, Any]):
    # Register tool with MCP server for discovery
    required = [k for k, v in parameters.items() if v.get('required', False)]
    
    TOOLS[name] = {
        'name': name,
        'description': description,
        'inputSchema': {
            'type': 'object',
            'properties': parameters,
            'required': required
        }
    }

