from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
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


@dataclass(slots=True)
class _RootBundle:
    best_move: chess.Move
    best_score: int
    top_lines: list[tuple[chess.Move, int]]


class Searcher:
    def __init__(self, depth: int = 3, tablebase_path: str | None = None) -> None:
        self.depth = max(1, depth)
        self.tt: dict[object, TTEntry] = {}
        self.nodes = 0
        self.killer_moves: dict[int, list[chess.Move]] = {}
        self.history: dict[str, int] = {}
        env_tablebase = tablebase_path or os.getenv("BOSS_CHESS_SYZYGY_PATH")
        self.tablebase_path = Path(env_tablebase).expanduser() if env_tablebase else None

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

        tablebase = self._analyse_tablebase(board, max_lines=max_lines)
        if tablebase is not None:
            return tablebase

        self.nodes = 0
        best_move = legal_moves[0]
        best_score = -INF
        top_lines: list[tuple[chess.Move, int]] = [(best_move, best_score)]
        previous_best: chess.Move | None = None
        aspiration = 40

        for current_depth in range(1, self.depth + 1):
            if current_depth == 1 or abs(best_score) >= MATE_SCORE // 2:
                alpha, beta = -INF, INF
            else:
                alpha = max(-INF, best_score - aspiration)
                beta = min(INF, best_score + aspiration)

            for _attempt in range(3):
                bundle = self._search_root(board, current_depth, alpha, beta, previous_best, max_lines=max_lines)
                if bundle.best_score <= alpha and alpha > -INF:
                    alpha = max(-INF, alpha - aspiration)
                    beta = min(INF, beta + aspiration)
                    continue
                if bundle.best_score >= beta and beta < INF:
                    alpha = max(-INF, alpha - aspiration)
                    beta = min(INF, beta + aspiration)
                    continue
                best_move = bundle.best_move
                best_score = bundle.best_score
                top_lines = bundle.top_lines
                previous_best = best_move
                break
            else:
                best_move = bundle.best_move
                best_score = bundle.best_score
                top_lines = bundle.top_lines
                previous_best = best_move

        return _AnalysisBundle(
            best_move=best_move,
            best_score=best_score,
            top_lines=top_lines[:max_lines],
            summary=_format_summary(best_score, board.turn),
        )

    def score_position(self, board: chess.Board) -> int:
        color = 1 if board.turn == chess.WHITE else -1
        return color * evaluate_board(board)

    def _search_root(
        self,
        board: chess.Board,
        depth: int,
        alpha: int,
        beta: int,
        hash_move: Optional[chess.Move],
        max_lines: int = 3,
    ) -> _RootBundle:
        legal_moves = list(board.legal_moves)
        if not legal_moves:
            raise ValueError("No legal moves available.")

        # Prefer the first immediate mate in the natural move-generation order.
        # This keeps forced-mate tests stable when more than one mate exists.
        for move in legal_moves:
            board.push(move)
            is_mate = board.is_checkmate()
            board.pop()
            if is_mate:
                return _RootBundle(best_move=move, best_score=MATE_SCORE, top_lines=[(move, MATE_SCORE)])

        entry = self.tt.get(self._key(board))
        root_hint = hash_move or (entry.best_move if entry else None)
        moves = self._order_moves(board, legal_moves, root_hint, ply=0)

        scored: list[tuple[chess.Move, int]] = []
        current_alpha = alpha
        best_move = moves[0]
        best_score = -INF

        for move in moves:
            board.push(move)
            score = -self._negamax(board, depth - 1, -beta, -current_alpha, ply=1)
            board.pop()
            scored.append((move, score))

            if score > best_score:
                best_score = score
                best_move = move
            if score > current_alpha:
                current_alpha = score

        scored.sort(key=lambda item: item[1], reverse=True)
        return _RootBundle(best_move=best_move, best_score=best_score, top_lines=scored[:max_lines])

    def _negamax(self, board: chess.Board, depth: int, alpha: int, beta: int, ply: int) -> int:
        self.nodes += 1

        if board.is_checkmate():
            return -MATE_SCORE + ply
        if board.is_stalemate() or board.is_insufficient_material() or board.can_claim_draw():
            return 0

        tb_score = self._tablebase_score(board)
        if tb_score is not None:
            return tb_score

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
            return self._quiescence(board, alpha, beta, ply)

        legal_moves = list(board.legal_moves)
        if not legal_moves:
            return _side_to_move(board) * evaluate_board(board)

        hash_move = entry.best_move if entry else None
        moves = self._order_moves(board, legal_moves, hash_move, ply=ply)

        best_score = -INF
        best_move: Optional[chess.Move] = None
        original_alpha = alpha

        for move in moves:
            board.push(move)
            score = -self._negamax(board, depth - 1, -beta, -alpha, ply + 1)
            board.pop()

            if score > best_score:
                best_score = score
                best_move = move
            if score > alpha:
                alpha = score
            if alpha >= beta:
                self._record_killer(ply, move)
                self._bump_history(move, depth)
                break

        flag = "exact"
        if best_score <= original_alpha:
            flag = "upper"
        elif best_score >= beta:
            flag = "lower"
        self.tt[key] = TTEntry(depth=depth, score=best_score, flag=flag, best_move=best_move)
        return best_score

    def _quiescence(self, board: chess.Board, alpha: int, beta: int, ply: int) -> int:
        stand_pat = _side_to_move(board) * evaluate_board(board)
        if stand_pat >= beta:
            return beta
        if stand_pat > alpha:
            alpha = stand_pat

        tactical_moves = [move for move in board.legal_moves if board.is_capture(move) or board.gives_check(move)]
        tactical_moves.sort(key=lambda move: self._move_order_score(board, move, ply), reverse=True)
        for move in tactical_moves:
            board.push(move)
            score = -self._quiescence(board, -beta, -alpha, ply + 1)
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
        ply: int,
    ) -> list[chess.Move]:
        killers = self.killer_moves.get(ply, [])

        def sort_key(move: chess.Move) -> int:
            score = self._move_order_score(board, move, ply)
            if hash_move is not None and move == hash_move:
                score += 100_000
            if move in killers:
                score += 9_000
            return score

        return sorted(moves, key=sort_key, reverse=True)

    def _move_order_score(self, board: chess.Board, move: chess.Move, ply: int) -> int:
        score = 0
        if board.is_capture(move):
            victim = board.piece_at(move.to_square)
            attacker = board.piece_at(move.from_square)
            if victim:
                score += 10 * _piece_value(victim.piece_type)
            if attacker:
                score -= _piece_value(attacker.piece_type)
        if move.promotion:
            score += 1_000 + _piece_value(move.promotion)
        if board.gives_check(move):
            score += 100
        if move == self._killer_move(ply, 0):
            score += 500
        if move == self._killer_move(ply, 1):
            score += 400
        score += self.history.get(move.uci(), 0)
        piece = board.piece_at(move.from_square)
        if piece is not None:
            if piece.piece_type in (chess.KNIGHT, chess.BISHOP) and chess.square_rank(move.from_square) in (0, 7):
                score += 20
            if piece.piece_type == chess.PAWN and chess.square_file(move.to_square) in (3, 4):
                score += 12
            if piece.piece_type == chess.ROOK and board.is_castling(move):
                score += 60
        return score

    def _record_killer(self, ply: int, move: chess.Move) -> None:
        killers = self.killer_moves.setdefault(ply, [])
        if move in killers:
            return
        killers.insert(0, move)
        del killers[2:]

    def _killer_move(self, ply: int, index: int) -> Optional[chess.Move]:
        killers = self.killer_moves.get(ply, [])
        if 0 <= index < len(killers):
            return killers[index]
        return None

    def _bump_history(self, move: chess.Move, depth: int) -> None:
        key = move.uci()
        self.history[key] = min(50_000, self.history.get(key, 0) + depth * depth * 8)

    def _tablebase_score(self, board: chess.Board) -> int | None:
        bundle = self._analyse_tablebase(board, max_lines=1)
        return None if bundle is None else bundle.best_score

    def _analyse_tablebase(self, board: chess.Board, max_lines: int = 3):
        if self.tablebase_path is None or board.piece_count() > 6:
            return None

        try:
            import chess.syzygy
        except Exception:
            return None

        try:
            with chess.syzygy.open_tablebase(str(self.tablebase_path)) as tablebase:
                scored: list[tuple[chess.Move, int]] = []
                for move in board.legal_moves:
                    board.push(move)
                    try:
                        wdl = tablebase.probe_wdl(board)
                        dtz = tablebase.probe_dtz(board)
                    except Exception:
                        wdl = 0
                        dtz = 0
                    board.pop()
                    scored.append((move, self._wdl_to_score(wdl, dtz, board.turn)))
                if not scored:
                    return None
                scored.sort(key=lambda item: item[1], reverse=True)
                best_move, best_score = scored[0]
                return _AnalysisBundle(
                    best_move=best_move,
                    best_score=best_score,
                    top_lines=scored[:max_lines],
                    summary="Endgame tablebase line.",
                )
        except Exception:
            return None

    def _wdl_to_score(self, wdl: int, dtz: int, turn: chess.Color) -> int:
        base = int(wdl) * 10_000
        if dtz:
            base -= min(999, abs(int(dtz)))
        return base if turn == chess.WHITE else -base

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


def _side_to_move(board: chess.Board) -> int:
    return 1 if board.turn == chess.WHITE else -1


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
