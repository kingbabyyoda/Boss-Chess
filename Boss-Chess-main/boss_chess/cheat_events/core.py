from __future__ import annotations

import random
from dataclasses import dataclass, field

import chess


@dataclass(slots=True)
class CheatController:
    last_event: str = "The board is behaving suspiciously."
    extra_turns: int = 0
    chaos_level: int = 0
    captured_white: list[chess.PieceType] = field(default_factory=list)
    captured_black: list[chess.PieceType] = field(default_factory=list)
    event_log: list[str] = field(default_factory=list)

    def note_capture(self, piece: chess.Piece | None) -> None:
        if piece is None:
            return
        if piece.color == chess.WHITE:
            self.captured_white.append(piece.piece_type)
        else:
            self.captured_black.append(piece.piece_type)

    def to_dict(self) -> dict[str, object]:
        return {
            "last_event": self.last_event,
            "extra_turns": self.extra_turns,
            "chaos_level": self.chaos_level,
            "captured_white": [int(piece_type) for piece_type in self.captured_white],
            "captured_black": [int(piece_type) for piece_type in self.captured_black],
            "event_log": list(self.event_log),
        }

    @classmethod
    def from_dict(cls, data: dict[str, object] | None) -> "CheatController":
        if not isinstance(data, dict):
            return cls()
        controller = cls()
        controller.last_event = str(data.get("last_event", controller.last_event))
        controller.extra_turns = int(data.get("extra_turns", 0))
        controller.chaos_level = int(data.get("chaos_level", 0))
        controller.captured_white = [chess.PieceType(int(v)) for v in data.get("captured_white", []) if isinstance(v, int) or str(v).isdigit()]
        controller.captured_black = [chess.PieceType(int(v)) for v in data.get("captured_black", []) if isinstance(v, int) or str(v).isdigit()]
        controller.event_log = [str(item) for item in data.get("event_log", []) if item is not None]
        return controller

    def apply(self, board: chess.Board, ai_color: chess.Color) -> None:
        self.chaos_level += 1
        roll = random.random()
        weights = [
            (0.15, self._delete_enemy_piece),
            (0.30, self._teleport_piece),
            (0.45, self._spawn_piece),
            (0.60, self._duplicate_piece),
            (0.74, self._resurrect_piece),
            (0.84, self._grant_extra_turn),
            (0.92, self._reality_rewrite),
            (1.00, self._boss_phase),
        ]
        for cutoff, event in weights:
            if roll <= cutoff:
                event(board, ai_color)
                self.event_log.append(self.last_event)
                self.event_log = self.event_log[-12:]
                return

    def _enemy_squares(self, board: chess.Board, ai_color: chess.Color) -> list[int]:
        return [sq for sq, piece in board.piece_map().items() if piece.color != ai_color and piece.piece_type != chess.KING]

    def _ai_squares(self, board: chess.Board, ai_color: chess.Color) -> list[int]:
        return [sq for sq, piece in board.piece_map().items() if piece.color == ai_color and piece.piece_type != chess.KING]

    def _empty_squares(self, board: chess.Board) -> list[int]:
        return [sq for sq in chess.SQUARES if board.piece_at(sq) is None]

    def _delete_enemy_piece(self, board: chess.Board, ai_color: chess.Color) -> None:
        squares = self._enemy_squares(board, ai_color)
        if not squares:
            return
        sq = random.choice(squares)
        piece = board.piece_at(sq)
        board.remove_piece_at(sq)
        self.note_capture(piece)
        self.last_event = f"Reality deleted {chess.square_name(sq)}."

    def _teleport_piece(self, board: chess.Board, ai_color: chess.Color) -> None:
        own = self._ai_squares(board, ai_color)
        empty = self._empty_squares(board)
        if not own or not empty:
            return
        from_sq = random.choice(own)
        to_sq = random.choice(empty)
        piece = board.piece_at(from_sq)
        board.remove_piece_at(from_sq)
        board.set_piece_at(to_sq, piece)
        self.last_event = f"A piece teleported from {chess.square_name(from_sq)} to {chess.square_name(to_sq)}."

    def _spawn_piece(self, board: chess.Board, ai_color: chess.Color) -> None:
        empty = self._empty_squares(board)
        if not empty:
            return
        sq = random.choice(empty)
        piece_type = random.choice([chess.PAWN, chess.KNIGHT, chess.BISHOP, chess.ROOK, chess.QUEEN])
        board.set_piece_at(sq, chess.Piece(piece_type, ai_color))
        self.last_event = f"A forged piece spawned on {chess.square_name(sq)}."

    def _duplicate_piece(self, board: chess.Board, ai_color: chess.Color) -> None:
        own = self._ai_squares(board, ai_color)
        empty = self._empty_squares(board)
        if not own or not empty:
            return
        source = random.choice(own)
        target = random.choice(empty)
        piece = board.piece_at(source)
        if piece is None:
            return
        board.set_piece_at(target, chess.Piece(piece.piece_type, piece.color))
        self.last_event = f"The board cloned {piece.symbol()} to {chess.square_name(target)}."

    def _resurrect_piece(self, board: chess.Board, ai_color: chess.Color) -> None:
        pool = self.captured_white if ai_color == chess.WHITE else self.captured_black
        if not pool:
            return
        empty = self._empty_squares(board)
        if not empty:
            return
        sq = random.choice(empty)
        piece_type = random.choice(pool)
        board.set_piece_at(sq, chess.Piece(piece_type, ai_color))
        self.last_event = f"A captured piece returned at {chess.square_name(sq)}."

    def _grant_extra_turn(self, *_args) -> None:
        self.extra_turns += 1
        if self.chaos_level >= 3:
            self.extra_turns += 1
        self.last_event = "The AI stole an extra turn."

    def _reality_rewrite(self, board: chess.Board, ai_color: chess.Color) -> None:
        pieces = list(board.piece_map().items())
        if len(pieces) < 2:
            return
        (sq1, p1), (sq2, p2) = random.sample(pieces, 2)
        board.set_piece_at(sq1, p2)
        board.set_piece_at(sq2, p1)
        self.last_event = f"Reality rewrote itself between {chess.square_name(sq1)} and {chess.square_name(sq2)}."

    def _boss_phase(self, board: chess.Board, ai_color: chess.Color) -> None:
        # Escalate into a nastier phase: spawn a queen, grant a turn, and delete a random enemy piece.
        self.chaos_level += 2
        self._spawn_piece(board, ai_color)
        self._grant_extra_turn()
        self._delete_enemy_piece(board, ai_color)
        self.last_event = f"Boss phase {min(3, 1 + self.chaos_level // 4)} activated. The board is collapsing."
