from __future__ import annotations

from dataclasses import dataclass, field

import chess

from boss_chess.trainer.openings import OpeningRecognizer
from boss_chess.trainer.puzzles import PuzzleGenerator
from boss_chess.trainer.report import PracticePrompt


@dataclass(slots=True)
class PracticeMode:
    puzzle_generator: PuzzleGenerator = field(default_factory=PuzzleGenerator)
    opening_recognizer: OpeningRecognizer = field(default_factory=OpeningRecognizer)

    def next_prompt(self, board: chess.Board, side_to_move: chess.Color | None = None) -> PracticePrompt:
        side = side_to_move if side_to_move is not None else board.turn
        return self.puzzle_generator.generate(board, side_to_move=side)

    def lesson_text(self, board: chess.Board) -> str:
        opening = self.opening_recognizer.identify(list(board.move_stack))
        plan = self.opening_recognizer.suggest_plan(board)
        puzzle = self.puzzle_generator.generate(board)
        return "\n".join(
            [
                f"Opening: {opening}",
                f"Plan: {plan}",
                f"Practice puzzle: {puzzle.theme} | {puzzle.clue}",
                f"Target move: {puzzle.target_move}",
            ]
        )
