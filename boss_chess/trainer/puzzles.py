from __future__ import annotations

from dataclasses import dataclass, field
import random

import chess

from boss_chess.trainer.motifs import TacticalMotifDetector
from boss_chess.trainer.openings import OpeningRecognizer
from boss_chess.trainer.report import PracticePrompt


@dataclass(slots=True)
class PuzzleGenerator:
    openings: OpeningRecognizer = field(default_factory=OpeningRecognizer)
    motifs: TacticalMotifDetector = field(default_factory=TacticalMotifDetector)

    def generate(self, board: chess.Board, side_to_move: chess.Color | None = None) -> PracticePrompt:
        side = side_to_move if side_to_move is not None else board.turn
        best_move = self._choose_target_move(board, side)
        theme = self._theme_for(board, best_move)
        clue = self._clue_for(board, best_move)
        explanation = self._explanation_for(board, best_move)
        return PracticePrompt(
            board_fen=board.fen(),
            side_to_move="white" if side == chess.WHITE else "black",
            target_move=best_move.uci(),
            theme=theme,
            clue=clue,
            explanation=explanation,
            opening_name=self.openings.identify(list(board.move_stack)),
        )

    def _choose_target_move(self, board: chess.Board, side: chess.Color) -> chess.Move:
        if board.turn != side:
            board = board.copy(stack=False)
        legal = list(board.legal_moves)
        if not legal:
            return chess.Move.null()

        tactical = [move for move in legal if self.motifs.detect(board, move).name not in {"Quiet move", "Positional move"}]
        if tactical:
            return random.choice(tactical)
        captures = [move for move in legal if board.is_capture(move)]
        if captures:
            return random.choice(captures)
        checks = [move for move in legal if board.gives_check(move)]
        if checks:
            return random.choice(checks)
        return random.choice(legal)

    def _theme_for(self, board: chess.Board, move: chess.Move) -> str:
        motif = self.motifs.detect(board, move)
        opening = self.openings.identify(list(board.move_stack))
        if motif.name != "Quiet move":
            return motif.name
        if "Opening" in opening or opening in {"Ruy Lopez", "Italian Game", "Queen's Gambit"}:
            return f"Opening ideas: {opening}"
        return "General calculation"

    def _clue_for(self, board: chess.Board, move: chess.Move) -> str:
        return self.motifs.detect(board, move).explanation

    def _explanation_for(self, board: chess.Board, move: chess.Move) -> str:
        piece = board.piece_at(move.from_square)
        if piece is None:
            return "Study the board and look for forcing moves."
        color = "White" if piece.color == chess.WHITE else "Black"
        return f"{color} to move should consider how {move.uci()} changes the tension."
