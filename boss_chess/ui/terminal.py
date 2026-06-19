from __future__ import annotations

from dataclasses import replace

import chess

from boss_chess.cheat_events.core import CheatController
from boss_chess.engine.engine import ChessEngine
from boss_chess.memes.provider import MemeProvider
from boss_chess.state import GameState
from boss_chess.trainer.analysis import Trainer
from boss_chess.types import GameConfig


class TerminalGame:
    def __init__(self, config: GameConfig):
        self.config = config
        self.state = GameState()
        self.engine = ChessEngine(depth=config.engine.depth)
        self.trainer = Trainer(self.engine)
        self.memes = MemeProvider()
        self.cheat = CheatController()
        self.ai_color = chess.BLACK if not config.ai_plays_white else chess.WHITE
        self.running = True

    def run(self) -> None:
        self._banner()
        while self.running:
            self._render()
            if self.state.board.is_game_over():
                self._game_over()
                break

            if self.state.board.turn == self.ai_color:
                self._ai_turn()
            else:
                self._human_turn()

    def _banner(self) -> None:
        print("=== Boss Chess ===")
        print("Type 'help' for commands.")
        print(self._mode_line())

    def _mode_line(self) -> str:
        active = ["AI White" if self.ai_color == chess.WHITE else "AI Black"]
        if self.config.trainer:
            active.append("Trainer")
        if self.config.meme:
            active.append("Meme")
        if self.config.cheat:
            active.append("Cheat")
        return "Active: " + ", ".join(active)

    def _render(self) -> None:
        print()
        print(self.state.board.unicode(borders=True))
        print(f"Turn: {'White' if self.state.board.turn == chess.WHITE else 'Black'}")
        print(self._mode_line())
        if self.config.cheat:
            print(f"Cheat event: {self.cheat.last_event}")

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
                self._help()
                continue
            if lower == "new":
                self.state = GameState()
                self.cheat = CheatController()
                print("New game started.")
                return
            if lower == "undo":
                self._undo()
                return
            if lower == "fen":
                print(self.state.board.fen())
                continue
            if lower == "modes":
                print(self._mode_line())
                continue

            move = self._parse_move(text)
            if move is None:
                print("Could not parse that move. Example: e2e4")
                continue
            if move not in self.state.board.legal_moves:
                print("Illegal move.")
                continue

            board_before = self.state.board.copy(stack=False)
            captured = self.state.board.piece_at(move.to_square)
            self.state.push(move)
            if captured:
                self.cheat.note_capture(captured)

            if self.config.trainer:
                print(self.trainer.review_move(board_before, move))
            if self.config.meme:
                print(f"Meme [{self.memes.personality()}]: {self.memes.get_meme()}")

            return

    def _ai_turn(self) -> None:
        move = self.engine.pick_move(self.state.board)
        print(f"AI plays {move.uci()}")
        captured = self.state.board.piece_at(move.to_square)
        self.state.push(move)
        if captured:
            self.cheat.note_capture(captured)

        if self.config.cheat:
            self.cheat.apply(self.state.board, self.ai_color)
            print(f"Cheat event: {self.cheat.last_event}")

        if self.config.meme:
            print(f"Meme [{self.memes.personality()}]: {self.memes.get_meme()}")

        while self.config.cheat and self.cheat.extra_turns > 0 and not self.state.board.is_game_over():
            self.cheat.extra_turns -= 1
            extra = self.engine.pick_move(self.state.board)
            print(f"AI steals another move: {extra.uci()}")
            cap = self.state.board.piece_at(extra.to_square)
            self.state.push(extra)
            if cap:
                self.cheat.note_capture(cap)
            self.cheat.apply(self.state.board, self.ai_color)
            print(f"Cheat event: {self.cheat.last_event}")

    def _game_over(self) -> None:
        print()
        print("Game over.")
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

    def _undo(self) -> None:
        if self.state.pop() is None:
            print("Nothing to undo.")
            return
        print("Undid the last move.")

    def _help(self) -> None:
        print(
            "Commands: e2e4, undo, fen, new, modes, help, quit"
        )

    def _parse_move(self, text: str) -> chess.Move | None:
        try:
            return chess.Move.from_uci(text.strip().lower())
        except Exception:
            return None
