from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import chess
import chess.pgn

from boss_chess.state import GameState
from boss_chess.types import GameVariant


@dataclass(slots=True)
class ReplaySummary:
    path: Path
    ply_count: int
    result: str


def export_pgn(state: GameState, path: Path, headers: dict[str, str] | None = None) -> ReplaySummary:
    path.parent.mkdir(parents=True, exist_ok=True)
    game = chess.pgn.Game()
    if headers:
        for key, value in headers.items():
            game.headers[key] = value
    game.headers["Variant"] = state.variant
    if state.variant == GameVariant.CHESS960.value:
        game.headers["Chess960Seed"] = str(state.chess960_seed)
    game.setup(chess.Board(state.starting_fen))
    node = game
    board = chess.Board(state.starting_fen)
    for move in state.move_history:
        node = node.add_variation(move)
        board.push(move)
    game.headers["Result"] = board.result(claim_draw=True)
    with path.open("w", encoding="utf-8") as handle:
        print(game, file=handle, end="\n\n")
    return ReplaySummary(path=path, ply_count=len(state.move_history), result=board.result(claim_draw=True))


def load_pgn(path: Path) -> GameState:
    with path.open("r", encoding="utf-8") as handle:
        game = chess.pgn.read_game(handle)
    if game is None:
        raise ValueError(f"No PGN game found in {path}")

    starting_fen = game.headers.get("FEN", chess.STARTING_FEN)
    variant = str(game.headers.get("Variant", GameVariant.STANDARD.value))
    chess960_seed = int(game.headers.get("Chess960Seed", 0) or 0)
    state = GameState(starting_fen=starting_fen, variant=variant, chess960_seed=chess960_seed)
    board = chess.Board(starting_fen)
    for move in game.mainline_moves():
        if move in board.legal_moves:
            state.push(move)
            board.push(move)
    return state
