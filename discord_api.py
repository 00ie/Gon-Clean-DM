import requests
import time
import logging
from typing import Optional, List, Dict, Any
from utils import CacheManager

class DiscordAPI:
    """
    Cliente para API do Discord
    Inclui cache e tratamento de erros sem rate limiting artificial
    """
    
    def __init__(self):
        self.base_url = "https://discord.com/api/v10"  # URL base da API v10
        self.cache_manager = CacheManager()
        self.session = requests.Session()  # Session para reutilizar conexões
        self.logger = logging.getLogger('GonCleanDM.API')
    
    def _make_request(self, endpoint: str, token: str, method: str = "GET", **kwargs) -> Optional[Dict[Any, Any]]:
        """
        Faz requisição autenticada sem delays artificiais
        
        Args:
            endpoint: Endpoint da API (ex: "/users/@me")
            token: Token de autenticação do Discord
            method: Método HTTP ("GET", "DELETE", etc.)
            **kwargs: Argumentos adicionais para requests
            
        Returns:
            Dados JSON da resposta ou None em caso de erro
        """
        url = f"{self.base_url}{endpoint}"
        headers = {
            "Authorization": token,
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        
        try:
            response = self.session.request(method, url, headers=headers, **kwargs)
            response.raise_for_status()  # Levanta exceção para status 4xx/5xx
            return response.json()
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Falha na requisição API: {e} - URL: {endpoint}")
            return None
    
    def get_user_info(self, token: str) -> Optional[Dict[Any, Any]]:
        """
        Obtém informações do usuário atual
        
        Args:
            token: Token de autenticação
            
        Returns:
            Dicionário com informações do usuário ou None
        """
        cache_key = f"user_info_{hash(token)}"
        cached = self.cache_manager.load_cache(cache_key)
        if cached:
            return cached
        
        user_data = self._make_request("/users/@me", token)
        if user_data:
            # Salva no cache por 60 minutos
            self.cache_manager.save_cache(cache_key, user_data, max_age_minutes=60)
        
        return user_data
    
    def get_dm_channels(self, token: str) -> List[Dict[Any, Any]]:
        """
        Obtém lista de canais DM e grupos
        
        Args:
            token: Token de autenticação
            
        Returns:
            Lista de canais DM/grupos ou lista vazia
        """
        cache_key = f"dm_channels_{hash(token)}"
        cached = self.cache_manager.load_cache(cache_key)
        if cached:
            return cached
        
        channels = self._make_request("/users/@me/channels", token) or []
        # Salva no cache por 30 minutos
        self.cache_manager.save_cache(cache_key, channels, max_age_minutes=30)
        
        return channels
    
    def fetch_messages(self, token: str, channel_id: str, limit: int = 50, before: str = None) -> List[Dict[Any, Any]]:
        """
        Busca mensagens de um canal específico
        
        Args:
            token: Token de autenticação
            channel_id: ID do canal do Discord
            limit: Número máximo de mensagens (máx 100)
            before: ID da mensagem para buscar mensagens anteriores
            
        Returns:
            Lista de mensagens ou lista vazia
        """
        endpoint = f"/channels/{channel_id}/messages?limit={limit}"
        if before:
            endpoint += f"&before={before}"
        
        return self._make_request(endpoint, token) or []
    
    def delete_message(self, token: str, channel_id: str, message_id: str) -> bool:
        """
        Deleta uma mensagem específica
        
        Args:
            token: Token de autenticação
            channel_id: ID do canal
            message_id: ID da mensagem a ser deletada
            
        Returns:
            True se deletou com sucesso, False caso contrário
        """
        endpoint = f"/channels/{channel_id}/messages/{message_id}"
        result = self._make_request(endpoint, token, "DELETE")
        return result is not None

# ==================== FUNÇÕES DE COMPATIBILIDADE ====================
# Mantém compatibilidade com código existente que importa estas funções

def get_user_info(token: str) -> Optional[Dict[Any, Any]]:
    """Função de compatibilidade - obtém informações do usuário"""
    return DiscordAPI().get_user_info(token)

def get_dm_channels(token: str) -> List[Dict[Any, Any]]:
    """Função de compatibilidade - obtém canais DM"""
    return DiscordAPI().get_dm_channels(token)

def fetch_messages(token: str, channel_id: str, limit: int = 50, before: str = None) -> List[Dict[Any, Any]]:
    """Função de compatibilidade - busca mensagens"""
    return DiscordAPI().fetch_messages(token, channel_id, limit, before)

def delete_message(token: str, channel_id: str, message_id: str) -> bool:
    """Função de compatibilidade - deleta mensagem"""
    return DiscordAPI().delete_message(token, channel_id, message_id)