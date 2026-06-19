from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import chess

from boss_chess.cheat_events.core import CheatController
from boss_chess.engine.engine import ChessEngine
from boss_chess.memes.provider import MemeProvider
from boss_chess.persistence import load_game, save_game
from boss_chess.state import GameState
from boss_chess.trainer.analysis import Trainer
from boss_chess.types import GameConfig


@dataclass(slots=True)
class GuiSession:
    config: GameConfig
    state: GameState = field(default_factory=GameState)
    engine: ChessEngine = field(init=False)
    trainer: Trainer = field(init=False)
    memes: MemeProvider = field(default_factory=MemeProvider)
    cheat: CheatController = field(default_factory=CheatController)
    ai_color: chess.Color = field(init=False)
    saves_dir: Path = field(default_factory=lambda: Path("saves"))

    def __post_init__(self) -> None:
        self.engine = ChessEngine(depth=self.config.engine.depth)
        self.trainer = Trainer(self.engine)
        self.ai_color = chess.BLACK if not self.config.ai_plays_white else chess.WHITE
        self.saves_dir.mkdir(parents=True, exist_ok=True)

    def current_turn_label(self) -> str:
        return "White" if self.state.board.turn == chess.WHITE else "Black"

    def mode_text(self) -> str:
        active = ["AI White" if self.ai_color == chess.WHITE else "AI Black"]
        if self.config.trainer:
            active.append("Trainer")
        if self.config.meme:
            active.append("Meme")
        if self.config.cheat:
            active.append("Cheat")
        return "Active: " + ", ".join(active)

    def status_text(self) -> str:
        lines = [self.mode_text(), f"Turn: {self.current_turn_label()}"]
        if self.state.move_history:
            lines.append(f"Last move: {self.state.move_history[-1].uci()}")
        if self.config.cheat:
            lines.append(f"Cheat: {self.cheat.last_event}")
            if self.cheat.event_log:
                lines.append(f"Chaos log: {self.cheat.event_log[-1]}")
        return "\n".join(lines)

    def board_title(self, square: int) -> str:
        piece = self.state.board.piece_at(square)
        if piece is None:
            return ""
        return piece.symbol()

    def can_human_move(self) -> bool:
        return not self.state.board.is_game_over() and self.state.board.turn != self.ai_color

    def human_move(self, move: chess.Move) -> str:
        if move not in self.state.board.legal_moves:
            return "Illegal move."
        board_before = self.state.board.copy(stack=False)
        captured = self.state.board.piece_at(move.to_square)
        self.state.push(move)
        if captured:
            self.cheat.note_capture(captured)

        messages: list[str] = []
        if self.config.trainer:
            messages.append(self.trainer.review_move(board_before, move))
        if self.config.meme:
            messages.append(f"Meme [{self.memes.personality()}]: {self.memes.get_meme()}")
        self._autosave()
        return "\n".join(messages) if messages else "Move played."

    def ai_move(self) -> list[str]:
        if self.state.board.is_game_over() or self.state.board.turn != self.ai_color:
            return []

        messages: list[str] = []
        move = self.engine.pick_move(self.state.board)
        captured = self.state.board.piece_at(move.to_square)
        self.state.push(move)
        if captured:
            self.cheat.note_capture(captured)
        messages.append(f"AI plays {move.uci()}")

        if self.config.cheat:
            self.cheat.apply(self.state.board, self.ai_color)
            messages.append(f"Cheat event: {self.cheat.last_event}")

        if self.config.meme:
            messages.append(f"Meme [{self.memes.personality()}]: {self.memes.get_meme()}")

        while self.config.cheat and self.cheat.extra_turns > 0 and not self.state.board.is_game_over():
            self.cheat.extra_turns -= 1
            extra = self.engine.pick_move(self.state.board)
            cap = self.state.board.piece_at(extra.to_square)
            self.state.push(extra)
            if cap:
                self.cheat.note_capture(cap)
            messages.append(f"AI steals another move: {extra.uci()}")
            self.cheat.apply(self.state.board, self.ai_color)
            messages.append(f"Cheat event: {self.cheat.last_event}")

        self._autosave()
        return messages

    def undo(self) -> str:
        if self.state.pop() is None:
            return "Nothing to undo."
        self._autosave()
        return "Undid the last move."

    def reset(self) -> None:
        self.state.reset()
        self.cheat = CheatController()
        self._autosave()

    def save(self, name: str) -> Path:
        path = self._save_path(name)
        save_game(path, self.state, self.config, self.ai_color, self.cheat)
        return path

    def load(self, name: str) -> Path:
        path = self._save_path(name)
        loaded = load_game(path)
        self.state = loaded.state
        self.config = loaded.config
        self.ai_color = loaded.ai_color
        self.cheat = loaded.cheat
        self.engine = ChessEngine(depth=self.config.engine.depth)
        self.trainer = Trainer(self.engine)
        self.memes = MemeProvider()
        return path

    def list_saves(self) -> list[str]:
        return sorted(path.name for path in self.saves_dir.glob("*.json"))

    def evaluation_text(self) -> str:
        analysis = self.engine.analyse(self.state.board, max_lines=3)
        best = analysis.best_move.uci() if analysis.best_move else "n/a"
        top = ", ".join(f"{move.uci()} ({score / 100:+.2f})" for move, score in analysis.top_lines) if analysis.top_lines else "n/a"
        return f"{analysis.summary}\nBest: {best}\nTop: {top}"

    def pgn_text(self) -> str:
        if not self.state.move_history:
            return "(no moves yet)"
        return " ".join(move.uci() for move in self.state.move_history)

    def _autosave(self) -> None:
        try:
            save_game(self.saves_dir / "autosave.json", self.state, self.config, self.ai_color, self.cheat)
        except Exception:
            pass

    def _save_path(self, name: str) -> Path:
        clean = name.strip().replace("/", "_").replace("\\", "_")
        if not clean.endswith(".json"):
            clean += ".json"
        return self.saves_dir / clean
