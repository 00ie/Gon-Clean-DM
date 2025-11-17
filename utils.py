import logging
import time
from datetime import datetime
from typing import Optional, Any
import pickle
import os
from pathlib import Path
from config import CACHE_DIR

def setup_logging():
    """
    Configura sistema de logging para a aplicação
    Cria arquivo de log e output no console
    """
    logger = logging.getLogger('GonCleanDM')
    logger.setLevel(logging.INFO)
    
    # Limpa handlers existentes para evitar duplicação
    logger.handlers.clear()
    
    # Handler para arquivo de log
    file_handler = logging.FileHandler('gon_clean_dm.log', encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    
    # Handler para console (apenas warnings e errors)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING)
    
    # Formato das mensagens de log
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # Adiciona handlers ao logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

def discord_timestamp_from_id(snowflake_id: str) -> str:
    try:
        # Fórmula para extrair timestamp do snowflake ID
        timestamp_ms = (int(snowflake_id) >> 22) + 1420070400000
        return datetime.utcfromtimestamp(timestamp_ms / 1000).strftime('%Y-%m-%d %H:%M:%S UTC')
    except Exception as e:
        logging.error(f"Erro convertendo snowflake {snowflake_id}: {e}")
        return "Desconhecido"

class CacheManager:
    """
    Gerenciando cache para melhorar performance
    """
    
    def __init__(self, cache_dir: Path = CACHE_DIR):
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(exist_ok=True)
    
    def get_cache_file(self, key: str) -> Path:
        """Retorna caminho completo do arquivo de cache para uma chave"""
        return self.cache_dir / f"{key}.pkl"
    
    def save_cache(self, key: str, data: Any, max_age_minutes: int = 30) -> bool:
        try:
            cache_data = {
                'timestamp': time.time(),
                'data': data,
                'max_age': max_age_minutes * 60  # Converter para segundos
            }
            with open(self.get_cache_file(key), 'wb') as f:
                pickle.dump(cache_data, f)
            return True
        except Exception as e:
            logging.error(f"Erro salvando cache para {key}: {e}")
            return False
    
    def load_cache(self, key: str) -> Optional[Any]:
        try:
            cache_file = self.get_cache_file(key)
            if not cache_file.exists():
                return None
            
            with open(cache_file, 'rb') as f:
                cache_data = pickle.load(f)
            
            # Verifica se o cache expirou
            if time.time() - cache_data['timestamp'] > cache_data['max_age']:
                cache_file.unlink()  # Remove cache expirado
                return None
            
            return cache_data['data']
        except Exception as e:
            logging.error(f"Erro carregando cache para {key}: {e}")
            return None
    
    def clear_cache(self, key: str = None):
        try:
            if key:
                self.get_cache_file(key).unlink(missing_ok=True)
            else:
                # Remove todos os arquivos .pkl do diretório de cache
                for file in self.cache_dir.glob("*.pkl"):
                    file.unlink()
        except Exception as e:
            logging.error(f"Erro limpando cache: {e}")

def validate_date_format(date_str: str) -> bool:
    """
    Valida se a string ta em YYYY-MM-DD
    
    Args:
        date_str: String pra validar
        
    Returns:
        True se formato é válido, False caso contrário
    """
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except ValueError:
        return False

def format_file_size(bytes_size: int) -> str:
    """
    Formata tamanho de arquivo em formato legível
    
    Args:
        bytes_size: Tamanho em bytes
        
    Returns:
        String formatada (ex: "1.5 MB", "250.0 KB")
    """
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.1f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.1f} TB"