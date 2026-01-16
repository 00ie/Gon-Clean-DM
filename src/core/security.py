import time
import logging
from typing import Optional
from cryptography.fernet import Fernet
import base64
import os

class TokenManager:
    def __init__(self):
        self.key = self._get_encryption_key()
        self.cipher = Fernet(self.key)
        self.logger = logging.getLogger('GonCleanDM.Security')
        self.token_data = None
        self.token_timestamp = 0
    
    def _get_encryption_key(self) -> bytes:
        key_file = "token_key.key"
        if os.path.exists(key_file):
            with open(key_file, 'rb') as f:
                return f.read()
        else:
            key = Fernet.generate_key()
            with open(key_file, 'wb') as f:
                f.write(key)
            return key
    
    def store_token(self, token: str, timeout_minutes: int = 120):
        encrypted_token = self.cipher.encrypt(token.encode())
        self.token_data = base64.b64encode(encrypted_token).decode()
        self.token_timestamp = time.time()
        self.token_timeout = timeout_minutes * 60
        
        self.logger.info("Token armazenado com segurança")
    
    def get_token(self) -> Optional[str]:
        if not self.token_data:
            return None
        
        if time.time() - self.token_timestamp > self.token_timeout:
            self.clear_token()
            self.logger.warning("Token expirado e removido da memória")
            return None
        
        try:
            encrypted_token = base64.b64decode(self.token_data.encode())
            return self.cipher.decrypt(encrypted_token).decode()
        except Exception as e:
            self.logger.error(f"Falha na descriptografia do token: {e}")
            self.clear_token()
            return None
    
    def clear_token(self):
        self.token_data = None
        self.token_timestamp = 0
        self.logger.info("Token removido da memória")
    
    def is_token_valid(self) -> bool:
        return self.get_token() is not None