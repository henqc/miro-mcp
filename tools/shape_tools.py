from typing import Any, Dict, Optional
from miro_client import MiroClient
from tool_registry import register_tool

register_tool(
    'create_shape',
    'Create a shape on a Miro board',
    {
        'board_id': {
            'type': 'string',
            'description': 'The ID of the board'
        },
        'shape_type': {
            'type': 'string',
            'description': 'Type of shape: rectangle, circle, triangle, star, arrow, etc.',
            'enum': ['rectangle', 'circle', 'triangle', 'star', 'arrow', 'rhombus', 'octagon', 'hexagon']
        },
        'x': {
            'type': 'number',
            'description': 'X coordinate of the shape position'
        },
        'y': {
            'type': 'number',
            'description': 'Y coordinate of the shape position'
        },
        'width': {
            'type': 'number',
            'description': 'Width of the shape'
        },
        'height': {
            'type': 'number',
            'description': 'Height of the shape'
        },
        'fillColor': {
            'type': 'string',
            'description': 'Fill color in hex format (e.g., #FF0000)',
            'required': False
        },
        'borderColor': {
            'type': 'string',
            'description': 'Border color in hex format (e.g., #000000)',
            'required': False
        },
        'borderWidth': {
            'type': 'number',
            'description': 'Border width in pixels',
            'required': False
        },
        'content': {
            'type': 'string',
            'description': 'Text content to display in the shape',
            'required': False
        }
    }
)

register_tool(
    'update_shape',
    'Update properties of an existing shape',
    {
        'board_id': {
            'type': 'string',
            'description': 'The ID of the board'
        },
        'item_id': {
            'type': 'string',
            'description': 'The ID of the shape item to update'
        },
        'x': {
            'type': 'number',
            'description': 'New X coordinate (optional)',
            'required': False
        },
        'y': {
            'type': 'number',
            'description': 'New Y coordinate (optional)',
            'required': False
        },
        'width': {
            'type': 'number',
            'description': 'New width (optional)',
            'required': False
        },
        'height': {
            'type': 'number',
            'description': 'New height (optional)',
            'required': False
        },
        'fillColor': {
            'type': 'string',
            'description': 'New fill color in hex format (optional)',
            'required': False
        },
        'borderColor': {
            'type': 'string',
            'description': 'New border color in hex format (optional)',
            'required': False
        },
        'borderWidth': {
            'type': 'number',
            'description': 'New border width in pixels (optional)',
            'required': False
        },
        'content': {
            'type': 'string',
            'description': 'New text content (optional)',
            'required': False
        }
    }
)

register_tool(
    'delete_shape',
    'Delete a shape from a board',
    {
        'board_id': {
            'type': 'string',
            'description': 'The ID of the board'
        },
        'item_id': {
            'type': 'string',
            'description': 'The ID of the shape item to delete'
        }
    }
)


def _build_style_dict(arguments: Dict[str, Any]) -> Dict[str, Any]:
    # Extract style properties from arguments
    style = {}
    if arguments.get('fillColor'):
        style['fillColor'] = arguments['fillColor']
    if arguments.get('borderColor'):
        style['borderColor'] = arguments['borderColor']
    # 0 is a valid borderWidth, so check is not None
    if arguments.get('borderWidth') is not None:
        style['borderWidth'] = float(arguments['borderWidth'])
    return style


def handle_tool_call(tool_name: str, arguments: Dict[str, Any], miro_client: MiroClient) -> Dict[str, Any]:
    # Route shape tool calls to appropriate handler
    if tool_name == 'create_shape':
        board_id = arguments.get('board_id')
        shape_type = arguments.get('shape_type')
        x = arguments.get('x')
        y = arguments.get('y')
        width = arguments.get('width')
        height = arguments.get('height')
        
        # 0 is a valid coordinate
        if not all([board_id, shape_type, x is not None, y is not None, width, height]):
            return {'error': 'board_id, shape_type, x, y, width, and height are required'}
        
        try:
            result = miro_client.create_shape(
                board_id=board_id,
                shape_type=shape_type,
                position={'x': float(x), 'y': float(y)},
                geometry={'width': float(width), 'height': float(height)},
                style=_build_style_dict(arguments) or None,
                content=arguments.get('content')
            )
            return {
                'success': True,
                'shape': result
            }
        except Exception as e:
            return {'error': str(e)}
    
    elif tool_name == 'update_shape':
        board_id = arguments.get('board_id')
        item_id = arguments.get('item_id')
        
        if not board_id or not item_id:
            return {'error': 'board_id and item_id are required'}
        
        position = None
        if arguments.get('x') is not None or arguments.get('y') is not None:
            position = {}
            if arguments.get('x') is not None:
                position['x'] = float(arguments['x'])
            if arguments.get('y') is not None:
                position['y'] = float(arguments['y'])
        
        geometry = None
        if arguments.get('width') is not None or arguments.get('height') is not None:
            geometry = {}
            if arguments.get('width') is not None:
                geometry['width'] = float(arguments['width'])
            if arguments.get('height') is not None:
                geometry['height'] = float(arguments['height'])
        
        try:
            result = miro_client.update_shape(
                board_id=board_id,
                item_id=item_id,
                position=position,
                geometry=geometry,
                style=_build_style_dict(arguments) or None,
                content=arguments.get('content')
            )
            return {
                'success': True,
                'shape': result
            }
        except Exception as e:
            return {'error': str(e)}
    
    elif tool_name == 'delete_shape':
        board_id = arguments.get('board_id')
        item_id = arguments.get('item_id')
        
        if not board_id or not item_id:
            return {'error': 'board_id and item_id are required'}
        
        try:
            miro_client.delete_shape(board_id, item_id)
            return {
                'success': True,
                'message': 'Shape deleted successfully'
            }
        except Exception as e:
            return {'error': str(e)}
    
    else:
        return {'error': f'Unknown shape tool: {tool_name}'}
