import logging
import time
from datetime import datetime
from typing import Optional, Any
import pickle
from pathlib import Path
from src.core.config import CACHE_DIR, LOG_DIR

def setup_logging():
    logger = logging.getLogger('GonCleanDM')
    logger.setLevel(logging.INFO)

    logger.handlers.clear()

    LOG_DIR.mkdir(exist_ok=True)
    file_handler = logging.FileHandler(LOG_DIR / 'gon_clean_dm.log', encoding='utf-8')
    file_handler.setLevel(logging.INFO)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING)

    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

def discord_timestamp_from_id(snowflake_id: str) -> str:
    try:
        timestamp_ms = (int(snowflake_id) >> 22) + 1420070400000
        return datetime.utcfromtimestamp(timestamp_ms / 1000).strftime('%Y-%m-%d %H:%M:%S UTC')
    except Exception as e:
        logging.error(f"Erro convertendo snowflake {snowflake_id}: {e}")
        return "Desconhecido"

class CacheManager:
    def __init__(self, cache_dir: Path = CACHE_DIR):
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(exist_ok=True)
    
    def get_cache_file(self, key: str) -> Path:
        return self.cache_dir / f"{key}.pkl"
    
    def save_cache(self, key: str, data: Any, max_age_minutes: int = 30) -> bool:
        try:
            cache_data = {
                'timestamp': time.time(),
                'data': data,
                'max_age': max_age_minutes * 60
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
            
            if time.time() - cache_data['timestamp'] > cache_data['max_age']:
                cache_file.unlink()
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
                for file in self.cache_dir.glob("*.pkl"):
                    file.unlink()
        except Exception as e:
            logging.error(f"Erro limpando cache: {e}")

def validate_date_format(date_str: str) -> bool:
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except ValueError:
        return False

def format_file_size(bytes_size: int) -> str:
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.1f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.1f} TB"