from __future__ import annotations

from dataclasses import dataclass

import chess

from boss_chess.engine.search import choose_move, top_lines


@dataclass
class ChessEngine:
    depth: int = 3

    def pick_move(self, board: chess.Board) -> chess.Move:
        return choose_move(board, depth=self.depth)

    def analyse(self, board: chess.Board, max_lines: int = 3) -> list[tuple[chess.Move, int]]:
        return top_lines(board, depth=self.depth, max_lines=max_lines)
