from __future__ import annotations

from boss_chess.gui.production_shell import ProductionBossChessApp
from boss_chess.gui.session import GuiSession
from boss_chess.gui.splash import show_splash
from boss_chess.types import GameConfig


def run_gui(config: GameConfig) -> None:
    show_splash()
    ProductionBossChessApp(GuiSession(config)).run()
