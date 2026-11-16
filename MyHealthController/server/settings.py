"""Paths are anchored to the installation, never to the current directory."""
import os
from pathlib import Path

SERVER_DIR = Path(__file__).resolve().parent
CONTROLLER_DIR = SERVER_DIR.parent


def configured_path(name, default):
    path = Path(os.environ.get(name, str(default))).expanduser()
    return path.resolve() if path.is_absolute() else (CONTROLLER_DIR / path).resolve()


DATA_DIR = configured_path('MYHEALTHKIT_DATA_DIR', CONTROLLER_DIR / 'data')
DATABASE_PATH = configured_path('MYHEALTHKIT_DATABASE', CONTROLLER_DIR / 'database/pharmacy.db')
AUDIO_DIR = DATA_DIR / 'audio'
KEYS_PATH = configured_path('MYHEALTHKIT_KEYS', SERVER_DIR / 'keys.env')
MODEL_DIR = configured_path('MYHEALTHKIT_MODELS', SERVER_DIR / 'vosk-models')
