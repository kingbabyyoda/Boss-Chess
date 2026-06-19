from __future__ import annotations

from dataclasses import dataclass

import chess

from boss_chess.engine.engine import ChessEngine


@dataclass(slots=True)
class Trainer:
    engine: ChessEngine

    def review_move(self, board_before: chess.Board, played_move: chess.Move) -> str:
        analysis = self.engine.analyse(board_before, max_lines=3)
        best = analysis.best_move
        if played_move == best:
            return f"Trainer: great move. {analysis.summary}"

        played_board = board_before.copy(stack=False)
        played_board.push(played_move)
        played_score = self.engine.score_position(played_board)
        best_score = analysis.best_score
        cpl = abs(best_score - played_score)
        accuracy = self.estimate_accuracy(cpl)

        verdict = self._verdict(cpl)
        details = [
            f"Trainer: best move was {best.uci()}.",
            f"Trainer: your move was {verdict}.",
            f"Trainer: estimated accuracy {accuracy:.0f}% | centipawn loss ~ {cpl}.",
            f"Trainer: {self._explain_move(board_before, played_move, best)}",
        ]
        if analysis.top_lines:
            lines = ", ".join(f"{move.uci()} ({score / 100:+.2f})" for move, score in analysis.top_lines)
            details.append(f"Trainer: top lines: {lines}")
        return "\n".join(details)

    def estimate_accuracy(self, centipawn_loss: int) -> float:
        if centipawn_loss <= 10:
            return 99.0
        if centipawn_loss <= 25:
            return 96.0
        if centipawn_loss <= 50:
            return 90.0
        if centipawn_loss <= 100:
            return 80.0
        if centipawn_loss <= 200:
            return 65.0
        return max(5.0, 65.0 - (centipawn_loss - 200) * 0.05)

    def _verdict(self, cpl: int) -> str:
        if cpl < 25:
            return "solid"
        if cpl < 75:
            return "an inaccuracy"
        if cpl < 150:
            return "a mistake"
        return "a blunder"

    def _explain_move(self, board: chess.Board, played: chess.Move, best: chess.Move) -> str:
        return (
            f"Best move {best.uci()} keeps the evaluation better. "
            f"Your move {played.uci()} {self._move_nature(board, played)}."
        )

    def _move_nature(self, board: chess.Board, move: chess.Move) -> str:
        parts: list[str] = []
        piece = board.piece_at(move.from_square)
        if piece:
            if piece.piece_type in (chess.KNIGHT, chess.BISHOP):
                parts.append("develops a minor piece")
            elif piece.piece_type == chess.PAWN:
                parts.append("claims space with a pawn")
            elif piece.piece_type == chess.ROOK:
                parts.append("activates a rook")
            elif piece.piece_type == chess.QUEEN:
                parts.append("moves the queen")
        if board.is_capture(move):
            parts.append("wins material")
        if board.gives_check(move):
            parts.append("gives check")
        if move.promotion:
            parts.append("promotes a pawn")
        return ", ".join(parts) or "keeps the position flexible"
