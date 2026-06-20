from __future__ import annotations

import os

from boss_chess.gui.production_shell import ProductionBossChessApp
from boss_chess.gui.session import GuiSession
from boss_chess.gui.splash import show_splash
from boss_chess.preferences import AppPreferences
from boss_chess.types import GameConfig


def run_gui(config: GameConfig, preferences: AppPreferences | None = None) -> None:
    prefs = preferences or AppPreferences(config=config)
    os.environ["BOSS_CHESS_PIECE_SET"] = prefs.config.piece_set
    show_splash()
    ProductionBossChessApp(GuiSession(prefs.config), prefs).run()
