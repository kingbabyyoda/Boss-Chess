from __future__ import annotations

import chess

PIECE_VALUES = {
    chess.PAWN: 100,
    chess.KNIGHT: 320,
    chess.BISHOP: 330,
    chess.ROOK: 500,
    chess.QUEEN: 900,
    chess.KING: 0,
}


def evaluate_board(board: chess.Board) -> int:
    if board.is_checkmate():
        return -100000 if board.turn == chess.WHITE else 100000
    if board.is_stalemate() or board.is_insufficient_material() or board.can_claim_draw():
        return 0

    score = 0
    for _, piece in board.piece_map().items():
        value = PIECE_VALUES[piece.piece_type]
        score += value if piece.color == chess.WHITE else -value

    score += _mobility(board)
    score += _piece_activity(board)
    score += _king_safety(board)
    return score


def _mobility(board: chess.Board) -> int:
    turn = board.turn
    my_moves = board.legal_moves.count()
    board.turn = not turn
    try:
        opp_moves = board.legal_moves.count()
    finally:
        board.turn = turn
    delta = my_moves - opp_moves
    return delta * (2 if board.turn == chess.WHITE else -2)


def _piece_activity(board: chess.Board) -> int:
    score = 0
    for square, piece in board.piece_map().items():
        rank = chess.square_rank(square)
        if piece.piece_type in (chess.KNIGHT, chess.BISHOP) and rank not in (0, 7):
            score += 8 if piece.color == chess.WHITE else -8
    return score


def _king_safety(board: chess.Board) -> int:
    score = 0
    for color in (chess.WHITE, chess.BLACK):
        king = board.king(color)
        if king is None:
            continue
        attackers = len(board.attackers(not color, king))
        local = -25 * attackers
        score += local if color == chess.WHITE else -local
    return score
