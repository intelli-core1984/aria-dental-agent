"""
ARIA — Centralized path handling.
Works correctly both when running from source and when frozen by PyInstaller.
"""
import sys
import os
from pathlib import Path


def get_resource_dir() -> Path:
    """Read-only resources bundled with the exe (skills, etc.)."""
    if getattr(sys, 'frozen', False):
        return Path(sys._MEIPASS)
    return Path(__file__).parent


def get_data_dir() -> Path:
    """Writable data directory — persistent across runs, never inside the exe."""
    if sys.platform == 'win32':
        base = Path(os.environ.get('APPDATA', Path.home())) / 'ARIA'
    elif sys.platform == 'darwin':
        base = Path.home() / 'Library' / 'Application Support' / 'ARIA'
    else:
        base = Path.home() / '.aria'
    base.mkdir(parents=True, exist_ok=True)
    return base


def get_config_path() -> Path:
    """Path to the .env config file."""
    return get_data_dir() / '.env'
