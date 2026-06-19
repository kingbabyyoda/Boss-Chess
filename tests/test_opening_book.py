from __future__ import annotations

import chess

from boss_chess.engine.engine import ChessEngine
from boss_chess.engine.opening_book import OpeningBook


def test_opening_book_returns_legal_start_move() -> None:
    board = chess.Board()
    book = OpeningBook(enabled=True)
    move = book.choose_move(board)
    assert move is not None
    assert move in board.legal_moves


def test_engine_uses_opening_book_on_start_position() -> None:
    board = chess.Board()
    engine = ChessEngine(depth=2, use_opening_book=True, use_stockfish=False)
    move = engine.pick_move(board)
    assert move.uci() in {"e2e4", "d2d4", "c2c4", "g1f3", "b1c3"}
