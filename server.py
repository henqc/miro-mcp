import json
import sys
import traceback
from typing import Any, Dict, Optional, Callable
from miro_client import MiroClient
from tool_registry import TOOLS
from tools import shape_tools, group_tools, auth_tools, board_tools


def handle_initialize(params: Dict[str, Any]) -> Dict[str, Any]:
    # Initialize MCP protocol handshake
    return {
        'protocolVersion': '2024-11-05',
        'capabilities': {
            'tools': {}
        },
        'serverInfo': {
            'name': 'miro-mcp-server',
            'version': '1.0.0'
        }
    }


def handle_tools_list() -> Dict[str, Any]:
    # Return list of all registered tools
    return {
        'tools': list(TOOLS.values())
    }


def handle_tools_call(tool_name: str, arguments: Dict[str, Any], get_miro_client: Callable[[], MiroClient]) -> Dict[str, Any]:
    # Execute tool by routing to appropriate handler
    if tool_name not in TOOLS:
        return {
            'content': [{
                'type': 'text',
                'text': f'Unknown tool: {tool_name}'
            }],
            'isError': True
        }
    
    try:
        miro_client = get_miro_client()
        
        if tool_name in ['create_shape', 'update_shape', 'delete_shape']:
            result = shape_tools.handle_tool_call(tool_name, arguments, miro_client)
        elif tool_name in ['group_shapes', 'ungroup_shapes']:
            result = group_tools.handle_tool_call(tool_name, arguments, miro_client)
        elif tool_name.startswith('get_auth') or tool_name.startswith('exchange_auth'):
            result = auth_tools.handle_tool_call(tool_name, arguments, miro_client)
        elif tool_name == 'get_board':
            result = board_tools.handle_tool_call(tool_name, arguments, miro_client)
        else:
            return {
                'content': [{
                    'type': 'text',
                    'text': f'No handler for tool: {tool_name}'
                }],
                'isError': True
            }
        return {
            'content': [{
                'type': 'text',
                'text': json.dumps(result, indent=2)
            }]
        }
    except Exception as e:
        return {
            'content': [{
                'type': 'text',
                'text': f'Error executing tool {tool_name}: {str(e)}'
            }],
            'isError': True
        }


def process_request(request: Dict[str, Any], get_miro_client: Callable[[], MiroClient]) -> Optional[Dict[str, Any]]:
    # Process JSON-RPC request and route to appropriate handler
    method = request.get('method')
    params = request.get('params', {})
    request_id = request.get('id')
    
    if method == 'initialize':
        response = handle_initialize(params)
    elif method == 'tools/list':
        response = handle_tools_list()
    elif method == 'tools/call':
        tool_name = params.get('name')
        arguments = params.get('arguments', {})
        response = handle_tools_call(tool_name, arguments, get_miro_client)
    else:
        # Notifications don't need responses
        if request_id is not None:
            return {
                'jsonrpc': '2.0',
                'id': request_id,
                'error': {
                    'code': -32601,
                    'message': f'Method not found: {method}'
                }
            }
        return None
    
    if request_id is not None:
        return {
            'jsonrpc': '2.0',
            'id': request_id,
            'result': response
        }
    return None


def main():
    miro_client = None
    
    def get_miro_client():
        # Lazy initialization of Miro client
        nonlocal miro_client
        if miro_client is None:
            try:
                miro_client = MiroClient()
            except Exception as e:
                print(f"Error initializing Miro client: {e}", file=sys.stderr)
                sys.stderr.flush()
                traceback.print_exc(file=sys.stderr)
                sys.stderr.flush()
                raise
        return miro_client
    
    # Tool modules are imported at top level to trigger registration
    
    # Main loop: read JSON-RPC requests from stdin
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        
        try:
            request = json.loads(line)
            response = process_request(request, get_miro_client)
            
            if response:
                print(json.dumps(response))
                sys.stdout.flush()
        except json.JSONDecodeError as e:
            error_response = {
                'jsonrpc': '2.0',
                'id': None,
                'error': {
                    'code': -32700,
                    'message': f'Parse error: {str(e)}'
                }
            }
            print(json.dumps(error_response))
            sys.stdout.flush()
        except Exception as e:
            print(f"Error processing request: {e}", file=sys.stderr)
            traceback.print_exc(file=sys.stderr)
            sys.stderr.flush()
            error_response = {
                'jsonrpc': '2.0',
                'id': None,
                'error': {
                    'code': -32603,
                    'message': f'Internal error: {str(e)}'
                }
            }
            print(json.dumps(error_response))
            sys.stdout.flush()


if __name__ == '__main__':
    main()
