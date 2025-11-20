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
    """
    Converte ID do Discord (snowflake) para timestamp legível
    
    Args:
        snowflake_id: ID único do Discord no formato snowflake
        
    Returns:
        String com data/hora no formato 'YYYY-MM-DD HH:MM:SS UTC'
        ou 'Desconhecido' em caso de erro
    """
    try:
        # Fórmula para extrair timestamp do snowflake ID
        timestamp_ms = (int(snowflake_id) >> 22) + 1420070400000
        return datetime.utcfromtimestamp(timestamp_ms / 1000).strftime('%Y-%m-%d %H:%M:%S UTC')
    except Exception as e:
        logging.error(f"Erro convertendo snowflake {snowflake_id}: {e}")
        return "Desconhecido"

class CacheManager:
    """
    Gerenciador de cache para melhorar performance
    Armazena dados temporários como canais e informações de usuário
    """
    
    def __init__(self, cache_dir: Path = CACHE_DIR):
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(exist_ok=True)
    
    def get_cache_file(self, key: str) -> Path:
        """Retorna caminho completo do arquivo de cache para uma chave"""
        return self.cache_dir / f"{key}.pkl"
    
    def save_cache(self, key: str, data: Any, max_age_minutes: int = 30) -> bool:
        """
        Salva dados no cache com tempo de expiração
        
        Args:
            key: Chave única para identificar os dados
            data: Dados a serem armazenados
            max_age_minutes: Tempo de expiração em minutos
            
        Returns:
            True se salvou com sucesso, False em caso de erro
        """
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
        """
        Carrega dados do cache se não estiverem expirados
        
        Args:
            key: Chave única dos dados buscados
            
        Returns:
            Dados armazenados ou None se expirados/não existirem
        """
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
        """
        Limpa cache específico ou todos os caches
        
        Args:
            key: Chave específica para limpar ou None para limpar tudo
        """
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
    Valida se string está no formato de data YYYY-MM-DD
    
    Args:
        date_str: String a ser validada
        
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
    Formata tamanho de arquivo em formato legível para humanos
    
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