from __future__ import annotations

from boss_chess.gui.session import GuiSession
from boss_chess.gui.window import BossChessApp
from boss_chess.types import GameConfig


def run_gui(config: GameConfig) -> None:
    app = BossChessApp(GuiSession(config))
    app.run()
