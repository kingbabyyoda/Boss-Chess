from __future__ import annotations

from pathlib import Path

import chess

from boss_chess.cheat_events.core import CheatController
from boss_chess.engine.engine import ChessEngine
from boss_chess.gui.session import AiMoveOutcome
from boss_chess.memes.provider import MemeProvider
from boss_chess.persistence import load_game, save_game
from boss_chess.state import GameState
from boss_chess.trainer.analysis import Trainer
from boss_chess.types import GameConfig


class TerminalGame:
    def __init__(self, config: GameConfig):
        self.config = config
        self.state = GameState()
        self.engine = self._build_engine()
        self.trainer = Trainer(self.engine)
        self.memes = MemeProvider()
        self.cheat = CheatController()
        self.ai_color = chess.BLACK if not config.ai_plays_white else chess.WHITE
        self.running = True
        self.saves_dir = Path("saves")
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

    def run(self) -> None:
        self._banner()
        while self.running:
            self._render()
            if self.state.board.is_game_over():
                self._game_over()
                break
            self._ai_turn() if self.state.board.turn == self.ai_color else self._human_turn()

    def _banner(self) -> None:
        print("=== Boss Chess ===")
        print("Type 'help' for commands.")
        print(self._mode_line())
        if self.config.trainer:
            print(self.trainer.analyse_opening(self.state.board))
        if self.config.meme:
            print(self.memes.status_line())
        if self.config.cheat:
            self._print_boss_banner()
            self.cheat.boss_intro_shown = True

    def _print_boss_banner(self) -> None:
        for line in self.cheat.boss_banner():
            print(line)

    def _mode_line(self) -> str:
        active = ["AI White" if self.ai_color == chess.WHITE else "AI Black"]
        for flag, name in ((self.config.trainer, "Trainer"), (self.config.meme, "Meme"), (self.config.cheat, "Cheat")):
            if flag:
                active.append(name)
        return "Active: " + ", ".join(active)

    def _render(self) -> None:
        print()
        print(self.state.board.unicode(borders=True))
        print(f"Turn: {'White' if self.state.board.turn == chess.WHITE else 'Black'}")
        print(self._mode_line())
        print(self._history_line())
        if self.config.trainer:
            print(self.trainer.analyse_opening(self.state.board))
        if self.config.meme:
            print(self.memes.status_line())
        if self.config.cheat:
            self._print_boss_banner()
            print(f"Cheat event: {self.cheat.last_event}")
            if self.cheat.event_log:
                print("Recent chaos: " + " | ".join(self.cheat.event_log[-3:]))
        if self.state.move_history:
            print(f"Last move: {self.state.move_history[-1].uci()}")

    def _history_line(self) -> str:
        return "Moves: none yet" if not self.state.move_history else f"Moves: {' '.join(move.uci() for move in self.state.move_history[-8:])}"

    def _human_turn(self) -> None:
        while True:
            text = input("Your move> ").strip()
            if not text:
                continue
            lower = text.lower()
            if lower in {"quit", "exit"}:
                self.running = False
                return
            if lower == "help":
                self._help(); continue
            if lower == "new":
                self.state.reset(); self.cheat = CheatController(); print("New game started.")
                if self.config.trainer:
                    print(self.trainer.analyse_opening(self.state.board))
                if self.config.meme:
                    print(self.memes.status_line())
                if self.config.cheat:
                    self._print_boss_banner(); self.cheat.boss_intro_shown = True
                return
            if lower == "undo":
                self._undo(); return
            if lower == "fen":
                print(self.state.board.fen()); continue
            if lower == "modes":
                print(self._mode_line()); continue
            if lower == "pgn":
                print(self._pgn_text()); continue
            if lower == "eval":
                print(self._evaluation_text()); continue
            if lower == "report":
                print(self.trainer.report_text(self.state.board)); continue
            if lower == "lesson":
                print(self.trainer.lesson_text(self.state.board)); continue
            if lower in {"practice", "puzzle"}:
                prompt = self.trainer.practice_prompt(self.state.board)
                print(f"Puzzle theme: {prompt.theme}")
                print(f"Opening: {prompt.opening_name}")
                print(f"Clue: {prompt.clue}")
                print(f"Target move: {prompt.target_move}")
                print(f"Explanation: {prompt.explanation}")
                continue
            if lower in {"save", "load"}:
                print(f"Usage: {lower} <name>"); continue
            if lower == "saves":
                self._list_saves(); continue
            if lower.startswith("save "):
                self._save(lower[5:].strip()); continue
            if lower.startswith("load "):
                self._load(lower[5:].strip()); return

            move = self._parse_move(text)
            if move is None:
                print("Could not parse that move. Example: e2e4"); continue
            if move not in self.state.board.legal_moves:
                print("Illegal move."); continue

            board_before = self.state.board.copy(stack=False)
            captured = self.state.board.piece_at(move.to_square)
            self.state.push(move)
            if captured:
                self.cheat.note_capture(captured, self.ai_color)
            if self.config.trainer:
                print(self.trainer.review_move(board_before, move))
            if self.config.meme:
                print(self.memes.get_context_line())
            if self.config.cheat and not self.cheat.boss_intro_shown:
                self._print_boss_banner(); self.cheat.boss_intro_shown = True
            self._autosave(); return

    def _ai_turn(self) -> None:
        outcome = self.session_ai_turn()
        if outcome:
            for message in outcome.messages:
                print(message)
            self._autosave()

    def session_ai_turn(self) -> AiMoveOutcome | None:
        if self.state.board.is_game_over() or self.state.board.turn != self.ai_color:
            return None
        move = self.engine.pick_move(self.state.board)
        captured = self.state.board.piece_at(move.to_square)
        self.state.push(move)
        if captured:
            self.cheat.note_capture(captured, self.ai_color)
        messages = [f"AI plays {move.uci()}"]
        if self.config.cheat:
            if not self.cheat.boss_intro_shown:
                self._print_boss_banner(); self.cheat.boss_intro_shown = True
            self.cheat.apply(self.state.board, self.ai_color)
            messages.append(f"Cheat event: {self.cheat.last_event}")
        if self.config.trainer:
            messages.append(self.trainer.report_text(self.state.board))
        if self.config.meme:
            messages.append(self.memes.get_context_line())
        while self.config.cheat and self.cheat.extra_turns > 0 and not self.state.board.is_game_over():
            self.cheat.extra_turns -= 1
            extra = self.engine.pick_move(self.state.board)
            cap = self.state.board.piece_at(extra.to_square)
            self.state.push(extra)
            if cap:
                self.cheat.note_capture(cap, self.ai_color)
            messages.append(f"AI steals another move: {extra.uci()}")
            self.cheat.apply(self.state.board, self.ai_color)
            messages.append(f"Cheat event: {self.cheat.last_event}")
        return AiMoveOutcome(move=move, messages=messages)

    def _game_over(self) -> None:
        print(); print("Game over.")
        if self.state.board.is_checkmate():
            winner = "White" if self.state.board.turn == chess.BLACK else "Black"
            print(f"Checkmate. {winner} wins.")
        elif self.state.board.is_stalemate():
            print("Stalemate.")
        elif self.state.board.is_insufficient_material():
            print("Draw by insufficient material.")
        else:
            print("Draw.")
        print(f"Result: {self.state.board.result(claim_draw=True)}")
        if self.config.trainer:
            print(self.trainer.report_text(self.state.board))

    def _undo(self) -> None:
        print("Nothing to undo." if self.state.pop() is None else "Undid the last move.")
        self._autosave()

    def _help(self) -> None:
        print("Commands: e2e4, undo, fen, pgn, eval, report, lesson, practice, puzzle, save <name>, load <name>, saves, new, modes, help, quit")

    def _parse_move(self, text: str) -> chess.Move | None:
        try:
            return chess.Move.from_uci(text.strip().lower())
        except Exception:
            return None

    def _autosave(self) -> None:
        try:
            save_game(self.saves_dir / "autosave.json", self.state, self.config, self.ai_color, self.cheat)
        except Exception:
            pass

    def _save(self, name: str) -> None:
        if not name:
            print("Usage: save <name>"); return
        path = self._save_path(name)
        save_game(path, self.state, self.config, self.ai_color, self.cheat)
        print(f"Saved to {path.as_posix()}")

    def _load(self, name: str) -> None:
        if not name:
            print("Usage: load <name>"); return
        path = self._save_path(name)
        if not path.exists():
            print(f"No save found at {path.as_posix()}"); return
        loaded = load_game(path)
        self.state, self.config, self.ai_color, self.cheat = loaded.state, loaded.config, loaded.ai_color, loaded.cheat
        self.engine = self._build_engine(); self.trainer = Trainer(self.engine); self.memes = MemeProvider()
        print(f"Loaded {path.as_posix()}")

    def _list_saves(self) -> None:
        saves = sorted(self.saves_dir.glob("*.json"))
        print("No save files yet." if not saves else "\n".join(path.name for path in saves))

    def _save_path(self, name: str) -> Path:
        clean = name.strip().replace("/", "_").replace("\\", "_")
        if not clean.endswith(".json"):
            clean += ".json"
        return self.saves_dir / clean

    def _pgn_text(self) -> str:
        return "(no moves yet)" if not self.state.move_history else " ".join(move.uci() for move in self.state.move_history)

    def _evaluation_text(self) -> str:
        analysis = self.engine.analyse(self.state.board, max_lines=3)
        best = analysis.best_move.uci() if analysis.best_move else "n/a"
        top = ", ".join(f"{move.uci()} ({score / 100:+.2f})" for move, score in analysis.top_lines) if analysis.top_lines else "n/a"
        return f"{analysis.summary}\nBest: {best}\nTop: {top}"
