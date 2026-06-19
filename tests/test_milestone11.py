from __future__ import annotations

from pathlib import Path

from boss_chess.persistence import load_game, save_game
from boss_chess.state import GameState
from boss_chess.types import GameConfig, GameVariant


def test_variant_and_multiplayer_settings_round_trip(tmp_path: Path) -> None:
    config = GameConfig()
    config.variant.name = GameVariant.THREE_CHECK
    config.variant.chess960_seed = 42
    config.multiplayer.mode = "host"
    config.multiplayer.host = "0.0.0.0"
    config.multiplayer.port = 9234
    config.multiplayer.username = "Boss"

    state = GameState(variant=config.variant.name.value, chess960_seed=config.variant.chess960_seed)
    path = tmp_path / "save.json"
    save_game(path, state, config, ai_color=state.board.turn, cheat=state.board.turn)

    loaded = load_game(path)

    assert loaded.config.variant.name == GameVariant.THREE_CHECK
    assert loaded.config.variant.chess960_seed == 42
    assert loaded.config.multiplayer.mode == "host"
    assert loaded.config.multiplayer.port == 9234
    assert loaded.config.multiplayer.username == "Boss"
    assert loaded.state.variant == GameVariant.THREE_CHECK.value
