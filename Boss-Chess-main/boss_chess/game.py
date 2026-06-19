from __future__ import annotations

from boss_chess.config import default_game_config
from boss_chess.types import GameConfig
from boss_chess.ui.terminal import TerminalGame


def run_game(config: GameConfig | None = None) -> None:
    game = TerminalGame(config or default_game_config())
    game.run()
