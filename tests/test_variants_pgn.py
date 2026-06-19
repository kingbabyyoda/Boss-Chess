from __future__ import annotations

from pathlib import Path

import chess

from boss_chess.replay import export_pgn, load_pgn
from boss_chess.state import GameState
from boss_chess.types import GameVariant


def test_pgn_round_trip_keeps_variant(tmp_path: Path) -> None:
    state = GameState(variant=GameVariant.KING_OF_THE_HILL.value)
    for uci in ["e2e4", "e7e5", "g1f3"]:
        move = chess.Move.from_uci(uci)
        if move in state.board.legal_moves:
            state.push(move)

    path = tmp_path / "variant_game.pgn"
    export_pgn(state, path)
    loaded = load_pgn(path)

    assert loaded.variant == GameVariant.KING_OF_THE_HILL.value
    assert loaded.move_history == state.move_history
