from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import chess

from boss_chess.cheat_events.core import CheatController
from boss_chess.state import GameState
from boss_chess.types import EngineConfig, GameConfig, GameVariant, MultiplayerConfig, VariantConfig


@dataclass(slots=True)
class SavedGame:
    version: int
    created_at: str
    start_fen: str
    current_fen: str
    moves: list[str]
    config: dict[str, Any]
    ai_color: str
    cheat: dict[str, Any]


@dataclass(slots=True)
class LoadedGame:
    state: GameState
    config: GameConfig
    ai_color: chess.Color
    cheat: CheatController


def save_game(path: Path, state: GameState, config: GameConfig, ai_color: chess.Color, cheat: CheatController) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = SavedGame(
        version=2,
        created_at=datetime.now(timezone.utc).isoformat(),
        start_fen=state.starting_fen,
        current_fen=state.board.fen(),
        moves=[move.uci() for move in state.move_history],
        config=_config_to_dict(config),
        ai_color="white" if ai_color == chess.WHITE else "black",
        cheat=cheat.to_dict(),
    )
    path.write_text(json.dumps(asdict(payload), indent=2, sort_keys=True), encoding="utf-8")


def load_game(path: Path) -> LoadedGame:
    data = json.loads(path.read_text(encoding="utf-8"))

    config = _config_from_dict(data.get("config", {}))
    start_fen = str(data.get("start_fen", chess.STARTING_FEN))
    state = GameState(
        starting_fen=start_fen,
        variant=config.variant.name.value,
        chess960_seed=config.variant.chess960_seed,
    )
    state.move_history = []

    for move_text in data.get("moves", []):
        try:
            move = chess.Move.from_uci(str(move_text))
        except ValueError:
            continue
        if move in state.board.legal_moves:
            state.push(move)

    current_fen = str(data.get("current_fen", state.board.fen()))
    if state.board.fen() != current_fen:
        state.board = chess.Board(current_fen)

    ai_color = chess.WHITE if data.get("ai_color", "black") == "white" else chess.BLACK
    cheat = CheatController.from_dict(data.get("cheat", {}))
    return LoadedGame(state=state, config=config, ai_color=ai_color, cheat=cheat)


def _config_to_dict(config: GameConfig) -> dict[str, Any]:
    return {
        "ai_plays_white": config.ai_plays_white,
        "trainer": config.trainer,
        "meme": config.meme,
        "cheat": config.cheat,
        "engine": {
            "depth": config.engine.depth,
            "use_stockfish": config.engine.use_stockfish,
            "stockfish_path": config.engine.stockfish_path,
            "use_opening_book": config.engine.use_opening_book,
            "target_elo": config.engine.target_elo,
            "multi_pv": config.engine.multi_pv,
        },
        "variant": {
            "name": config.variant.name.value if isinstance(config.variant.name, GameVariant) else str(config.variant.name),
            "chess960_seed": config.variant.chess960_seed,
        },
        "multiplayer": {
            "mode": config.multiplayer.mode,
            "host": config.multiplayer.host,
            "port": config.multiplayer.port,
            "username": config.multiplayer.username,
        },
    }


def _config_from_dict(data: dict[str, Any]) -> GameConfig:
    engine_data = data.get("engine", {}) if isinstance(data, dict) else {}
    variant_data = data.get("variant", {}) if isinstance(data, dict) else {}
    mp_data = data.get("multiplayer", {}) if isinstance(data, dict) else {}
    engine = EngineConfig(
        depth=int(engine_data.get("depth", 3)),
        use_stockfish=bool(engine_data.get("use_stockfish", False)),
        stockfish_path=engine_data.get("stockfish_path"),
        use_opening_book=bool(engine_data.get("use_opening_book", True)),
        target_elo=int(engine_data.get("target_elo", 1800)),
        multi_pv=int(engine_data.get("multi_pv", 3)),
    )
    variant = VariantConfig(
        name=GameVariant(str(variant_data.get("name", GameVariant.STANDARD.value))),
        chess960_seed=int(variant_data.get("chess960_seed", 0)),
    )
    multiplayer = MultiplayerConfig(
        mode=str(mp_data.get("mode", "offline")),
        host=str(mp_data.get("host", "127.0.0.1")),
        port=int(mp_data.get("port", 8765)),
        username=str(mp_data.get("username", "Player")),
    )
    return GameConfig(
        ai_plays_white=bool(data.get("ai_plays_white", False)),
        trainer=bool(data.get("trainer", False)),
        meme=bool(data.get("meme", False)),
        cheat=bool(data.get("cheat", False)),
        engine=engine,
        variant=variant,
        multiplayer=multiplayer,
    )
