from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import chess
import tkinter as tk
from tkinter import messagebox, ttk

from boss_chess.gui.session import AiMoveOutcome, GuiSession

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
        self.root.geometry("1240x840")
        self.root.minsize(1040, 760)

        self.theme = ThemeState()
        self.flip_board = False
        self.selected_square: int | None = None
        self.square_buttons: dict[int, tk.Button] = {}
        self.message_lines: list[str] = []
        self.animating = False
        self._animation_label: tk.Label | None = None

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

        left = ttk.Frame(container)
        left.pack(side="left", fill="both", expand=False)

        board_toolbar = ttk.Frame(left)
        board_toolbar.pack(fill="x", pady=(0, 8))
        ttk.Button(board_toolbar, text="Flip Board", style="Boss.TButton", command=self._flip_board).pack(side="left")
        ttk.Button(board_toolbar, text="Reset View", style="Boss.TButton", command=self._reset_view).pack(side="left", padx=(8, 0))

        self.board_frame = ttk.Frame(left)
        self.board_frame.pack(fill="both", expand=False)

        side = ttk.Frame(container)
        side.pack(side="right", fill="both", expand=True, padx=(14, 0))

        self.status_var = tk.StringVar(value="")
        self.eval_var = tk.StringVar(value="Press Eval to inspect the position.")
        self.white_captured_var = tk.StringVar(value="White captured: none")
        self.black_captured_var = tk.StringVar(value="Black captured: none")

        status_label = ttk.Label(side, textvariable=self.status_var, style="Boss.TLabel", justify="left")
        status_label.pack(anchor="w")

        eval_wrap = ttk.Labelframe(side, text="Evaluation", style="Boss.TLabelframe")
        eval_wrap.pack(fill="x", pady=(10, 0))
        self.eval_canvas = tk.Canvas(eval_wrap, width=56, height=240, highlightthickness=1, highlightbackground="#555")
        self.eval_canvas.pack(side="left", padx=(0, 10))
        eval_text = ttk.Label(eval_wrap, textvariable=self.eval_var, style="Boss.TLabel", justify="left")
        eval_text.pack(side="left", fill="x", expand=True)

        captured_box = ttk.Labelframe(side, text="Captured Pieces", style="Boss.TLabelframe")
        captured_box.pack(fill="x", pady=(10, 0))
        ttk.Label(captured_box, textvariable=self.white_captured_var, style="Boss.TLabel", justify="left").pack(anchor="w")
        ttk.Label(captured_box, textvariable=self.black_captured_var, style="Boss.TLabel", justify="left").pack(anchor="w", pady=(4, 0))

        self.move_text = tk.Text(side, height=12, wrap="word", font=("Consolas", 10))
        self.move_text.pack(fill="x", pady=(10, 12))
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
        self.sound_var = tk.BooleanVar(value=True)

        ttk.Checkbutton(options, text="Trainer", variable=self.trainer_var, command=self._sync_modes).pack(anchor="w")
        ttk.Checkbutton(options, text="Meme", variable=self.meme_var, command=self._sync_modes).pack(anchor="w")
        ttk.Checkbutton(options, text="Cheat", variable=self.cheat_var, command=self._sync_modes).pack(anchor="w")
        ttk.Checkbutton(options, text="Sound", variable=self.sound_var).pack(anchor="w")

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

        files = range(8) if not self.flip_board else range(7, -1, -1)
        ranks = range(7, -1, -1) if not self.flip_board else range(8)

        for row, rank in enumerate(ranks):
            for col, file in enumerate(files):
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
                button.grid(row=row, column=col, sticky="nsew")
                self.square_buttons[square] = button

        for i in range(8):
            self.board_frame.columnconfigure(i, weight=1)
            self.board_frame.rowconfigure(i, weight=1)

    def refresh_all(self) -> None:
        self._render_board()
        self._refresh_status()
        self._refresh_captured()
        self._refresh_moves()
        self._refresh_messages()
        self._refresh_evaluation_bar()
        if self.session.state.board.is_game_over():
            self.eval_var.set(self._game_over_text())

    def _render_board(self) -> None:
        palette = self.theme.palette
        legal_targets = self._legal_targets()
        last_move = self.session.state.move_history[-1] if self.session.state.move_history else None
        selected = self.selected_square
        board = self.session.state.board
        check_square = board.king(board.turn) if board.is_check() else None

        for square, button in self.square_buttons.items():
            piece = board.piece_at(square)
            label = UNICODE_PIECES.get(piece.symbol(), piece.symbol()) if piece else ""
            button.configure(text=label)

            base = palette["light"] if (chess.square_file(square) + chess.square_rank(square)) % 2 == 0 else palette["dark"]
            if selected == square:
                base = palette["selected"]
            elif square in legal_targets:
                base = palette["hint"]
            elif last_move and square in {last_move.from_square, last_move.to_square}:
                base = "#d4a373"
            elif check_square == square:
                base = "#ff7b7b"

            fg = "#111111"
            if piece and piece.color == chess.BLACK:
                fg = "#f4f4f4"
            button.configure(bg=base, activebackground=base, fg=fg, highlightthickness=0, bd=0)

    def _refresh_status(self) -> None:
        status = self.session.status_text()
        if self.session.state.board.is_checkmate():
            winner = "White" if self.session.state.board.turn == chess.BLACK else "Black"
            status += f"\nCheckmate: {winner} wins."
        self.status_var.set(status)

    def _refresh_captured(self) -> None:
        self.white_captured_var.set(f"White captured: {self._captured_text(self.session.cheat.captured_white, white=True)}")
        self.black_captured_var.set(f"Black captured: {self._captured_text(self.session.cheat.captured_black, white=False)}")

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
        self.message_text.insert("end", "\n\n".join(self.message_lines[-16:]) if self.message_lines else "Ready.")
        self.message_text.configure(state="disabled")

    def _refresh_evaluation_bar(self) -> None:
        self.eval_canvas.delete("all")
        if self.session.state.board.is_game_over():
            self.eval_canvas.create_rectangle(0, 0, 56, 240, fill="#888888", outline="")
            return

        analysis = self.session.engine.analyse(self.session.state.board, max_lines=3)
        self.eval_var.set(f"{analysis.summary}\nBest: {analysis.best_move.uci() if analysis.best_move else 'n/a'}")

        score = max(-1200, min(1200, analysis.best_score))
        height = 240
        width = 56
        white_portion = max(0.0, min(1.0, 0.5 - score / 2400.0))
        split = int(height * white_portion)

        self.eval_canvas.create_rectangle(0, 0, width, split, fill="#f8f8f8", outline="")
        self.eval_canvas.create_rectangle(0, split, width, height, fill="#202020", outline="")
        self.eval_canvas.create_line(0, height // 2, width, height // 2, fill="#666666")
        self.eval_canvas.create_text(width // 2, 16, text="W", fill="#111111")
        self.eval_canvas.create_text(width // 2, height - 16, text="B", fill="#f1f1f1")

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
        if self.animating:
            return
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

        board_before = self.session.state.board.copy(stack=False)
        moving_piece = board_before.piece_at(move.from_square)
        result = self.session.human_move(move)
        self._animate_and_finish(
            move=move,
            piece_symbol=self._piece_symbol(moving_piece),
            on_complete=lambda: self._after_human_move(result),
        )

    def _after_human_move(self, result: str) -> None:
        self._append_message(result)
        self._maybe_signal_event()
        self.refresh_all()
        self.root.after(120, self._maybe_ai_turn)

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
        return {move.to_square for move in board.legal_moves if move.from_square == self.selected_square}

    def _maybe_ai_turn(self) -> None:
        if self.animating or self.session.state.board.is_game_over() or self.session.state.board.turn != self.session.ai_color:
            return

        pre_board = self.session.state.board.copy(stack=False)
        outcome = self.session.ai_move()
        if outcome is None:
            return

        moving_piece = pre_board.piece_at(outcome.move.from_square)
        self._animate_and_finish(
            move=outcome.move,
            piece_symbol=self._piece_symbol(moving_piece),
            on_complete=lambda: self._after_ai_move(outcome),
        )

    def _after_ai_move(self, outcome: AiMoveOutcome) -> None:
        for message in outcome.messages:
            self._append_message(message)
        self._maybe_signal_event()
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
            self.root.after(120, self._maybe_ai_turn)
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
        self.root.after(120, self._maybe_ai_turn)

    def _undo(self) -> None:
        if self.animating:
            return
        self._append_message(self.session.undo())
        self.selected_square = None
        self.refresh_all()

    def _show_eval(self) -> None:
        self.refresh_all()
        self._append_message("Evaluation updated.")

    def _show_pgn(self) -> None:
        self._append_message(self.session.pgn_text() or "(no moves yet)")

    def _captured_text(self, piece_types: list[chess.PieceType], *, white: bool) -> str:
        if not piece_types:
            return "none"
        color = chess.WHITE if white else chess.BLACK
        symbols = [UNICODE_PIECES[chess.Piece(piece_type, color).symbol()] for piece_type in piece_types]
        return " ".join(symbols)

    def _piece_symbol(self, piece: chess.Piece | None) -> str:
        return UNICODE_PIECES.get(piece.symbol(), piece.symbol()) if piece else ""

    def _play_sound(self) -> None:
        if self.sound_var.get():
            try:
                self.root.bell()
            except tk.TclError:
                pass

    def _maybe_signal_event(self) -> None:
        board = self.session.state.board
        if board.is_checkmate() or board.is_check() or self.session.cheat.last_event != "The board is behaving suspiciously.":
            self._play_sound()
        if board.is_checkmate():
            self._append_message("Checkmate!")

    def _animate_and_finish(self, move: chess.Move, piece_symbol: str, on_complete: Callable[[], None]) -> None:
        self.animating = True
        self.root.update_idletasks()

        start_button = self.square_buttons.get(move.from_square)
        end_button = self.square_buttons.get(move.to_square)
        if start_button is None or end_button is None:
            self.animating = False
            on_complete()
            return

        start_button.configure(text="")
        end_button.configure(text="")
        self.root.update_idletasks()

        start_x, start_y = start_button.winfo_x(), start_button.winfo_y()
        end_x, end_y = end_button.winfo_x(), end_button.winfo_y()
        width, height = start_button.winfo_width(), start_button.winfo_height()
        bg = self._square_background(move.from_square)

        if self._animation_label is not None:
            self._animation_label.destroy()

        label = tk.Label(
            self.board_frame,
            text=piece_symbol,
            font=("Segoe UI Symbol", 24),
            bg=bg,
            fg=self._piece_foreground(piece_symbol),
            bd=0,
            highlightthickness=0,
        )
        self._animation_label = label
        label.place(x=start_x, y=start_y, width=width, height=height)

        steps = 10
        duration_ms = 16

        def step(index: int) -> None:
            fraction = index / steps
            x = start_x + (end_x - start_x) * fraction
            y = start_y + (end_y - start_y) * fraction
            label.place(x=x, y=y, width=width, height=height)
            if index < steps:
                self.root.after(duration_ms, lambda: step(index + 1))
                return
            label.destroy()
            self._animation_label = None
            self.animating = False
            on_complete()

        step(0)

    def _square_background(self, square: int) -> str:
        palette = self.theme.palette
        return palette["light"] if (chess.square_file(square) + chess.square_rank(square)) % 2 == 0 else palette["dark"]

    def _piece_foreground(self, piece_symbol: str) -> str:
        if not piece_symbol:
            return "#111111"
        return "#f4f4f4" if piece_symbol.islower() else "#111111"

    def _flip_board(self) -> None:
        if self.animating:
            return
        self.flip_board = not self.flip_board
        self._build_board()
        self.refresh_all()

    def _reset_view(self) -> None:
        if self.animating:
            return
        self.flip_board = False
        self.theme.name = "Classic"
        self._build_board()
        self.theme_var.set(self.theme.name)
        self.refresh_all()

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
        if self.animating:
            self.root.after(120, self._kick_ai_if_needed)
            return
        if self.session.state.board.turn == self.session.ai_color and not self.session.state.board.is_game_over():
            self._maybe_ai_turn()
        self.root.after(150, self._kick_ai_if_needed)
