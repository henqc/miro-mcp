from typing import Any, Dict
from miro_client import MiroClient
from tool_registry import register_tool

register_tool(
    'get_board',
    'Get information about a Miro board including metadata, name, description, and settings',
    {
        'board_id': {
            'type': 'string',
            'description': 'The ID of the board'
        }
    }
)


def handle_tool_call(tool_name: str, arguments: Dict[str, Any], miro_client: MiroClient) -> Dict[str, Any]:
    # Route board tool calls to appropriate handler
    if tool_name == 'get_board':
        board_id = arguments.get('board_id')
        
        if not board_id:
            return {'error': 'board_id is required'}
        
        try:
            result = miro_client.get_board(board_id)
            return {
                'success': True,
                'board': result
            }
        except Exception as e:
            return {'error': str(e)}
    
    else:
        return {'error': f'Unknown board tool: {tool_name}'}

