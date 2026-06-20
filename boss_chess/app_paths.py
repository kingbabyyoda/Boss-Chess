from __future__ import annotations

import os
from pathlib import Path

APP_NAME = "BossChess"
SETTINGS_FILE = "settings.json"
LOG_FILE = "boss_chess.log"


def app_root() -> Path:
    if os.name == "nt":
        base = Path(os.environ.get("APPDATA") or os.environ.get("LOCALAPPDATA") or Path.home())
        return base / APP_NAME
    if os.environ.get("XDG_CONFIG_HOME"):
        return Path(os.environ["XDG_CONFIG_HOME"]) / APP_NAME
    return Path.home() / ".config" / APP_NAME


def settings_path() -> Path:
    return app_root() / SETTINGS_FILE


def logs_dir() -> Path:
    return app_root() / "logs"


def crashes_dir() -> Path:
    return app_root() / "crashes"


def ensure_app_dirs() -> None:
    app_root().mkdir(parents=True, exist_ok=True)
    logs_dir().mkdir(parents=True, exist_ok=True)
    crashes_dir().mkdir(parents=True, exist_ok=True)
