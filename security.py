import time
import logging
from typing import Optional
from cryptography.fernet import Fernet
import base64
import os

class TokenManager:
    """
    Gerenciador seguro de tokens com criptografia
    Armazena tokens encriptados na memória com timeout automático
    """
    
    def __init__(self):
        self.key = self._get_encryption_key()
        self.cipher = Fernet(self.key)
        self.logger = logging.getLogger('GonCleanDM.Security')
        self.token_data = None
        self.token_timestamp = 0
    
    def _get_encryption_key(self) -> bytes:
        """
        Obtém ou gera chave de criptografia
        A chave é armazenada em arquivo para persistência entre execuções
        """
        key_file = "token_key.key"
        if os.path.exists(key_file):
            with open(key_file, 'rb') as f:
                return f.read()
        else:
            # Gera nova chave se não existir
            key = Fernet.generate_key()
            with open(key_file, 'wb') as f:
                f.write(key)
            return key
    
    def store_token(self, token: str, timeout_minutes: int = 120):
        """
        Armazena token encriptado na memória com timeout
        
        Args:
            token: Token do Discord a ser armazenado
            timeout_minutes: Tempo em minutos até limpar automaticamente
        """
        # Encripta o token antes de armazenar
        encrypted_token = self.cipher.encrypt(token.encode())
        # Codifica em base64 para armazenamento seguro
        self.token_data = base64.b64encode(encrypted_token).decode()
        self.token_timestamp = time.time()
        self.token_timeout = timeout_minutes * 60  # Converte para segundos
        
        self.logger.info("Token armazenado com segurança")
    
    def get_token(self) -> Optional[str]:
        """
        Recupera e descriptografa token se não estiver expirado
        
        Returns:
            Token descriptografado ou None se expirado/inválido
        """
        if not self.token_data:
            return None
        
        # Verifica se o token expirou
        if time.time() - self.token_timestamp > self.token_timeout:
            self.clear_token()
            self.logger.warning("Token expirado e removido da memória")
            return None
        
        try:
            # Decodifica e descriptografa o token
            encrypted_token = base64.b64decode(self.token_data.encode())
            return self.cipher.decrypt(encrypted_token).decode()
        except Exception as e:
            self.logger.error(f"Falha na descriptografia do token: {e}")
            self.clear_token()
            return None
    
    def clear_token(self):
        """Limpa token armazenado da memória"""
        self.token_data = None
        self.token_timestamp = 0
        self.logger.info("Token removido da memória")
    
    def is_token_valid(self) -> bool:
        """
        Verifica se token existe e não está expirado
        
        Returns:
            True se token é válido, False caso contrário
        """
        return self.get_token() is not None