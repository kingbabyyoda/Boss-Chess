from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import chess
import tkinter as tk
from tkinter import messagebox, simpledialog, ttk

from boss_chess.gui.session import GuiSession

UNICODE_PIECES = {
    "P": "♙",
    "N": "♘",
    "B": "♗",
    "R": "♖",
    "Q": "♕",
    "K": "♔",
    "p": "♟",
    "n": "♞",
    "b": "♝",
    "r": "♜",
    "q": "♛",
    "k": "♚",
}

THEMES = {
    "Classic": {"light": "#f0d9b5", "dark": "#b58863", "selected": "#f7ea48", "hint": "#8fd3ff"},
    "Midnight": {"light": "#d8dee9", "dark": "#4c566a", "selected": "#88c0d0", "hint": "#a3be8c"},
    "Neon": {"light": "#202020", "dark": "#101010", "selected": "#7c3aed", "hint": "#22d3ee"},
}


@dataclass(slots=True)
class ThemeState:
    name: str = "Classic"

    @property
    def palette(self) -> dict[str, str]:
        return THEMES[self.name]


class BossChessApp:
    def __init__(self, session: GuiSession):
        self.session = session
        self.root = tk.Tk()
        self.root.title("Boss Chess")
        self.root.geometry("1100x780")
        self.root.minsize(980, 700)

        self.theme = ThemeState()
        self.selected_square: int | None = None
        self.square_buttons: dict[int, tk.Button] = {}
        self.message_lines: list[str] = []
        self.human_color = not self.session.ai_color
        self._setup_styles()
        self._build_ui()
        self.refresh_all()
        self.root.after(150, self._kick_ai_if_needed)

    def run(self) -> None:
        self.root.mainloop()

    def _setup_styles(self) -> None:
        style = ttk.Style(self.root)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("Boss.TButton", padding=8)
        style.configure("Boss.TLabelframe", padding=10)
        style.configure("Boss.TLabelframe.Label", font=("Segoe UI", 10, "bold"))
        style.configure("Boss.TLabel", font=("Segoe UI", 10))

    def _build_ui(self) -> None:
        container = ttk.Frame(self.root, padding=12)
        container.pack(fill="both", expand=True)

        self.board_frame = ttk.Frame(container)
        self.board_frame.pack(side="left", fill="both", expand=False)

        side = ttk.Frame(container)
        side.pack(side="right", fill="both", expand=True, padx=(14, 0))

        self.status_var = tk.StringVar(value="")
        self.eval_var = tk.StringVar(value="Press Eval to inspect the position.")
        self.message_var = tk.StringVar(value="Ready.")

        status_label = ttk.Label(side, textvariable=self.status_var, style="Boss.TLabel", justify="left")
        status_label.pack(anchor="w")

        eval_label = ttk.Label(side, textvariable=self.eval_var, style="Boss.TLabel", justify="left")
        eval_label.pack(anchor="w", pady=(8, 12))

        self.move_text = tk.Text(side, height=14, wrap="word", font=("Consolas", 10))
        self.move_text.pack(fill="x", pady=(0, 12))
        self.move_text.configure(state="disabled")

        self.message_text = tk.Text(side, height=12, wrap="word", font=("Consolas", 10))
        self.message_text.pack(fill="both", expand=True)
        self.message_text.configure(state="disabled")

        controls = ttk.Labelframe(side, text="Controls", style="Boss.TLabelframe")
        controls.pack(fill="x", pady=(12, 0))

        button_row = ttk.Frame(controls)
        button_row.pack(fill="x")

        ttk.Button(button_row, text="New Game", style="Boss.TButton", command=self._new_game).pack(side="left", padx=(0, 6))
        ttk.Button(button_row, text="Undo", style="Boss.TButton", command=self._undo).pack(side="left", padx=(0, 6))
        ttk.Button(button_row, text="AI Move", style="Boss.TButton", command=self._force_ai_turn).pack(side="left", padx=(0, 6))
        ttk.Button(button_row, text="Eval", style="Boss.TButton", command=self._show_eval).pack(side="left", padx=(0, 6))
        ttk.Button(button_row, text="PGN", style="Boss.TButton", command=self._show_pgn).pack(side="left")

        save_row = ttk.Frame(controls)
        save_row.pack(fill="x", pady=(10, 0))
        ttk.Label(save_row, text="Save name:").pack(side="left")
        self.save_entry = ttk.Entry(save_row, width=16)
        self.save_entry.pack(side="left", padx=(6, 6))
        self.save_entry.insert(0, "autosave")
        ttk.Button(save_row, text="Save", style="Boss.TButton", command=self._save_game).pack(side="left")
        ttk.Button(save_row, text="Load", style="Boss.TButton", command=self._load_game).pack(side="left", padx=(6, 0))

        options = ttk.Labelframe(side, text="Modes & Theme", style="Boss.TLabelframe")
        options.pack(fill="x", pady=(12, 0))

        self.trainer_var = tk.BooleanVar(value=self.session.config.trainer)
        self.meme_var = tk.BooleanVar(value=self.session.config.meme)
        self.cheat_var = tk.BooleanVar(value=self.session.config.cheat)

        ttk.Checkbutton(options, text="Trainer", variable=self.trainer_var, command=self._sync_modes).pack(anchor="w")
        ttk.Checkbutton(options, text="Meme", variable=self.meme_var, command=self._sync_modes).pack(anchor="w")
        ttk.Checkbutton(options, text="Cheat", variable=self.cheat_var, command=self._sync_modes).pack(anchor="w")

        theme_row = ttk.Frame(options)
        theme_row.pack(fill="x", pady=(8, 0))
        ttk.Label(theme_row, text="Theme:").pack(side="left")
        self.theme_var = tk.StringVar(value=self.theme.name)
        theme_box = ttk.Combobox(theme_row, textvariable=self.theme_var, values=list(THEMES.keys()), state="readonly", width=12)
        theme_box.pack(side="left", padx=(6, 0))
        theme_box.bind("<<ComboboxSelected>>", lambda _event: self._set_theme(self.theme_var.get()))

        self._build_board()

    def _build_board(self) -> None:
        for child in self.board_frame.winfo_children():
            child.destroy()
        self.square_buttons.clear()

        for rank in range(7, -1, -1):
            for file in range(8):
                square = chess.square(file, rank)
                button = tk.Button(
                    self.board_frame,
                    text="",
                    font=("Segoe UI Symbol", 24),
                    width=3,
                    height=1,
                    relief="flat",
                    command=lambda sq=square: self._square_clicked(sq),
                )
                button.grid(row=7 - rank, column=file, sticky="nsew")
                self.square_buttons[square] = button

        for i in range(8):
            self.board_frame.columnconfigure(i, weight=1)
            self.board_frame.rowconfigure(i, weight=1)

    def refresh_all(self) -> None:
        self._render_board()
        self._refresh_status()
        self._refresh_moves()
        self._refresh_messages()
        if self.session.state.board.is_game_over():
            self.eval_var.set(self._game_over_text())

    def _render_board(self) -> None:
        palette = self.theme.palette
        legal_targets = self._legal_targets()
        last_move = self.session.state.move_history[-1] if self.session.state.move_history else None
        selected = self.selected_square

        for square, button in self.square_buttons.items():
            piece = self.session.state.board.piece_at(square)
            label = UNICODE_PIECES.get(piece.symbol(), piece.symbol()) if piece else ""
            button.configure(text=label)

            base = palette["light"] if (chess.square_file(square) + chess.square_rank(square)) % 2 == 0 else palette["dark"]
            if selected == square:
                base = palette["selected"]
            elif square in legal_targets:
                base = palette["hint"]
            elif last_move and square in {last_move.from_square, last_move.to_square}:
                base = "#d4a373"

            fg = "#111111"
            if piece and piece.color == chess.BLACK:
                fg = "#f4f4f4"
            button.configure(bg=base, activebackground=base, fg=fg, highlightthickness=0, bd=0)

    def _refresh_status(self) -> None:
        self.status_var.set(self.session.status_text())

    def _refresh_moves(self) -> None:
        moves = self.session.pgn_text()
        self.move_text.configure(state="normal")
        self.move_text.delete("1.0", "end")
        self.move_text.insert("end", "Moves\n")
        self.move_text.insert("end", moves if moves else "(no moves yet)")
        self.move_text.configure(state="disabled")

    def _refresh_messages(self) -> None:
        self.message_text.configure(state="normal")
        self.message_text.delete("1.0", "end")
        self.message_text.insert("end", "\n\n".join(self.message_lines[-12:]) if self.message_lines else "Ready.")
        self.message_text.configure(state="disabled")

    def _set_theme(self, name: str) -> None:
        if name in THEMES:
            self.theme.name = name
            self.refresh_all()

    def _sync_modes(self) -> None:
        self.session.config.trainer = self.trainer_var.get()
        self.session.config.meme = self.meme_var.get()
        self.session.config.cheat = self.cheat_var.get()
        self._append_message("Modes updated.")
        self.refresh_all()

    def _square_clicked(self, square: int) -> None:
        if not self.session.can_human_move():
            self._append_message("It is not your turn.")
            return

        piece = self.session.state.board.piece_at(square)
        if self.selected_square is None:
            if piece is None or piece.color == self.session.ai_color:
                return
            self.selected_square = square
            self.refresh_all()
            return

        if square == self.selected_square:
            self.selected_square = None
            self.refresh_all()
            return

        move = self._build_move(self.selected_square, square)
        self.selected_square = None
        if move is None:
            self._append_message("That move is not legal.")
            self.refresh_all()
            return

        result = self.session.human_move(move)
        self._append_message(result)
        self.refresh_all()
        self._maybe_ai_turn()

    def _build_move(self, from_square: int, to_square: int) -> chess.Move | None:
        board = self.session.state.board
        source_piece = board.piece_at(from_square)
        if source_piece is None:
            return None

        promotions: tuple[int | None, ...] = (None,)
        if source_piece.piece_type == chess.PAWN:
            last_rank = 7 if source_piece.color == chess.WHITE else 0
            if chess.square_rank(to_square) == last_rank:
                promotions = (chess.QUEEN, chess.ROOK, chess.BISHOP, chess.KNIGHT)

        for promotion in promotions:
            move = chess.Move(from_square, to_square, promotion=promotion)
            if move in board.legal_moves:
                return move
        return None

    def _legal_targets(self) -> set[int]:
        if self.selected_square is None:
            return set()
        board = self.session.state.board
        targets: set[int] = set()
        for move in board.legal_moves:
            if move.from_square == self.selected_square:
                targets.add(move.to_square)
        return targets

    def _maybe_ai_turn(self) -> None:
        while not self.session.state.board.is_game_over() and self.session.state.board.turn == self.session.ai_color:
            messages = self.session.ai_move()
            for message in messages:
                self._append_message(message)
            self.refresh_all()

    def _force_ai_turn(self) -> None:
        if self.session.state.board.is_game_over():
            self._append_message("The game is over.")
            return
        if self.session.state.board.turn != self.session.ai_color:
            self._append_message("It is not the AI's turn yet.")
            return
        self._maybe_ai_turn()

    def _save_game(self) -> None:
        name = self.save_entry.get().strip() or "autosave"
        try:
            path = self.session.save(name)
            self._append_message(f"Saved to {path.as_posix()}")
        except Exception as exc:
            self._append_message(f"Save failed: {exc}")

    def _load_game(self) -> None:
        name = self.save_entry.get().strip()
        if not name:
            messagebox.showinfo("Boss Chess", "Enter a save name first.")
            return
        try:
            path = self.session.load(name)
            self.selected_square = None
            self._append_message(f"Loaded {path.as_posix()}")
            self._sync_mode_checkboxes()
            self.refresh_all()
            self._maybe_ai_turn()
        except Exception as exc:
            self._append_message(f"Load failed: {exc}")

    def _sync_mode_checkboxes(self) -> None:
        self.trainer_var.set(self.session.config.trainer)
        self.meme_var.set(self.session.config.meme)
        self.cheat_var.set(self.session.config.cheat)
        self.theme_var.set(self.theme.name)

    def _new_game(self) -> None:
        if not messagebox.askyesno("Boss Chess", "Start a new game?"):
            return
        self.session.reset()
        self.selected_square = None
        self._append_message("New game started.")
        self._sync_mode_checkboxes()
        self.refresh_all()
        self._maybe_ai_turn()

    def _undo(self) -> None:
        self._append_message(self.session.undo())
        self.selected_square = None
        self.refresh_all()

    def _show_eval(self) -> None:
        self.eval_var.set(self.session.evaluation_text())
        self._append_message("Evaluation updated.")

    def _show_pgn(self) -> None:
        self._append_message(self.session.pgn_text() or "(no moves yet)")

    def _game_over_text(self) -> str:
        board = self.session.state.board
        if board.is_checkmate():
            winner = "White" if board.turn == chess.BLACK else "Black"
            return f"Checkmate. {winner} wins."
        if board.is_stalemate():
            return "Stalemate."
        if board.is_insufficient_material():
            return "Draw by insufficient material."
        return f"Game over: {board.result(claim_draw=True)}"

    def _append_message(self, text: str) -> None:
        if not text:
            return
        self.message_lines.append(text)
        self.message_lines = self.message_lines[-20:]
        self._refresh_messages()

    def _kick_ai_if_needed(self) -> None:
        if self.session.state.board.turn == self.session.ai_color and not self.session.state.board.is_game_over():
            self._maybe_ai_turn()
        self.root.after(150, self._kick_ai_if_needed)
