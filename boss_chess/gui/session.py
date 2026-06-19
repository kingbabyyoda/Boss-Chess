from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import chess

from boss_chess.cheat_events.core import CheatController
from boss_chess.engine.engine import ChessEngine
from boss_chess.memes.provider import MemeProvider
from boss_chess.persistence import load_game, save_game
from boss_chess.replay import export_pgn
from boss_chess.stats import SessionStats
from boss_chess.state import GameState
from boss_chess.trainer.analysis import Trainer
from boss_chess.trainer.report import PracticePrompt
from boss_chess.types import GameConfig
from boss_chess.variants import variant_label


@dataclass(slots=True)
class AiMoveOutcome:
    move: chess.Move
    messages: list[str]
    evaluation: int = 0


@dataclass(slots=True)
class GuiSession:
    config: GameConfig
    state: GameState = field(default_factory=GameState)
    engine: ChessEngine = field(init=False)
    trainer: Trainer = field(init=False)
    memes: MemeProvider = field(default_factory=MemeProvider)
    cheat: CheatController = field(default_factory=CheatController)
    stats: SessionStats = field(default_factory=SessionStats)
    ai_color: chess.Color = field(init=False)
    saves_dir: Path = field(default_factory=lambda: Path("saves"))
    eval_history: list[int] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.state.reset(variant=self.config.variant.name.value, chess960_seed=self.config.variant.chess960_seed)
        self.engine = self._build_engine()
        self.trainer = Trainer(self.engine)
        self.ai_color = chess.BLACK if not self.config.ai_plays_white else chess.WHITE
        self.saves_dir.mkdir(parents=True, exist_ok=True)

    def _build_engine(self) -> ChessEngine:
        return ChessEngine(
            depth=self.config.engine.depth,
            use_stockfish=self.config.engine.use_stockfish,
            stockfish_path=self.config.engine.stockfish_path,
            use_opening_book=self.config.engine.use_opening_book,
            target_elo=self.config.engine.target_elo,
            multi_pv=self.config.engine.multi_pv,
        )

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
        lines = [self.mode_text(), f"Variant: {variant_label(self.state.variant)}", f"Turn: {self.current_turn_label()}"]
        if self.state.move_history:
            lines.append(f"Last move: {self.state.move_history[-1].uci()}")
        if self.state.board.is_check():
            lines.append("Check!")
        if self.config.trainer:
            lines.append(self.trainer.analyse_opening(self.state.board))
        if self.config.meme:
            lines.append(self.memes.status_line())
        if self.config.cheat:
            lines.extend(self.cheat.boss_banner())
            lines.append(f"Cheat: {self.cheat.last_event}")
            if self.cheat.event_log:
                lines.append(f"Chaos log: {self.cheat.event_log[-1]}")
        return "\n".join(lines)

    def trainer_report_text(self) -> str:
        return self.trainer.report_text(self.state.board)

    def trainer_lesson_text(self) -> str:
        return self.trainer.lesson_text(self.state.board)

    def trainer_practice_prompt(self) -> PracticePrompt:
        return self.trainer.practice_prompt(self.state.board)

    def trainer_puzzle_text(self) -> str:
        prompt = self.trainer.practice_prompt(self.state.board)
        return "\n".join(
            [
                f"Puzzle theme: {prompt.theme}",
                f"Opening: {prompt.opening_name}",
                f"Clue: {prompt.clue}",
                f"Target move: {prompt.target_move}",
                f"Explanation: {prompt.explanation}",
            ]
        )

    def opening_explorer_text(self) -> str:
        return self.trainer.analyse_opening(self.state.board)

    def stats_text(self) -> str:
        lines = self.stats.summary_lines()
        achievements = self.stats.unlocked_achievements()
        if achievements:
            lines.append("Achievements:")
            lines.extend(f"- {item.title}: {item.description}" for item in achievements)
        else:
            lines.append("Achievements: none unlocked yet")
        return "\n".join(lines)

    def export_pgn(self, name: str) -> Path:
        path = self.saves_dir / (name if name.endswith(".pgn") else f"{name}.pgn")
        export_pgn(self.state, path, headers={"Event": "Boss Chess", "White": "Human", "Black": "Engine"})
        return path

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
            self.cheat.note_capture(captured, self.ai_color)
        opening_name = self.trainer.opening_recognizer.identify(list(board_before.move_stack))
        self.stats.record_move(opening_name)

        messages: list[str] = []
        if self.config.trainer:
            messages.append(self.trainer.review_move(board_before, move))
        if self.config.meme:
            messages.append(self.memes.get_context_line())
        if self.config.cheat and not self.cheat.boss_intro_shown:
            messages.extend(self.cheat.boss_banner())
            self.cheat.boss_intro_shown = True
        self.eval_history.append(self.trainer.engine.score_position(self.state.board))
        self.eval_history = self.eval_history[-48:]
        self._autosave()
        return "\n".join(messages) if messages else "Move played."

    def ai_move(self) -> AiMoveOutcome | None:
        if self.state.board.is_game_over() or self.state.board.turn != self.ai_color:
            return None

        messages: list[str] = []
        move = self.engine.pick_move(self.state.board)
        captured = self.state.board.piece_at(move.to_square)
        self.state.push(move)
        if captured:
            self.cheat.note_capture(captured, self.ai_color)
        opening_name = self.trainer.opening_recognizer.identify(list(self.state.board.move_stack))
        self.stats.record_move(opening_name)
        messages.append(f"AI plays {move.uci()}")

        if self.config.cheat:
            if not self.cheat.boss_intro_shown:
                messages.extend(self.cheat.boss_banner())
                self.cheat.boss_intro_shown = True
            self.cheat.apply(self.state.board, self.ai_color)
            messages.append(f"Cheat event: {self.cheat.last_event}")

        if self.config.meme:
            messages.append(self.memes.get_context_line())

        while self.config.cheat and self.cheat.extra_turns > 0 and not self.state.board.is_game_over():
            self.cheat.extra_turns -= 1
            extra = self.engine.pick_move(self.state.board)
            cap = self.state.board.piece_at(extra.to_square)
            self.state.push(extra)
            if cap:
                self.cheat.note_capture(cap, self.ai_color)
            self.stats.record_move(self.trainer.opening_recognizer.identify(list(self.state.board.move_stack)))
            messages.append(f"AI steals another move: {extra.uci()}")
            self.cheat.apply(self.state.board, self.ai_color)
            messages.append(f"Cheat event: {self.cheat.last_event}")

        self.eval_history.append(self.trainer.engine.score_position(self.state.board))
        self.eval_history = self.eval_history[-48:]
        self._autosave()
        return AiMoveOutcome(move=move, messages=messages, evaluation=self.eval_history[-1] if self.eval_history else 0)

    def game_over_report(self) -> None:
        result = self.state.board.result(claim_draw=True)
        winner = None
        if result == "1-0":
            winner = chess.WHITE
        elif result == "0-1":
            winner = chess.BLACK
        self.stats.record_game_end(result, winner=winner, checkmate=self.state.board.is_checkmate())

    def undo(self) -> str:
        if self.state.pop() is None:
            return "Nothing to undo."
        self._autosave()
        return "Undid the last move."

    def reset(self) -> None:
        self.state.reset(variant=self.config.variant.name.value, chess960_seed=self.config.variant.chess960_seed)
        self.cheat = CheatController()
        self.eval_history.clear()
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
        self.engine = self._build_engine()
        self.trainer = Trainer(self.engine)
        self.memes = MemeProvider()
        self.eval_history.clear()
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

    def eval_graph(self) -> list[int]:
        return list(self.eval_history)

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
