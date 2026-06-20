from __future__ import annotations

import os
from dataclasses import dataclass, field

import chess

from boss_chess.engine.opening_book import OpeningBook
from boss_chess.engine.search import Searcher, analyse_position, top_lines
from boss_chess.engine.stockfish import StockfishAdapter
from boss_chess.types import AnalysisResult


@dataclass(slots=True)
class ChessEngine:
    depth: int = 3
    use_stockfish: bool = False
    stockfish_path: str | None = None
    use_opening_book: bool = True
    target_elo: int = 1800
    multi_pv: int = 3
    searcher: Searcher = field(init=False)
    book: OpeningBook = field(init=False)
    stockfish: StockfishAdapter | None = field(init=False)

    def __post_init__(self) -> None:
        self.searcher = Searcher(depth=self.depth, tablebase_path=os.getenv("BOSS_CHESS_SYZYGY_PATH"))
        self.book = OpeningBook(enabled=self.use_opening_book)
        self.stockfish = None
        if self.use_stockfish:
            adapter = StockfishAdapter(
                path=self.stockfish_path,
                target_elo=self.target_elo,
                multi_pv=self.multi_pv,
                depth=self.depth,
            )
            if adapter.available():
                self.stockfish = adapter
            else:
                adapter.close()

    def close(self) -> None:
        if self.stockfish is not None:
            self.stockfish.close()
            self.stockfish = None

    def pick_move(self, board: chess.Board) -> chess.Move:
        book_move = self.book.choose_move(board)
        if book_move is not None:
            return book_move

        if self.stockfish is not None:
            stockfish_move = self.stockfish.choose_move(board)
            if stockfish_move is not None:
                return stockfish_move

        return self.searcher.choose_move(board)

    def analyse(self, board: chess.Board, max_lines: int = 3) -> AnalysisResult:
        line_count = max(1, min(max_lines, self.multi_pv))

        book_move = self.book.choose_move(board)
        if book_move is not None:
            candidates = self._book_top_lines(board, max_lines=line_count)
            return AnalysisResult(
                best_move=book_move,
                best_score=0,
                top_lines=candidates,
                summary="Opening book line.",
            )

        if self.stockfish is not None:
            result = self.stockfish.analyse(board, max_lines=line_count)
            if result is not None:
                return result

        bundle = analyse_position(board, depth=self.depth, max_lines=line_count)
        return AnalysisResult(
            best_move=bundle.best_move,
            best_score=bundle.best_score,
            top_lines=bundle.top_lines,
            summary=bundle.summary,
        )

    def top_lines(self, board: chess.Board, max_lines: int = 3) -> list[tuple[chess.Move, int]]:
        return self.analyse(board, max_lines=max_lines).top_lines

    def score_position(self, board: chess.Board) -> int:
        return self.searcher.score_position(board)

    def _book_top_lines(self, board: chess.Board, max_lines: int = 3) -> list[tuple[chess.Move, int]]:
        if not self.book.enabled:
            return []
        key = self.book.position_key(board)
        candidates = self.book.candidates_for_key(key)
        legal = {move.uci() for move in board.legal_moves}
        lines: list[tuple[chess.Move, int]] = []
        for index, move_text in enumerate(candidates):
            if move_text in legal:
                lines.append((chess.Move.from_uci(move_text), 10_000 - index * 100))
        return lines[:max_lines]
