from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import chess

from boss_chess.cheat_events.core import CheatController
from boss_chess.state import GameState
from boss_chess.types import EngineConfig, GameConfig


@dataclass(slots=True)
class SavedGame:
    version: int
    created_at: str
    fen: str
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
        version=1,
        created_at=datetime.now(timezone.utc).isoformat(),
        fen=state.board.fen(),
        moves=[move.uci() for move in state.move_history],
        config=_config_to_dict(config),
        ai_color="white" if ai_color == chess.WHITE else "black",
        cheat=cheat.to_dict(),
    )
    path.write_text(json.dumps(asdict(payload), indent=2, sort_keys=True), encoding="utf-8")


def load_game(path: Path) -> LoadedGame:
    data = json.loads(path.read_text(encoding="utf-8"))

    config = _config_from_dict(data.get("config", {}))
    state = GameState()
    state.board = chess.Board(data.get("fen", chess.STARTING_FEN))
    state.move_history = []
    for move_text in data.get("moves", []):
        try:
            move = chess.Move.from_uci(move_text)
        except ValueError:
            continue
        if move in state.board.legal_moves:
            state.board.push(move)
            state.move_history.append(move)

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
        },
    }


def _config_from_dict(data: dict[str, Any]) -> GameConfig:
    engine_data = data.get("engine", {}) if isinstance(data, dict) else {}
    engine = EngineConfig(
        depth=int(engine_data.get("depth", 3)),
        use_stockfish=bool(engine_data.get("use_stockfish", False)),
        stockfish_path=engine_data.get("stockfish_path"),
    )
    return GameConfig(
        ai_plays_white=bool(data.get("ai_plays_white", False)),
        trainer=bool(data.get("trainer", False)),
        meme=bool(data.get("meme", False)),
        cheat=bool(data.get("cheat", False)),
        engine=engine,
    )
