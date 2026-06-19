from __future__ import annotations

import math
import random

import chess

from boss_chess.engine.evaluation import evaluate_board

INF = 10**9


def choose_move(board: chess.Board, depth: int = 3) -> chess.Move:
    legal_moves = list(board.legal_moves)
    if not legal_moves:
        raise ValueError("No legal moves available.")

    random.shuffle(legal_moves)
    ordered = sorted(legal_moves, key=lambda m: _move_priority(board, m), reverse=True)

    best_move = ordered[0]
    best_score = -INF if board.turn == chess.WHITE else INF

    for move in ordered:
        board.push(move)
        score = _negamax(board, depth - 1, -INF, INF, -1)
        board.pop()

        if board.turn == chess.WHITE and score > best_score:
            best_score = score
            best_move = move
        elif board.turn == chess.BLACK and score < best_score:
            best_score = score
            best_move = move

    return best_move


def top_lines(board: chess.Board, depth: int = 3, max_lines: int = 3) -> list[tuple[chess.Move, int]]:
    scored: list[tuple[chess.Move, int]] = []
    for move in board.legal_moves:
        board.push(move)
        score = -_negamax(board, depth - 1, -INF, INF, -1)
        board.pop()
        scored.append((move, score))
    scored.sort(key=lambda item: item[1], reverse=board.turn == chess.WHITE)
    return scored[:max_lines]


def _negamax(board: chess.Board, depth: int, alpha: int, beta: int, color: int) -> int:
    if board.is_checkmate():
        return -100000 + depth
    if board.is_stalemate() or board.is_insufficient_material() or board.can_claim_draw():
        return 0
    if depth <= 0:
        return color * evaluate_board(board)

    best = -INF
    moves = list(board.legal_moves)
    moves.sort(key=lambda m: _move_priority(board, m), reverse=True)

    for move in moves:
        board.push(move)
        score = -_negamax(board, depth - 1, -beta, -alpha, -color)
        board.pop()
        if score > best:
            best = score
        if score > alpha:
            alpha = score
        if alpha >= beta:
            break

    return best


def _move_priority(board: chess.Board, move: chess.Move) -> int:
    score = 0
    if board.is_capture(move):
        captured = board.piece_at(move.to_square)
        if captured:
            score += 10 * _piece_value(captured.piece_type)
    if move.promotion:
        score += 1000 + _piece_value(move.promotion)
    if board.gives_check(move):
        score += 80
    return score


def _piece_value(piece_type: chess.PieceType) -> int:
    return {
        chess.PAWN: 100,
        chess.KNIGHT: 320,
        chess.BISHOP: 330,
        chess.ROOK: 500,
        chess.QUEEN: 900,
        chess.KING: 0,
    }[piece_type]
