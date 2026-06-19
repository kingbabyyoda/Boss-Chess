from __future__ import annotations

from dataclasses import dataclass, field

import chess


@dataclass
class GameState:
    board: chess.Board = field(default_factory=chess.Board)
    move_history: list[chess.Move] = field(default_factory=list)

    def push(self, move: chess.Move) -> None:
        self.board.push(move)
        self.move_history.append(move)

    def pop(self) -> chess.Move | None:
        if not self.move_history:
            return None
        move = self.board.pop()
        self.move_history.pop()
        return move
