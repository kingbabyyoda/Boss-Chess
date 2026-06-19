from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import chess

from boss_chess.trainer.motifs import MotifResult


@dataclass(slots=True)
class MoveReview:
    move: chess.Move
    best_move: chess.Move | None
    centipawn_loss: int
    accuracy: float
    verdict: str
    motif: MotifResult
    opening_name: str
    explanation: str


@dataclass(slots=True)
class GameReport:
    opening_name: str
    move_count: int
    average_accuracy: float
    average_centipawn_loss: float
    best_move_count: int
    inaccuracies: int
    mistakes: int
    blunders: int
    motifs: dict[str, int] = field(default_factory=dict)
    highlights: list[str] = field(default_factory=list)

    def summary_lines(self) -> list[str]:
        lines = [
            f"Opening: {self.opening_name}",
            f"Moves reviewed: {self.move_count}",
            f"Average accuracy: {self.average_accuracy:.1f}%",
            f"Average centipawn loss: {self.average_centipawn_loss:.1f}",
            f"Best moves played: {self.best_move_count}",
            f"Inaccuracies / mistakes / blunders: {self.inaccuracies} / {self.mistakes} / {self.blunders}",
        ]
        if self.motifs:
            motif_bits = ", ".join(f"{name}: {count}" for name, count in sorted(self.motifs.items(), key=lambda item: (-item[1], item[0])))
            lines.append(f"Common motifs: {motif_bits}")
        lines.extend(self.highlights[:5])
        return lines


@dataclass(slots=True)
class PracticePrompt:
    board_fen: str
    side_to_move: str
    target_move: str
    theme: str
    clue: str
    explanation: str
    opening_name: str = "Unknown"

    def as_dict(self) -> dict[str, Any]:
        return {
            "board_fen": self.board_fen,
            "side_to_move": self.side_to_move,
            "target_move": self.target_move,
            "theme": self.theme,
            "clue": self.clue,
            "explanation": self.explanation,
            "opening_name": self.opening_name,
        }
