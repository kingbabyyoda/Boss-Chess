from __future__ import annotations

import random
from dataclasses import dataclass

import chess


def _position_key(board: chess.Board) -> str:
    # Ignore the halfmove/fullmove counters so the book can match the same
    # position reached through different move orders.
    return " ".join(board.fen().split(" ")[:4])


OPENING_BOOK: dict[str, list[str]] = {
    _position_key(chess.Board()): ["e2e4", "d2d4", "c2c4", "g1f3", "b1c3"],
    "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq -": ["e7e5", "c7c5", "e7e6", "c7c6", "g8f6"],
    "rnbqkbnr/pppppppp/8/8/3P4/8/PPP1PPPP/RNBQKBNR b KQkq -": ["d7d5", "g8f6", "e7e6", "c7c5"],
    "rnbqkbnr/pppppppp/8/8/2P5/8/PP1PPPPP/RNBQKBNR b KQkq -": ["e7e5", "g8f6", "c7c5", "e7e6"],
    "rnbqkbnr/pppp1ppp/4p3/8/4P3/8/PPPP1PPP/RNBQKBNR w KQkq -": ["g1f3", "d2d4", "f1b5", "b1c3"],
    "rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq -": ["g1f3", "f1c4", "d2d4", "b1c3"],
    "rnbqkbnr/pppp1ppp/8/8/4P3/5N2/PPPP1PPP/RNBQKB1R b KQkq -": ["b8c6", "g8f6", "d7d6", "f8e7"],
    "rnbqkb1r/pppppppp/5n2/8/4P3/8/PPPP1PPP/RNBQKBNR w KQkq -": ["b1c3", "d2d4", "f1c4", "g1f3"],
}


@dataclass(slots=True)
class OpeningBook:
    enabled: bool = True

    def position_key(self, board: chess.Board) -> str:
        return _position_key(board)

    def candidates_for_key(self, key: str) -> list[str]:
        return list(OPENING_BOOK.get(key, []))

    def choose_move(self, board: chess.Board) -> chess.Move | None:
        if not self.enabled:
            return None

        key = _position_key(board)
        candidates = OPENING_BOOK.get(key)
        if not candidates:
            return None

        legal = {move.uci() for move in board.legal_moves}
        legal_candidates = [move for move in candidates if move in legal]
        if not legal_candidates:
            return None
        return chess.Move.from_uci(random.choice(legal_candidates))

    def in_book(self, board: chess.Board) -> bool:
        return self.choose_move(board) is not None
