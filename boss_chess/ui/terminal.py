from __future__ import annotations

from pathlib import Path

import chess

from boss_chess.cheat_events.core import CheatController
from boss_chess.engine.engine import ChessEngine
from boss_chess.gui.session import AiMoveOutcome
from boss_chess.memes.provider import MemeProvider
from boss_chess.online import MultiplayerSession
from boss_chess.persistence import load_game, save_game
from boss_chess.replay import export_pgn, load_pgn
from boss_chess.state import GameState
from boss_chess.stats import SessionStats
from boss_chess.trainer.analysis import Trainer
from boss_chess.types import GameConfig
from boss_chess.variants import variant_label


class TerminalGame:
    def __init__(self, config: GameConfig):
        self.config = config
        self.state = GameState(variant=config.variant.name.value, chess960_seed=config.variant.chess960_seed)
        self.engine = self._build_engine()
        self.trainer = Trainer(self.engine)
        self.memes = MemeProvider()
        self.cheat = CheatController()
        self.stats = SessionStats()
        self.ai_color = chess.BLACK if not config.ai_plays_white else chess.WHITE
        self.network: MultiplayerSession | None = None
        self.local_color: chess.Color | None = None
        self.running = True
        self.saves_dir = Path("saves")
        self.saves_dir.mkdir(parents=True, exist_ok=True)

        if self.config.multiplayer.mode in {"host", "join"}:
            self.local_color = chess.WHITE if self.config.multiplayer.mode == "host" else chess.BLACK
            self.network = MultiplayerSession(self.config.multiplayer, self.state.variant, self.local_color)
            print(f"Starting {self.config.multiplayer.mode} session on {self.config.multiplayer.host}:{self.config.multiplayer.port}...")
            self.network.start()
            print(f"Connected to {self.network.peer_name}.")
            if self.config.cheat:
                self.config.cheat = False
                print("Cheat mode is disabled in multiplayer.")

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
        try:
            while self.running:
                self._render()
                if self.state.board.is_game_over():
                    self._game_over()
                    break
                if self.network is not None:
                    self._network_turn()
                elif self.state.board.turn == self.ai_color:
                    self._ai_turn()
                else:
                    self._human_turn()
        finally:
            if self.network is not None:
                self.network.close()

    def _banner(self) -> None:
        print("=== Boss Chess ===")
        print("Type 'help' for commands.")
        print(self._mode_line())
        print(f"Variant: {variant_label(self.state.variant)}")
        if self.network is not None:
            print(f"Multiplayer: {self.config.multiplayer.mode} as {'White' if self.local_color == chess.WHITE else 'Black'}")
            print(f"Opponent: {self.network.peer_name}")
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
        if self.config.trainer:
            active.append("Trainer")
        if self.config.meme:
            active.append("Meme")
        if self.config.cheat:
            active.append("Cheat")
        if self.network is not None:
            active.append(f"Multiplayer ({self.config.multiplayer.mode})")
        return "Active: " + ", ".join(active)

    def _render(self) -> None:
        print()
        print(self.state.board.unicode(borders=True))
        print(f"Turn: {'White' if self.state.board.turn == chess.WHITE else 'Black'}")
        print(self._mode_line())
        print(self._history_line())
        print(f"Variant: {variant_label(self.state.variant)}")
        if self.config.trainer:
            print(self.trainer.analyse_opening(self.state.board))
        if self.config.meme:
            print(self.memes.status_line())
        if self.config.cheat:
            self._print_boss_banner()
            print(f"Cheat event: {self.cheat.last_event}")
            if self.cheat.event_log:
                print("Recent chaos: " + " | ".join(self.cheat.event_log[-3:]))
        if self.network is not None:
            print(f"Opponent: {self.network.peer_name}")
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
                self._reset_game(); print("New game started."); return
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
            if lower == "stats":
                print("\n".join(self.stats.summary_lines()))
                unlocked = self.stats.unlocked_achievements()
                if unlocked:
                    print("Achievements:")
                    for ach in unlocked:
                        print(f"- {ach.title}: {ach.description}")
                continue
            if lower.startswith("exportpgn"):
                name = lower.split(maxsplit=1)[1] if " " in lower else "replay"
                path = self._export_pgn(name)
                print(f"Exported PGN to {path.as_posix()}")
                continue
            if lower.startswith("importpgn"):
                name = lower.split(maxsplit=1)[1] if " " in lower else ""
                if not name:
                    print("Usage: importpgn <name>"); continue
                path = self._pgn_path(name)
                if not path.exists():
                    print(f"No PGN found at {path.as_posix()}")
                    continue
                try:
                    self.state = load_pgn(path)
                    self.engine = self._build_engine()
                    self.trainer = Trainer(self.engine)
                    self._append_message(f"Loaded PGN {path.as_posix()}")
                except Exception as exc:
                    print(f"PGN import failed: {exc}")
                return
            if lower in {"save", "load"}:
                print(f"Usage: {lower} <name>"); continue
            if lower == "saves":
                self._list_saves(); continue
            if lower.startswith("save "):
                self._save(lower[5:].strip()); continue
            if lower.startswith("load "):
                if self.network is not None:
                    print("Loading during multiplayer is disabled.")
                    continue
                self._load(lower[5:].strip()); return

            move = self._parse_move(text)
            if move is None:
                print("Could not parse that move. Example: e2e4"); continue
            if move not in self.state.board.legal_moves:
                print("Illegal move."); continue

            messages = self._apply_move(move, source="You", trainer=self.config.trainer, meme=self.config.meme, use_cheat=self.config.cheat and self.network is None)
            for message in messages:
                print(message)
            if self.network is not None:
                self.network.send_move(move)
            self._autosave(); return

    def _network_turn(self) -> None:
        if self.network is None or self.local_color is None:
            return
        if self.state.board.turn == self.local_color:
            self._human_turn()
            return
        print(f"Waiting for {self.network.peer_name}...")
        try:
            move = self.network.recv_move()
        except Exception as exc:
            print(f"Network error: {exc}")
            self.running = False
            return
        if move not in self.state.board.legal_moves:
            print(f"Remote sent an illegal move: {move.uci()}")
            self.running = False
            return
        for message in self._apply_move(move, source=self.network.peer_name, trainer=False, meme=False, use_cheat=False):
            print(message)

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
        messages = self._apply_move(move, source="AI", trainer=self.config.trainer, meme=self.config.meme, use_cheat=self.config.cheat)
        return AiMoveOutcome(move=move, messages=messages, evaluation=self._current_eval())

    def _apply_move(self, move: chess.Move, source: str, trainer: bool, meme: bool, use_cheat: bool) -> list[str]:
        board_before = self.state.board.copy(stack=False)
        captured = self.state.board.piece_at(move.to_square)
        self.state.push(move)
        if captured:
            self.cheat.note_capture(captured, self.ai_color if use_cheat else None)
        opening_name = self.trainer.opening_recognizer.identify(list(board_before.move_stack))
        self.stats.record_move(opening_name)

        messages = [f"{source} plays {move.uci()}"]
        if trainer:
            if source == "AI":
                messages.append(self.trainer.report_text(board_before))
            else:
                messages.append(self.trainer.review_move(board_before, move))
        if meme:
            messages.append(self.memes.get_context_line())
        if use_cheat:
            if not self.cheat.boss_intro_shown:
                self._print_boss_banner()
                self.cheat.boss_intro_shown = True
            self.cheat.apply(self.state.board, self.ai_color)
            messages.append(f"Cheat event: {self.cheat.last_event}")
            while self.cheat.extra_turns > 0 and not self.state.board.is_game_over():
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
        return messages

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
        result = self.state.board.result(claim_draw=True)
        print(f"Result: {result}")
        self.stats.record_game_end(result, winner=chess.WHITE if result == "1-0" else chess.BLACK if result == "0-1" else None, checkmate=self.state.board.is_checkmate())
        if self.config.trainer:
            print(self.trainer.report_text(self.state.board))

    def _reset_game(self) -> None:
        if self.network is not None:
            print("New game is disabled during multiplayer.")
            return
        self.state.reset(variant=self.config.variant.name.value, chess960_seed=self.config.variant.chess960_seed)
        self.cheat = CheatController()
        self._autosave()

    def _undo(self) -> None:
        if self.network is not None:
            print("Undo is disabled during multiplayer.")
            return
        print("Nothing to undo." if self.state.pop() is None else "Undid the last move.")
        self._autosave()

    def _help(self) -> None:
        commands = [
            "e2e4", "undo", "fen", "pgn", "eval", "report", "lesson", "practice", "puzzle",
            "stats", "exportpgn <name>", "importpgn <name>", "save <name>", "load <name>",
            "saves", "new", "modes", "help", "quit",
        ]
        if self.network is not None:
            commands.append("(multiplayer: new/load/undo are disabled)")
        print("Commands: " + ", ".join(commands))

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

    def _export_pgn(self, name: str) -> Path:
        path = self._pgn_path(name)
        export_pgn(self.state, path, headers={"Event": "Boss Chess", "White": "Human", "Black": "Engine"})
        return path

    def _pgn_path(self, name: str) -> Path:
        clean = name.strip().replace("/", "_").replace("\\", "_")
        if not clean.endswith(".pgn"):
            clean += ".pgn"
        return self.saves_dir / clean

    def _current_eval(self) -> int:
        return self.engine.score_position(self.state.board)

    def _append_message(self, text: str) -> None:
        print(text)
