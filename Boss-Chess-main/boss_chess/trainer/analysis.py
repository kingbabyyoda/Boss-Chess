from __future__ import annotations

from dataclasses import dataclass

import chess

from boss_chess.engine.engine import ChessEngine


@dataclass
class Trainer:
    engine: ChessEngine

    def review_move(self, board_before: chess.Board, played_move: chess.Move) -> str:
        best = self.engine.pick_move(board_before.copy(stack=False))
        if played_move == best:
            return "Trainer: great move. That was the engine choice."

        return f"Trainer: best move was {best.uci()}."

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
