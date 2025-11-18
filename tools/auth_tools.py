from typing import Any, Dict
from miro_client import MiroClient
from tool_registry import register_tool

register_tool(
    'get_auth_url',
    'Get the OAuth 2.0 authorization URL to authenticate with Miro',
    {}
)

register_tool(
    'exchange_auth_code',
    'Exchange an authorization code for an access token',
    {
        'code': {
            'type': 'string',
            'description': 'The authorization code received from Miro OAuth callback'
        }
    }
)


def handle_tool_call(tool_name: str, arguments: Dict[str, Any], miro_client: MiroClient) -> Dict[str, Any]:
    # Route auth tool calls to appropriate handler
    if tool_name == 'get_auth_url':
        try:
            auth_url = miro_client.get_auth_url()
            return {
                'success': True,
                'auth_url': auth_url,
                'message': 'Visit this URL to authorize the application, then use exchange_auth_code with the code from the callback'
            }
        except Exception as e:
            return {'error': str(e)}
    
    elif tool_name == 'exchange_auth_code':
        code = arguments.get('code')
        if not code:
            return {'error': 'code parameter is required'}
        
        try:
            result = miro_client.exchange_code_for_token(code)
            return result
        except Exception as e:
            return {'error': str(e)}
    
    else:
        return {'error': f'Unknown auth tool: {tool_name}'}
