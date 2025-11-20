import os
from pathlib import Path

# Diretório base do projeto
BASE_DIR = Path(__file__).parent

# Caminho do icone
ICON_PATH = BASE_DIR / "assets" / "icon.png"

# Diretório de cache 
CACHE_DIR = BASE_DIR / ".cache"

THEME = {
    "appear": "dark",     
    "color": "dark-blue"  
}
# Criar diretório de cache se não existir
CACHE_DIR.mkdir(exist_ok=True)