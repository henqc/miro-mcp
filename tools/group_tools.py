from typing import Any, Dict
from miro_client import MiroClient
from tool_registry import register_tool

register_tool(
    'group_shapes',
    'Group multiple shapes together on a board',
    {
        'board_id': {
            'type': 'string',
            'description': 'The ID of the board'
        },
        'item_ids': {
            'type': 'array',
            'items': {
                'type': 'string'
            },
            'description': 'List of item IDs to group together'
        }
    }
)

register_tool(
    'ungroup_shapes',
    'Ungroup shapes by removing them from a group/frame',
    {
        'board_id': {
            'type': 'string',
            'description': 'The ID of the board'
        },
        'group_id': {
            'type': 'string',
            'description': 'The ID of the group/frame to ungroup'
        }
    }
)


def handle_tool_call(tool_name: str, arguments: Dict[str, Any], miro_client: MiroClient) -> Dict[str, Any]:
    # Route group tool calls to appropriate handler
    if tool_name == 'group_shapes':
        board_id = arguments.get('board_id')
        item_ids = arguments.get('item_ids')
        
        if not board_id:
            return {'error': 'board_id parameter is required'}
        if not item_ids or not isinstance(item_ids, list) or len(item_ids) < 2:
            return {'error': 'item_ids must be a list with at least 2 item IDs'}
        
        try:
            result = miro_client.group_shapes(board_id, item_ids)
            return {
                'success': True,
                'group': result,
                'message': f'Successfully grouped {len(item_ids)} shapes'
            }
        except Exception as e:
            return {'error': str(e)}
    
    elif tool_name == 'ungroup_shapes':
        board_id = arguments.get('board_id')
        group_id = arguments.get('group_id')
        
        if not board_id or not group_id:
            return {'error': 'board_id and group_id are required'}
        
        try:
            result = miro_client.ungroup_shapes(board_id, group_id)
            return {
                'success': True,
                'message': result.get('message', 'Shapes ungrouped successfully')
            }
        except Exception as e:
            return {'error': str(e)}
    
    else:
        return {'error': f'Unknown group tool: {tool_name}'}
