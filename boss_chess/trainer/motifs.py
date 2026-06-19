from __future__ import annotations

from dataclasses import dataclass

import chess


@dataclass(slots=True)
class MotifResult:
    name: str
    explanation: str


class TacticalMotifDetector:
    def detect(self, board: chess.Board, move: chess.Move) -> MotifResult:
        piece = board.piece_at(move.from_square)
        if piece is None:
            return MotifResult("Quiet move", "The move improves coordination without an obvious tactical shot.")

        captures = board.is_capture(move)
        gives_check = board.gives_check(move)
        if captures and gives_check:
            return MotifResult("Check-and-capture", "The move wins material while keeping the king under pressure.")

        if self._is_fork(board, move):
            return MotifResult("Fork", "The move attacks two or more valuable targets at once.")
        if self._is_discovered_attack(board, move):
            return MotifResult("Discovered attack", "Moving this piece uncovers a stronger attack behind it.")
        if self._is_pin(board, move):
            return MotifResult("Pin", "The move pins a piece to the king or queen and restricts it.")
        if self._is_skewer(board, move):
            return MotifResult("Skewer", "The move attacks a more valuable piece so a lesser piece must move.")
        if captures:
            return MotifResult("Capture", "The move wins material or improves the piece balance.")
        if gives_check:
            return MotifResult("Check", "The move forces the king to react and narrows the opponent's choices.")
        return MotifResult("Positional move", "The move improves the position without an immediate tactical shot.")

    def _is_fork(self, board: chess.Board, move: chess.Move) -> bool:
        piece = board.piece_at(move.from_square)
        if piece is None:
            return False
        if piece.piece_type not in {chess.KNIGHT, chess.PAWN, chess.BISHOP, chess.ROOK, chess.QUEEN}:
            return False
        attack_board = board.copy(stack=False)
        attack_board.push(move)
        attacked = list(attack_board.attacks(move.to_square))
        return len(attacked) >= 2

    def _is_discovered_attack(self, board: chess.Board, move: chess.Move) -> bool:
        piece = board.piece_at(move.from_square)
        if piece is None:
            return False
        if piece.piece_type not in {chess.BISHOP, chess.ROOK, chess.QUEEN, chess.KNIGHT, chess.PAWN}:
            return False
        for square, attacker in board.piece_map().items():
            if attacker.color != piece.color or square == move.from_square:
                continue
            if attacker.piece_type in {chess.BISHOP, chess.ROOK, chess.QUEEN}:
                if board.is_pinned(piece.color, move.from_square):
                    return True
        return False

    def _is_pin(self, board: chess.Board, move: chess.Move) -> bool:
        target = board.piece_at(move.to_square)
        if target is None or target.color == board.turn:
            return False
        if target.piece_type == chess.KING:
            return False
        board_after = board.copy(stack=False)
        board_after.push(move)
        return board_after.is_attacked_by(board.turn, move.to_square)

    def _is_skewer(self, board: chess.Board, move: chess.Move) -> bool:
        piece = board.piece_at(move.from_square)
        if piece is None:
            return False
        if piece.piece_type not in {chess.BISHOP, chess.ROOK, chess.QUEEN}:
            return False
        return board.is_check() or board.gives_check(move)
