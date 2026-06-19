from __future__ import annotations

from dataclasses import dataclass

import chess


@dataclass(slots=True)
class OpeningMatch:
    name: str
    line: list[str]


OPENINGS: list[OpeningMatch] = [
    OpeningMatch("King's Pawn Opening", ["e2e4"]),
    OpeningMatch("Queen's Pawn Opening", ["d2d4"]),
    OpeningMatch("English Opening", ["c2c4"]),
    OpeningMatch("Reti Opening", ["g1f3", "d2d4"]),
    OpeningMatch("Italian Game", ["e2e4", "e7e5", "g1f3", "b8c6", "f1c4"]),
    OpeningMatch("Ruy Lopez", ["e2e4", "e7e5", "g1f3", "b8c6", "f1b5"]),
    OpeningMatch("Sicilian Defense", ["e2e4", "c7c5"]),
    OpeningMatch("French Defense", ["e2e4", "e7e6"]),
    OpeningMatch("Caro-Kann Defense", ["e2e4", "c7c6"]),
    OpeningMatch("Queen's Gambit", ["d2d4", "d7d5", "c2c4"]),
    OpeningMatch("Slav Defense", ["d2d4", "d7d5", "c2c4", "c7c6"]),
]


class OpeningRecognizer:
    def identify(self, moves: list[chess.Move]) -> str:
        uci_moves = [move.uci() for move in moves]
        best_name = "Unclassified opening"
        best_len = 0
        for opening in OPENINGS:
            if uci_moves[: len(opening.line)] == opening.line and len(opening.line) > best_len:
                best_name = opening.name
                best_len = len(opening.line)
        return best_name

    def suggest_plan(self, board: chess.Board) -> str:
        name = self.identify(list(board.move_stack))
        if name == "Unclassified opening":
            return "Develop pieces, castle, and fight for the center."
        if name == "King's Pawn Opening":
            return "Claim the center and develop quickly behind the pawn chain."
        if name == "Queen's Pawn Opening":
            return "Build a sturdy center and prepare c-pawn pressure."
        if name == "Ruy Lopez":
            return "Pressure the e5 pawn, castle early, and prepare the bishop pair."
        if name == "Italian Game":
            return "Use quick development to attack f7 and keep the initiative."
        if name == "Queen's Gambit":
            return "Use the c-pawn pressure to control the center and gain space."
        return f"Follow the ideas of {name}: develop, castle, and watch the central tension."
