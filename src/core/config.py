from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]

ICON_ICO_PATH = BASE_DIR / "assets" / "icon.ico"
ICON_PATH = BASE_DIR / "assets" / "icon.png"

CACHE_DIR = BASE_DIR / ".cache"
AVATAR_CACHE_DIR = CACHE_DIR / "avatars"
LOG_DIR = BASE_DIR / "logs"
EXPORTS_DIR = BASE_DIR / "exports"

THEME = {
    "appear": "dark",
    "color": "dark-blue"
}

PALETTE = {
    "bg": "#000000",
    "panel": "#0a0a0a",
    "panel_alt": "#0f0f0f",
    "panel_soft": "#141414",
    "panel_soft_alt": "#1b1b1b",
    "text": "#e6e6e6",
    "muted": "#b5b5b5",
    "accent": "#3aa0ff",
    "accent_hover": "#2b7bd1",
    "success": "#2ecc71",
    "success_hover": "#27ae60",
    "danger": "#e74c3c",
    "danger_hover": "#c0392b",
    "info": "#20b7c7",
    "info_hover": "#1799a8",
    "link": "#55dfff"
}
CACHE_DIR.mkdir(exist_ok=True)
AVATAR_CACHE_DIR.mkdir(exist_ok=True)
LOG_DIR.mkdir(exist_ok=True)
EXPORTS_DIR.mkdir(exist_ok=True)