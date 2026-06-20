from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from boss_chess.app_paths import ensure_app_dirs, settings_path
from boss_chess.persistence import config_from_dict, config_to_dict
from boss_chess.types import GameConfig


@dataclass(slots=True)
class AppPreferences:
    config: GameConfig = field(default_factory=GameConfig)
    theme: str = "Classic"
    startup_tour_seen: bool = False
    window_geometry: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "config": config_to_dict(self.config),
            "theme": self.theme,
            "startup_tour_seen": self.startup_tour_seen,
            "window_geometry": self.window_geometry,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> "AppPreferences":
        if not isinstance(data, dict):
            return cls()
        return cls(
            config=config_from_dict(data.get("config", {})),
            theme=str(data.get("theme", "Classic")),
            startup_tour_seen=bool(data.get("startup_tour_seen", False)),
            window_geometry=data.get("window_geometry"),
        )


def load_preferences() -> AppPreferences:
    ensure_app_dirs()
    path = settings_path()
    if not path.exists():
        return AppPreferences()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return AppPreferences()
    return AppPreferences.from_dict(data)


def save_preferences(preferences: AppPreferences) -> Path:
    ensure_app_dirs()
    path = settings_path()
    path.write_text(json.dumps(preferences.to_dict(), indent=2, sort_keys=True), encoding="utf-8")
    return path
