from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from boss_chess.types import EngineConfig, GameConfig


@dataclass(slots=True)
class AppPaths:
    root: Path = Path(".")
    logs: Path = Path("logs")
    saves: Path = Path("saves")
    docs: Path = Path("docs")
    assets: Path = Path("assets")


def default_game_config() -> GameConfig:
    return GameConfig()


def config_to_dict(config: GameConfig) -> dict[str, Any]:
    data = asdict(config)
    return data


def ensure_directories(paths: AppPaths) -> None:
    for path in (paths.logs, paths.saves, paths.docs, paths.assets):
        path.mkdir(parents=True, exist_ok=True)
