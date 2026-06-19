from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import chess

from boss_chess.engine.evaluation import MATE_SCORE, evaluate_board

INF = 10**9


@dataclass(slots=True)
class TTEntry:
    depth: int
    score: int
    flag: str  # exact, lower, upper
    best_move: Optional[chess.Move]


class Searcher:
    def __init__(self, depth: int = 3) -> None:
        self.depth = max(1, depth)
        self.tt: dict[object, TTEntry] = {}
        self.nodes = 0

    def choose_move(self, board: chess.Board) -> chess.Move:
        result = self.analyse(board, max_lines=1)
        if result.best_move is None:
            legal = list(board.legal_moves)
            if not legal:
                raise ValueError("No legal moves available.")
            return legal[0]
        return result.best_move

    def analyse(self, board: chess.Board, max_lines: int = 3):
        legal_moves = list(board.legal_moves)
        if not legal_moves:
            raise ValueError("No legal moves available.")

        color = 1 if board.turn == chess.WHITE else -1
        scored: list[tuple[chess.Move, int]] = []
        ordered = self._order_moves(board, legal_moves, None)
        alpha = -INF
        beta = INF
        for move in ordered:
            board.push(move)
            score = -self._negamax(board, self.depth - 1, -beta, -alpha, -color, ply=1)
            board.pop()
            scored.append((move, score))
            if score > alpha:
                alpha = score

        scored.sort(key=lambda item: item[1], reverse=True)
        best_move, best_score = scored[0]
        top_lines = scored[:max_lines]
        return _AnalysisBundle(
            best_move=best_move,
            best_score=best_score,
            top_lines=top_lines,
            summary=_format_summary(best_score, board.turn),
        )

    def score_position(self, board: chess.Board) -> int:
        color = 1 if board.turn == chess.WHITE else -1
        return color * evaluate_board(board)

    def _negamax(self, board: chess.Board, depth: int, alpha: int, beta: int, color: int, ply: int) -> int:
        self.nodes += 1

        if board.is_checkmate():
            return -MATE_SCORE + ply
        if board.is_stalemate() or board.is_insufficient_material() or board.can_claim_draw():
            return 0

        key = self._key(board)
        entry = self.tt.get(key)
        if entry and entry.depth >= depth:
            if entry.flag == "exact":
                return entry.score
            if entry.flag == "lower":
                alpha = max(alpha, entry.score)
            elif entry.flag == "upper":
                beta = min(beta, entry.score)
            if alpha >= beta:
                return entry.score

        if depth <= 0:
            return self._quiescence(board, alpha, beta, color, ply)

        legal_moves = list(board.legal_moves)
        if not legal_moves:
            return color * evaluate_board(board)

        hash_move = entry.best_move if entry else None
        moves = self._order_moves(board, legal_moves, hash_move)

        best_score = -INF
        best_move: Optional[chess.Move] = None
        original_alpha = alpha

        for move in moves:
            board.push(move)
            score = -self._negamax(board, depth - 1, -beta, -alpha, -color, ply + 1)
            board.pop()

            if score > best_score:
                best_score = score
                best_move = move
            if score > alpha:
                alpha = score
            if alpha >= beta:
                break

        flag = "exact"
        if best_score <= original_alpha:
            flag = "upper"
        elif best_score >= beta:
            flag = "lower"
        self.tt[key] = TTEntry(depth=depth, score=best_score, flag=flag, best_move=best_move)
        return best_score

    def _quiescence(self, board: chess.Board, alpha: int, beta: int, color: int, ply: int) -> int:
        stand_pat = color * evaluate_board(board)
        if stand_pat >= beta:
            return beta
        if stand_pat > alpha:
            alpha = stand_pat

        tactical_moves = [move for move in board.legal_moves if board.is_capture(move) or board.gives_check(move)]
        tactical_moves.sort(key=lambda move: self._move_order_score(board, move), reverse=True)
        for move in tactical_moves:
            board.push(move)
            score = -self._quiescence(board, -beta, -alpha, -color, ply + 1)
            board.pop()
            if score >= beta:
                return beta
            if score > alpha:
                alpha = score
        return alpha

    def _order_moves(
        self,
        board: chess.Board,
        moves: list[chess.Move],
        hash_move: Optional[chess.Move],
    ) -> list[chess.Move]:
        if hash_move is not None and hash_move in moves:
            remaining = [move for move in moves if move != hash_move]
            remaining.sort(key=lambda move: self._move_order_score(board, move), reverse=True)
            return [hash_move, *remaining]
        return sorted(moves, key=lambda move: self._move_order_score(board, move), reverse=True)

    def _move_order_score(self, board: chess.Board, move: chess.Move) -> int:
        score = 0
        if board.is_capture(move):
            victim = board.piece_at(move.to_square)
            attacker = board.piece_at(move.from_square)
            if victim:
                score += 10 * _piece_value(victim.piece_type)
            if attacker:
                score -= _piece_value(attacker.piece_type)
        if move.promotion:
            score += 1000 + _piece_value(move.promotion)
        if board.gives_check(move):
            score += 80
        moved = board.piece_at(move.from_square)
        if moved and moved.piece_type in (chess.KNIGHT, chess.BISHOP) and chess.square_rank(move.from_square) in (0, 7):
            score += 15
        return score

    def _key(self, board: chess.Board) -> object:
        key_fn = getattr(board, "_transposition_key", None)
        if callable(key_fn):
            try:
                return key_fn()
            except Exception:
                pass
        return board.fen()


@dataclass(slots=True)
class _AnalysisBundle:
    best_move: chess.Move
    best_score: int
    top_lines: list[tuple[chess.Move, int]]
    summary: str


def choose_move(board: chess.Board, depth: int = 3) -> chess.Move:
    return Searcher(depth=depth).choose_move(board)


def top_lines(board: chess.Board, depth: int = 3, max_lines: int = 3) -> list[tuple[chess.Move, int]]:
    return Searcher(depth=depth).analyse(board, max_lines=max_lines).top_lines


def analyse_position(board: chess.Board, depth: int = 3, max_lines: int = 3):
    return Searcher(depth=depth).analyse(board, max_lines=max_lines)


def _piece_value(piece_type: chess.PieceType) -> int:
    return {
        chess.PAWN: 100,
        chess.KNIGHT: 320,
        chess.BISHOP: 330,
        chess.ROOK: 500,
        chess.QUEEN: 900,
        chess.KING: 0,
    }[piece_type]


def _format_summary(score: int, turn: chess.Color) -> str:
    if abs(score) >= MATE_SCORE // 2:
        return "Forced mate is on the board."
    side = "White" if score > 0 else "Black"
    strength = abs(score) / 100
    if strength < 0.25:
        return "Position is roughly equal."
    if strength < 1.0:
        return f"Small edge for {side.lower()} ({score / 100:+.2f})."
    return f"Strong edge for {side.lower()} ({score / 100:+.2f})."
