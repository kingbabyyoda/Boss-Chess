from __future__ import annotations

import random

import chess


class CheatController:
    def __init__(self) -> None:
        self.last_event = "The board is behaving suspiciously."
        self.extra_turns = 0
        self.captured_white: list[chess.PieceType] = []
        self.captured_black: list[chess.PieceType] = []

    def note_capture(self, piece: chess.Piece | None) -> None:
        if piece is None:
            return
        if piece.color == chess.WHITE:
            self.captured_white.append(piece.piece_type)
        else:
            self.captured_black.append(piece.piece_type)

    def apply(self, board: chess.Board, ai_color: chess.Color) -> None:
        roll = random.random()
        if roll < 0.20:
            self._delete_enemy_piece(board, ai_color)
        elif roll < 0.40:
            self._teleport_piece(board, ai_color)
        elif roll < 0.60:
            self._spawn_piece(board, ai_color)
        elif roll < 0.75:
            self._resurrect_piece(board, ai_color)
        elif roll < 0.88:
            self._grant_extra_turn()
        else:
            self._reality_rewrite(board)

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

    def _grant_extra_turn(self) -> None:
        self.extra_turns += 1
        self.last_event = "The AI stole an extra turn."

    def _reality_rewrite(self, board: chess.Board) -> None:
        pieces = list(board.piece_map().items())
        if len(pieces) < 2:
            return
        (sq1, p1), (sq2, p2) = random.sample(pieces, 2)
        board.set_piece_at(sq1, p2)
        board.set_piece_at(sq2, p1)
        self.last_event = f"Reality rewrote itself between {chess.square_name(sq1)} and {chess.square_name(sq2)}."
