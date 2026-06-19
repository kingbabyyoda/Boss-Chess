from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import chess
import chess.engine

from boss_chess.types import AnalysisResult

MATE_SCORE = 100000


@dataclass(slots=True)
class StockfishAdapter:
    path: str | None = None
    target_elo: int = 1800
    multi_pv: int = 3
    depth: int = 3
    engine: chess.engine.SimpleEngine | None = None

    def __post_init__(self) -> None:
        if not self.path:
            return
        candidate = Path(self.path).expanduser()
        if not candidate.exists():
            return
        try:
            self.engine = chess.engine.SimpleEngine.popen_uci(str(candidate))
        except Exception:
            self.engine = None
            return

        self._configure_strength()

    def close(self) -> None:
        if self.engine is None:
            return
        try:
            self.engine.quit()
        except Exception:
            pass
        self.engine = None

    def available(self) -> bool:
        return self.engine is not None

    def choose_move(self, board: chess.Board) -> chess.Move | None:
        if self.engine is None:
            return None
        try:
            result = self.engine.play(board, chess.engine.Limit(depth=self.depth))
        except Exception:
            return None
        return result.move

    def analyse(self, board: chess.Board, max_lines: int = 3) -> AnalysisResult | None:
        if self.engine is None:
            return None
        try:
            info = self.engine.analyse(
                board,
                chess.engine.Limit(depth=self.depth),
                multipv=max(1, max_lines),
            )
        except Exception:
            return None

        entries = info if isinstance(info, list) else [info]
        lines: list[tuple[chess.Move, int]] = []
        for entry in entries:
            pv = entry.get("pv") or []
            score_obj = entry.get("score")
            if not pv or score_obj is None:
                continue
            move = pv[0]
            score = _score_to_cp(score_obj)
            lines.append((move, score))

        if not lines:
            return None

        lines.sort(key=lambda item: item[1], reverse=board.turn == chess.WHITE)
        best_move, best_score = lines[0]
        return AnalysisResult(
            best_move=best_move,
            best_score=best_score,
            top_lines=lines[:max_lines],
            summary=_format_summary(best_score),
        )

    def _configure_strength(self) -> None:
        if self.engine is None:
            return
        try:
            opts = self.engine.options
            if "UCI_LimitStrength" in opts and "UCI_Elo" in opts:
                self.engine.configure({"UCI_LimitStrength": True, "UCI_Elo": int(self.target_elo)})
            elif "Skill Level" in opts:
                # Roughly map Elo to the Stockfish 0-20 skill scale.
                skill = max(0, min(20, round((self.target_elo - 800) / 120)))
                self.engine.configure({"Skill Level": skill})
        except Exception:
            pass


def _score_to_cp(score_obj: chess.engine.PovScore) -> int:
    try:
        if score_obj.is_mate():
            mate = score_obj.mate() or 0
            return MATE_SCORE - abs(mate)
        cp = score_obj.score(mate_score=MATE_SCORE)
        return int(cp or 0)
    except Exception:
        return 0


def _format_summary(score: int) -> str:
    if abs(score) >= MATE_SCORE // 2:
        return "Stockfish sees a forced mate."
    side = "White" if score > 0 else "Black"
    if abs(score) < 25:
        return "Stockfish says the position is roughly equal."
    if abs(score) < 100:
        return f"Stockfish gives a small edge to {side.lower()} ({score / 100:+.2f})."
    return f"Stockfish gives a clear edge to {side.lower()} ({score / 100:+.2f})."
