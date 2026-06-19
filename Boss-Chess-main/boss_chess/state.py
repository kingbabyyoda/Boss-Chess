from __future__ import annotations

from dataclasses import dataclass, field

import chess


@dataclass
class GameState:
    starting_fen: str = chess.STARTING_FEN
    board: chess.Board = field(init=False)
    move_history: list[chess.Move] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.board = chess.Board(self.starting_fen)

    def push(self, move: chess.Move) -> None:
        self.board.push(move)
        self.move_history.append(move)

    def pop(self) -> chess.Move | None:
        if not self.move_history:
            return None
        move = self.board.pop()
        self.move_history.pop()
        return move

    def reset(self, starting_fen: str | None = None) -> None:
        self.starting_fen = starting_fen or chess.STARTING_FEN
        self.board = chess.Board(self.starting_fen)
        self.move_history.clear()
