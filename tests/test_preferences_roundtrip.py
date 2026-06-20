from __future__ import annotations

from boss_chess.preferences import AppPreferences
from boss_chess.persistence import config_from_dict, config_to_dict
from boss_chess.types import GameConfig, GameVariant


def test_game_config_roundtrip() -> None:
    config = GameConfig()
    config.trainer = True
    config.meme = True
    config.cheat = True
    config.ui_scale = 1.15
    config.reduce_motion = True
    config.high_contrast = True
    config.piece_set = "Slate"
    config.engine.depth = 5
    config.engine.use_stockfish = True
    config.engine.stockfish_path = "/tmp/stockfish"
    config.engine.use_opening_book = False
    config.engine.target_elo = 2200
    config.engine.multi_pv = 4
    config.variant.name = GameVariant.CHESS960
    config.variant.chess960_seed = 512
    config.multiplayer.mode = "host"
    config.multiplayer.host = "0.0.0.0"
    config.multiplayer.port = 9000
    config.multiplayer.username = "Boss"

    restored = config_from_dict(config_to_dict(config))

    assert restored.trainer is True
    assert restored.meme is True
    assert restored.cheat is True
    assert restored.ui_scale == 1.15
    assert restored.reduce_motion is True
    assert restored.high_contrast is True
    assert restored.piece_set == "Slate"
    assert restored.engine.depth == 5
    assert restored.engine.use_stockfish is True
    assert restored.engine.stockfish_path == "/tmp/stockfish"
    assert restored.engine.use_opening_book is False
    assert restored.engine.target_elo == 2200
    assert restored.engine.multi_pv == 4
    assert restored.variant.name == GameVariant.CHESS960
    assert restored.variant.chess960_seed == 512
    assert restored.multiplayer.mode == "host"
    assert restored.multiplayer.host == "0.0.0.0"
    assert restored.multiplayer.port == 9000
    assert restored.multiplayer.username == "Boss"


def test_app_preferences_roundtrip() -> None:
    prefs = AppPreferences()
    prefs.theme = "Neon"
    prefs.startup_tour_seen = True
    prefs.window_geometry = "1400x900+20+20"
    prefs.config.piece_set = "Neon"

    restored = AppPreferences.from_dict(prefs.to_dict())

    assert restored.theme == "Neon"
    assert restored.startup_tour_seen is True
    assert restored.window_geometry == "1400x900+20+20"
    assert restored.config.piece_set == "Neon"
