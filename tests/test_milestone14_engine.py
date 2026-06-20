from __future__ import annotations

import chess

from boss_chess.engine.search import Searcher


def test_searcher_finds_forced_mate() -> None:
    board = chess.Board("7k/8/6KQ/8/8/8/8/8 w - - 0 1")
    searcher = Searcher(depth=2)

    best_move = searcher.choose_move(board)
    board.push(best_move)

    assert best_move == chess.Move.from_uci("h6g7")
    assert board.is_checkmate()
