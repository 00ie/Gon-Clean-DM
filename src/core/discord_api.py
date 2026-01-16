import requests
import logging
from typing import Optional, List, Dict, Any
from src.core.utils import CacheManager

class DiscordAPI:
    def __init__(self):
        self.base_url = "https://discord.com/api/v10"
        self.cache_manager = CacheManager()
        self.session = requests.Session()
        self.logger = logging.getLogger('GonCleanDM.API')
    
    def _make_request(self, endpoint: str, token: str, method: str = "GET", **kwargs) -> Optional[Dict[Any, Any]]:
        url = f"{self.base_url}{endpoint}"
        headers = {
            "Authorization": token,
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        
        try:
            response = self.session.request(method, url, headers=headers, **kwargs)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Falha na requisição API: {e} - URL: {endpoint}")
            return None
    
    def get_user_info(self, token: str) -> Optional[Dict[Any, Any]]:
        cache_key = f"user_info_{hash(token)}"
        cached = self.cache_manager.load_cache(cache_key)
        if cached:
            return cached
        
        user_data = self._make_request("/users/@me", token)
        if user_data:
            self.cache_manager.save_cache(cache_key, user_data, max_age_minutes=60)
        
        return user_data
    
    def get_dm_channels(self, token: str) -> List[Dict[Any, Any]]:
        cache_key = f"dm_channels_{hash(token)}"
        cached = self.cache_manager.load_cache(cache_key)
        if cached:
            return cached
        
        channels = self._make_request("/users/@me/channels", token) or []
        self.cache_manager.save_cache(cache_key, channels, max_age_minutes=30)
        
        return channels
    
    def fetch_messages(self, token: str, channel_id: str, limit: int = 50, before: str = None) -> List[Dict[Any, Any]]:
        endpoint = f"/channels/{channel_id}/messages?limit={limit}"
        if before:
            endpoint += f"&before={before}"
        
        return self._make_request(endpoint, token) or []
    
    def delete_message(self, token: str, channel_id: str, message_id: str) -> bool:
        endpoint = f"/channels/{channel_id}/messages/{message_id}"
        result = self._make_request(endpoint, token, "DELETE")
        return result is not None

def get_user_info(token: str) -> Optional[Dict[Any, Any]]:
    return DiscordAPI().get_user_info(token)

def get_dm_channels(token: str) -> List[Dict[Any, Any]]:
    return DiscordAPI().get_dm_channels(token)

def fetch_messages(token: str, channel_id: str, limit: int = 50, before: str = None) -> List[Dict[Any, Any]]:
    return DiscordAPI().fetch_messages(token, channel_id, limit, before)

def delete_message(token: str, channel_id: str, message_id: str) -> bool:
    return DiscordAPI().delete_message(token, channel_id, message_id)