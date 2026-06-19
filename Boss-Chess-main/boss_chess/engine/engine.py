from __future__ import annotations

from dataclasses import dataclass, field

import chess

from boss_chess.engine.search import Searcher, analyse_position, top_lines
from boss_chess.types import AnalysisResult


@dataclass(slots=True)
class ChessEngine:
    depth: int = 3
    searcher: Searcher = field(init=False)

    def __post_init__(self) -> None:
        self.searcher = Searcher(depth=self.depth)

    def pick_move(self, board: chess.Board) -> chess.Move:
        return self.searcher.choose_move(board)

    def analyse(self, board: chess.Board, max_lines: int = 3) -> AnalysisResult:
        bundle = analyse_position(board, depth=self.depth, max_lines=max_lines)
        return AnalysisResult(
            best_move=bundle.best_move,
            best_score=bundle.best_score,
            top_lines=bundle.top_lines,
            summary=bundle.summary,
        )

    def top_lines(self, board: chess.Board, max_lines: int = 3) -> list[tuple[chess.Move, int]]:
        return top_lines(board, depth=self.depth, max_lines=max_lines)

    def score_position(self, board: chess.Board) -> int:
        return self.searcher.score_position(board)
