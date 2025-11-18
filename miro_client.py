import json
from typing import Optional, Dict, Any
from datetime import datetime
import miro_api
import requests
from config import (
    MIRO_CLIENT_ID,
    MIRO_CLIENT_SECRET,
    MIRO_REDIRECT_URL,
    TOKEN_STORAGE_FILE,
    validate_config
)


def convert_to_dict(obj: Any) -> Any:
    # Convert Pydantic models and complex objects to JSON-serializable dicts
    if obj is None:
        return None
    
    type_str = str(type(obj))
    if type_str.startswith('typing.') or 'typing' in type_str:
        return str(obj)
    
    # Try Pydantic v2, fallback to v1
    if hasattr(obj, 'model_dump'):
        try:
            return obj.model_dump(mode='json')
        except Exception:
            try:
                return obj.model_dump()
            except Exception:
                pass
    
    if hasattr(obj, 'dict') and callable(getattr(obj, 'dict')):
        try:
            return obj.dict()
        except Exception:
            pass
    
    if isinstance(obj, (str, int, float, bool)):
        return obj
    
    if isinstance(obj, datetime):
        return obj.isoformat()
    
    if isinstance(obj, dict):
        return {k: convert_to_dict(v) for k, v in obj.items()}
    
    if isinstance(obj, (list, tuple, set)):
        return [convert_to_dict(item) for item in obj]
    
    if hasattr(obj, '__dict__'):
        try:
            result = {}
            for k, v in obj.__dict__.items():
                if not k.startswith('_') or k == '__class__':
                    try:
                        result[k] = convert_to_dict(v)
                    except Exception:
                        try:
                            result[k] = str(v)
                        except Exception:
                            pass
            return result
        except Exception:
            pass
    
    try:
        return str(obj)
    except Exception:
        return None


class MiroClient:
    def __init__(self):
        # Initialize client with config validation and token loading
        validate_config()
        self.client_id = MIRO_CLIENT_ID
        self.client_secret = MIRO_CLIENT_SECRET
        self.redirect_url = MIRO_REDIRECT_URL
        self._miro: Optional[miro_api.Miro] = None
        self._stored_access_token: Optional[str] = None
        self._stored_refresh_token: Optional[str] = None
        self._load_tokens()
    
    def _load_tokens(self) -> None:
        # Load stored OAuth tokens from file
        if not TOKEN_STORAGE_FILE.exists():
            return
        
        try:
            with open(TOKEN_STORAGE_FILE, 'r') as f:
                tokens = json.load(f)
                self._stored_access_token = tokens['access_token']
                self._stored_refresh_token = tokens.get('refresh_token')
        except (json.JSONDecodeError, KeyError):
            TOKEN_STORAGE_FILE.unlink(missing_ok=True)
            self._stored_access_token = None
            self._stored_refresh_token = None
    
    def _save_tokens(self) -> None:
        # Save OAuth tokens to file for persistence
        access_token = None
        refresh_token = None
        
        if self._miro and hasattr(self._miro, 'access_token') and self._miro.access_token:
            access_token = self._miro.access_token
            refresh_token = getattr(self._miro, 'refresh_token', None)
        elif self._stored_access_token:
            access_token = self._stored_access_token
            refresh_token = self._stored_refresh_token
        
        if access_token:
            tokens = {
                'access_token': access_token,
                'refresh_token': refresh_token
            }
            with open(TOKEN_STORAGE_FILE, 'w') as f:
                json.dump(tokens, f)
            self._stored_access_token = access_token
            self._stored_refresh_token = refresh_token
    
    def get_auth_url(self) -> str:
        # Generate OAuth authorization URL for user to visit
        self._miro = miro_api.Miro(
            client_id=self.client_id,
            client_secret=self.client_secret,
            redirect_url=self.redirect_url
        )
        return self._miro.auth_url
    
    def exchange_code_for_token(self, code: str) -> Dict[str, Any]:
        # Exchange OAuth authorization code for access token
        if not self._miro:
            raise ValueError(
                "Miro instance not initialized. Please call get_auth_url() first to start the OAuth flow."
            )
        
        self._miro.exchange_code_for_access_token(code)
        self._save_tokens()
        return {
            'success': True,
            'message': 'Successfully authenticated with Miro'
        }
    
    def is_authenticated(self) -> bool:
        # Check if client has valid access token
        if self._miro and hasattr(self._miro, 'access_token') and self._miro.access_token:
            return True
        return self._stored_access_token is not None
    
    def _ensure_authenticated(self) -> None:
        # Raise error if not authenticated
        if not self.is_authenticated():
            raise ValueError(
                "Not authenticated. Please complete OAuth flow first. "
                "Use get_auth_url() to get authorization URL, then exchange_code_for_token() with the code."
            )
    
    def _get_api(self):
        # Get authenticated Miro API client instance
        self._ensure_authenticated()
        
        # Miro API client requires tokens set via OAuth flow
        if not self._miro or not hasattr(self._miro, 'access_token') or not self._miro.access_token:
            if self._stored_access_token:
                raise ValueError(
                    "Miro API client requires tokens to be set through OAuth flow. "
                    "Please call get_auth_url() and exchange_code_for_token() to re-authenticate."
                )
            raise ValueError("Not authenticated. Please complete OAuth flow first.")
        
        return self._miro.api
    
    def _format_style(self, style: Dict[str, Any]) -> Dict[str, Any]:
        # Convert camelCase style keys to snake_case for API
        style_clean = {}
        for key, value in style.items():
            if key == 'fillColor':
                style_clean['fill_color'] = value
                if 'fill_opacity' not in style_clean:
                    style_clean['fill_opacity'] = '1.0'
            elif key == 'borderColor':
                style_clean['border_color'] = value
                if 'border_opacity' not in style_clean:
                    style_clean['border_opacity'] = '1.0'
            elif key == 'borderWidth':
                style_clean['border_width'] = str(float(value))
            else:
                style_clean[key] = value
        return style_clean
    
    def _format_shape_data(
        self,
        shape_type: str,
        position: Dict[str, float],
        geometry: Dict[str, float],
        style: Optional[Dict[str, Any]] = None,
        content: Optional[str] = None
    ) -> Dict[str, Any]:
        # Format shape data structure for API call
        shape_data = {
            'data': {
                'shape': shape_type
            },
            'position': {
                'x': float(position['x']),
                'y': float(position['y'])
            },
            'geometry': {
                'width': float(geometry['width']),
                'height': float(geometry['height'])
            }
        }
        
        if content:
            shape_data['data']['content'] = content
        
        if style:
            shape_data['style'] = self._format_style(style)
        
        return shape_data
    
    def create_shape(
        self,
        board_id: str,
        shape_type: str,
        position: Dict[str, float],
        geometry: Dict[str, float],
        style: Optional[Dict[str, Any]] = None,
        content: Optional[str] = None
    ) -> Dict[str, Any]:
        # Create a new shape on the board
        api = self._get_api()
        shape_data = self._format_shape_data(shape_type, position, geometry, style, content)
        result = api.create_shape_item(board_id, shape_data)
        return convert_to_dict(result)
    
    def update_shape(
        self,
        board_id: str,
        item_id: str,
        position: Optional[Dict[str, float]] = None,
        geometry: Optional[Dict[str, float]] = None,
        style: Optional[Dict[str, Any]] = None,
        content: Optional[str] = None
    ) -> Dict[str, Any]:
        # Update existing shape properties
        api = self._get_api()
        update_data = {}
        
        if position:
            position_update = {}
            if 'x' in position:
                position_update['x'] = float(position['x'])
            if 'y' in position:
                position_update['y'] = float(position['y'])
            if position_update:
                update_data['position'] = position_update
        
        if geometry:
            update_data['geometry'] = {
                'width': float(geometry['width']),
                'height': float(geometry['height'])
            }
        
        if content is not None:
            update_data['data'] = {'content': content}
        
        if style:
            update_data['style'] = self._format_style(style)
        
        result = api.update_shape_item(board_id, item_id, update_data)
        return convert_to_dict(result)
    
    def delete_shape(self, board_id: str, item_id: str) -> Dict[str, Any]:
        # Delete shape from board
        api = self._get_api()
        api.delete_shape_item(board_id, item_id)
        return {'success': True, 'message': f'Shape {item_id} deleted successfully'}
    
    def get_board(self, board_id: str) -> Dict[str, Any]:
        # Get board information and metadata
        self._ensure_authenticated()
        # Direct HTTP request since SDK doesn't have get_board method
        url = f"https://api.miro.com/v2/boards/{board_id}"
        
        access_token = None
        if self._miro and hasattr(self._miro, 'access_token') and self._miro.access_token:
            access_token = self._miro.access_token
        elif self._stored_access_token:
            access_token = self._stored_access_token
        else:
            raise ValueError("No access token available")
        
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return convert_to_dict(response.json())
    
    def _get_item_from_api(self, api, board_id: str, item_id: str):
        # Get item from API trying shape then frame then all items
        try:
            return api.get_shape_item(board_id, item_id)
        except Exception:
            try:
                return api.get_frame_item(board_id, item_id)
            except (AttributeError, Exception):
                # Different item types require different API methods
                all_items = api.get_items(board_id)
                items_list = self._extract_items_list(all_items)
                item_id_str = str(item_id)
                for item in items_list:
                    if str(item.get('id', '')) == item_id_str:
                        return item
                raise ValueError(f"Item {item_id} not found on board {board_id}")
    
    def _extract_items_list(self, all_items_result):
        # Extract items list from API response format
        all_items = convert_to_dict(all_items_result)
        if isinstance(all_items, dict) and 'data' in all_items:
            return all_items['data']
        elif isinstance(all_items, list):
            return all_items
        else:
            raise ValueError(f"Unexpected response format from API: {type(all_items_result)}")
    
    def group_shapes(self, board_id: str, item_ids: list) -> Dict[str, Any]:
        # Group multiple shapes into a frame
        api = self._get_api()
        
        items = []
        for item_id in item_ids:
            item = self._get_item_from_api(api, board_id, item_id)
            items.append(convert_to_dict(item))
        
        if not items:
            raise ValueError("No items found to group")
        
        # Calculate bounding box for frame
        positions = [item['position'] for item in items]
        geometries = [item['geometry'] for item in items]
        
        min_x = float(min(pos['x'] for pos in positions))
        min_y = float(min(pos['y'] for pos in positions))
        max_x = float(max(pos['x'] + geom['width'] for pos, geom in zip(positions, geometries)))
        max_y = float(max(pos['y'] + geom['height'] for pos, geom in zip(positions, geometries)))
        
        # Miro uses frames to group items
        frame_data = {
            'data': {'title': 'Group'},
            'position': {'x': min_x, 'y': min_y},
            'geometry': {
                'width': float(max_x - min_x),
                'height': float(max_y - min_y)
            }
        }
        
        frame_result = api.create_frame_item(board_id, frame_data)
        frame = convert_to_dict(frame_result)
        frame_id = frame['id']
        
        for item_id in item_ids:
            api.update_item_position_or_parent(board_id, item_id, {'parent': {'id': frame_id}})
        
        return frame
    
    def ungroup_shapes(self, board_id: str, group_id: str) -> Dict[str, Any]:
        # Remove shapes from frame and delete the frame
        api = self._get_api()
        
        try:
            frame = api.get_frame_item(board_id, group_id)
        except AttributeError:
            all_items = api.get_items(board_id)
            items_list = self._extract_items_list(all_items)
            frame = next((item for item in items_list if str(item.get('id', '')) == str(group_id)), None)
            if not frame:
                raise ValueError(f"Frame {group_id} not found on board {board_id}")
        except Exception as e:
            raise ValueError(f"Frame {group_id} not found: {str(e)}")
        
        frame_dict = convert_to_dict(frame)
        
        if frame_dict['type'] != 'frame':
            raise ValueError(f"Item {group_id} is not a frame/group")
        
        items_list = self._extract_items_list(api.get_items(board_id))
        board_items = [
            item for item in items_list
            if item.get('parent') and item['parent']['id'] == group_id
        ]
        
        for item in board_items:
            item_id = item['id']
            api.update_item_position_or_parent(board_id, item_id, {'parent': None})
        
        api.delete_frame_item(board_id, group_id)
        
        return {'success': True, 'message': f'Ungrouped {len(board_items)} items'}
