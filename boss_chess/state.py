from __future__ import annotations

from dataclasses import dataclass, field

import chess

from boss_chess.variants import GameVariant, create_board, normalize_variant


@dataclass
class GameState:
    starting_fen: str = chess.STARTING_FEN
    variant: str = GameVariant.STANDARD.value
    chess960_seed: int = 0
    board: chess.Board = field(init=False)
    move_history: list[chess.Move] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.board = create_board(self.variant, self.starting_fen, self.chess960_seed)

    def push(self, move: chess.Move) -> None:
        self.board.push(move)
        self.move_history.append(move)

    def pop(self) -> chess.Move | None:
        if not self.move_history:
            return None
        move = self.board.pop()
        self.move_history.pop()
        return move

    def reset(
        self,
        starting_fen: str | None = None,
        variant: str | GameVariant | None = None,
        chess960_seed: int | None = None,
    ) -> None:
        if starting_fen is not None:
            self.starting_fen = starting_fen
        if variant is not None:
            self.variant = normalize_variant(variant).value
        if chess960_seed is not None:
            self.chess960_seed = chess960_seed
        self.board = create_board(self.variant, self.starting_fen, self.chess960_seed)
        self.move_history.clear()
