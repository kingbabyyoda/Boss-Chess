from __future__ import annotations

import chess

MATE_SCORE = 100000

PIECE_VALUES = {
    chess.PAWN: 100,
    chess.KNIGHT: 320,
    chess.BISHOP: 330,
    chess.ROOK: 500,
    chess.QUEEN: 900,
    chess.KING: 0,
}

PAWN_PST = [
      0,   0,   0,   0,   0,   0,   0,   0,
     50,  50,  50,  50,  50,  50,  50,  50,
     10,  10,  20,  30,  30,  20,  10,  10,
      5,   5,  10,  25,  25,  10,   5,   5,
      0,   0,   0,  20,  20,   0,   0,   0,
      5,  -5, -10,   0,   0, -10,  -5,   5,
      5,  10,  10, -20, -20,  10,  10,   5,
      0,   0,   0,   0,   0,   0,   0,   0,
]
KNIGHT_PST = [
    -50, -40, -30, -30, -30, -30, -40, -50,
    -40, -20,   0,   0,   0,   0, -20, -40,
    -30,   0,  10,  15,  15,  10,   0, -30,
    -30,   5,  15,  20,  20,  15,   5, -30,
    -30,   0,  15,  20,  20,  15,   0, -30,
    -30,   5,  10,  15,  15,  10,   5, -30,
    -40, -20,   0,   5,   5,   0, -20, -40,
    -50, -40, -30, -30, -30, -30, -40, -50,
]
BISHOP_PST = [
    -20, -10, -10, -10, -10, -10, -10, -20,
    -10,   0,   0,   0,   0,   0,   0, -10,
    -10,   0,   5,  10,  10,   5,   0, -10,
    -10,   5,   5,  10,  10,   5,   5, -10,
    -10,   0,  10,  10,  10,  10,   0, -10,
    -10,  10,  10,  10,  10,  10,  10, -10,
    -10,   5,   0,   0,   0,   0,   5, -10,
    -20, -10, -10, -10, -10, -10, -10, -20,
]
ROOK_PST = [
      0,   0,   0,   5,   5,   0,   0,   0,
     -5,   0,   0,   0,   0,   0,   0,  -5,
     -5,   0,   0,   0,   0,   0,   0,  -5,
     -5,   0,   0,   0,   0,   0,   0,  -5,
     -5,   0,   0,   0,   0,   0,   0,  -5,
     -5,   0,   0,   0,   0,   0,   0,  -5,
      5,  10,  10,  10,  10,  10,  10,   5,
      0,   0,   0,   0,   0,   0,   0,   0,
]
QUEEN_PST = [
    -20, -10, -10,  -5,  -5, -10, -10, -20,
    -10,   0,   0,   0,   0,   5,   0, -10,
    -10,   0,   5,   5,   5,   5,   5, -10,
     -5,   0,   5,   5,   5,   5,   0,  -5,
      0,   0,   5,   5,   5,   5,   0,  -5,
    -10,   5,   5,   5,   5,   5,   0, -10,
    -10,   0,   5,   0,   0,   0,   0, -10,
    -20, -10, -10,  -5,  -5, -10, -10, -20,
]
KING_MID_PST = [
    -30, -40, -40, -50, -50, -40, -40, -30,
    -30, -40, -40, -50, -50, -40, -40, -30,
    -30, -40, -40, -50, -50, -40, -40, -30,
    -30, -40, -40, -50, -50, -40, -40, -30,
    -20, -30, -30, -40, -40, -30, -30, -20,
    -10, -20, -20, -20, -20, -20, -20, -10,
     20,  20,   0,   0,   0,   0,  20,  20,
     20,  30,  10,   0,   0,  10,  30,  20,
]
KING_END_PST = [
    -50, -40, -30, -20, -20, -30, -40, -50,
    -30, -20, -10,   0,   0, -10, -20, -30,
    -30, -10,  20,  30,  30,  20, -10, -30,
    -30, -10,  30,  40,  40,  30, -10, -30,
    -30, -10,  30,  40,  40,  30, -10, -30,
    -30, -10,  20,  30,  30,  20, -10, -30,
    -30, -30,   0,   0,   0,   0, -30, -30,
    -50, -30, -30, -30, -30, -30, -30, -50,
]

CENTER_SQUARES = (chess.D4, chess.E4, chess.D5, chess.E5)


def evaluate_board(board: chess.Board) -> int:
    if board.is_checkmate():
        # If it's checkmate and it's your turn, you've lost.
        return -MATE_SCORE if board.turn == chess.WHITE else MATE_SCORE
    if board.is_stalemate() or board.is_insufficient_material() or board.can_claim_draw():
        return 0

    phase = _game_phase(board)
    score = 0
    for square, piece in board.piece_map().items():
        value = PIECE_VALUES[piece.piece_type]
        pst = _piece_square_value(piece, square, phase)
        if piece.color == chess.WHITE:
            score += value + pst
        else:
            score -= value + pst

    score += _bishop_pair(board)
    score += _rook_activity(board)
    score += _passed_pawns(board)
    score += _center_control(board)
    score += _king_safety(board)
    score += _mobility(board)
    score += _tempo(board)
    return score


def _game_phase(board: chess.Board) -> float:
    non_king_material = 0
    for piece in board.piece_map().values():
        if piece.piece_type != chess.KING:
            non_king_material += PIECE_VALUES[piece.piece_type]
    return max(0.0, min(1.0, non_king_material / 5600.0))


def _piece_square_value(piece: chess.Piece, square: int, phase: float) -> int:
    if piece.piece_type == chess.PAWN:
        table = PAWN_PST
    elif piece.piece_type == chess.KNIGHT:
        table = KNIGHT_PST
    elif piece.piece_type == chess.BISHOP:
        table = BISHOP_PST
    elif piece.piece_type == chess.ROOK:
        table = ROOK_PST
    elif piece.piece_type == chess.QUEEN:
        table = QUEEN_PST
    elif piece.piece_type == chess.KING:
        mid = KING_MID_PST[square if piece.color == chess.WHITE else chess.square_mirror(square)]
        end = KING_END_PST[square if piece.color == chess.WHITE else chess.square_mirror(square)]
        return round(mid * phase + end * (1.0 - phase))
    else:
        return 0

    idx = square if piece.color == chess.WHITE else chess.square_mirror(square)
    value = table[idx]
    return value if piece.color == chess.WHITE else -value


def _bishop_pair(board: chess.Board) -> int:
    score = 0
    if len(board.pieces(chess.BISHOP, chess.WHITE)) >= 2:
        score += 30
    if len(board.pieces(chess.BISHOP, chess.BLACK)) >= 2:
        score -= 30
    return score


def _rook_activity(board: chess.Board) -> int:
    score = 0
    for square, piece in board.piece_map().items():
        if piece.piece_type != chess.ROOK:
            continue
        file_index = chess.square_file(square)
        own_pawns = 0
        enemy_pawns = 0
        for rank in range(8):
            sq = chess.square(file_index, rank)
            occupant = board.piece_at(sq)
            if occupant and occupant.piece_type == chess.PAWN:
                if occupant.color == piece.color:
                    own_pawns += 1
                else:
                    enemy_pawns += 1
        bonus = 0
        if own_pawns == 0 and enemy_pawns == 0:
            bonus = 20
        elif own_pawns == 0 and enemy_pawns > 0:
            bonus = 10
        if piece.color == chess.WHITE:
            score += bonus
        else:
            score -= bonus
    return score


def _passed_pawns(board: chess.Board) -> int:
    score = 0
    for square, piece in board.piece_map().items():
        if piece.piece_type != chess.PAWN:
            continue
        if _is_passed_pawn(board, square, piece.color):
            rank = chess.square_rank(square)
            if piece.color == chess.WHITE:
                score += 12 * rank + 10
            else:
                score -= 12 * (7 - rank) + 10
    return score


def _is_passed_pawn(board: chess.Board, square: int, color: chess.Color) -> bool:
    file_index = chess.square_file(square)
    rank_index = chess.square_rank(square)
    forward_ranks = range(rank_index + 1, 8) if color == chess.WHITE else range(rank_index - 1, -1, -1)
    for df in (-1, 0, 1):
        file_ = file_index + df
        if not 0 <= file_ < 8:
            continue
        for rank in forward_ranks:
            other = board.piece_at(chess.square(file_, rank))
            if other and other.color != color and other.piece_type == chess.PAWN:
                return False
    return True


def _center_control(board: chess.Board) -> int:
    score = 0
    for sq in CENTER_SQUARES:
        white_attackers = len(board.attackers(chess.WHITE, sq))
        black_attackers = len(board.attackers(chess.BLACK, sq))
        score += 4 * (white_attackers - black_attackers)
    return score


def _king_safety(board: chess.Board) -> int:
    score = 0
    for color in (chess.WHITE, chess.BLACK):
        king_sq = board.king(color)
        if king_sq is None:
            continue
        attackers = len(board.attackers(not color, king_sq))
        shield = _pawn_shield(board, king_sq, color)
        local = shield * 12 - attackers * 24
        score += local if color == chess.WHITE else -local
    return score


def _pawn_shield(board: chess.Board, king_sq: int, color: chess.Color) -> int:
    file_index = chess.square_file(king_sq)
    rank_index = chess.square_rank(king_sq)
    direction = 1 if color == chess.WHITE else -1
    shield = 0
    for df in (-1, 0, 1):
        file_ = file_index + df
        rank_ = rank_index - direction
        if 0 <= file_ < 8 and 0 <= rank_ < 8:
            piece = board.piece_at(chess.square(file_, rank_))
            if piece and piece.color == color and piece.piece_type == chess.PAWN:
                shield += 1
    return shield


def _mobility(board: chess.Board) -> int:
    my_moves = board.legal_moves.count()
    other = board.copy(stack=False)
    other.turn = not board.turn
    opp_moves = other.legal_moves.count()
    delta = my_moves - opp_moves
    # Scale from white perspective.
    return delta * (2 if board.turn == chess.WHITE else -2)


def _tempo(board: chess.Board) -> int:
    return 8 if board.turn == chess.WHITE else -8
