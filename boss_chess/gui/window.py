from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import chess
import tkinter as tk
from tkinter import messagebox, simpledialog, ttk

from boss_chess.gui.piece_art import build_piece_images
from boss_chess.gui.promotion_dialog import PromotionDialog
from boss_chess.gui.session import AiMoveOutcome, GuiSession
from boss_chess.gui.settings_dialog import SettingsDialog
from boss_chess.types import GameVariant
from boss_chess.variants import variant_label

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
    "Classic": {
        "window": "#f8fafc",
        "surface": "#ffffff",
        "surface_alt": "#f1f5f9",
        "text": "#0f172a",
        "muted": "#64748b",
        "accent": "#2563eb",
        "accent_alt": "#0ea5e9",
        "board_light": "#f0d9b5",
        "board_dark": "#b58863",
        "selected": "#facc15",
        "hint": "#93c5fd",
        "last": "#fb923c",
        "check": "#f87171",
        "panel_border": "#cbd5e1",
        "line": "#dbe4f0",
    },
    "Midnight": {
        "window": "#0f172a",
        "surface": "#111827",
        "surface_alt": "#172036",
        "text": "#e5e7eb",
        "muted": "#94a3b8",
        "accent": "#38bdf8",
        "accent_alt": "#a78bfa",
        "board_light": "#d8dee9",
        "board_dark": "#4c566a",
        "selected": "#7dd3fc",
        "hint": "#a3be8c",
        "last": "#f59e0b",
        "check": "#fb7185",
        "panel_border": "#334155",
        "line": "#334155",
    },
    "Neon": {
        "window": "#06060a",
        "surface": "#0f1118",
        "surface_alt": "#151827",
        "text": "#f8fafc",
        "muted": "#94a3b8",
        "accent": "#22d3ee",
        "accent_alt": "#7c3aed",
        "board_light": "#1b1b25",
        "board_dark": "#0f1020",
        "selected": "#7c3aed",
        "hint": "#22d3ee",
        "last": "#f472b6",
        "check": "#fb7185",
        "panel_border": "#2e2e44",
        "line": "#2e2e44",
    },
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
        self.root.geometry("1380x900")
        self.root.minsize(1180, 800)

        self.theme = ThemeState()
        self.flip_board = False
        self.selected_square: int | None = None
        self.square_buttons: dict[int, tk.Button] = {}
        self.message_lines: list[str] = []
        self.animating = False
        self._animation_label: tk.Label | None = None
        self._piece_images = build_piece_images(self.root, size=74)

        self._setup_styles()
        self._build_ui()
        self._apply_theme()
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
        style.configure("Boss.TButton", padding=(12, 8), font=("Segoe UI", 10, "bold"))
        style.configure("Boss.Primary.TButton", padding=(12, 8), font=("Segoe UI", 10, "bold"))
        style.configure("Boss.TLabelframe", padding=12)
        style.configure("Boss.TLabelframe.Label", font=("Segoe UI", 10, "bold"))
        style.configure("Boss.TLabel", font=("Segoe UI", 10))
        style.configure("Boss.Header.TLabel", font=("Segoe UI", 20, "bold"))
        style.configure("Boss.Subtitle.TLabel", font=("Segoe UI", 10))
        style.configure("Boss.Tag.TLabel", font=("Segoe UI", 9, "bold"))

    def _build_ui(self) -> None:
        self.root.rowconfigure(0, weight=1)
        self.root.columnconfigure(0, weight=1)

        self.main = tk.Frame(self.root, bd=0, highlightthickness=0)
        self.main.grid(row=0, column=0, sticky="nsew")
        self.main.columnconfigure(0, weight=0)
        self.main.columnconfigure(1, weight=1)
        self.main.rowconfigure(1, weight=1)

        self.header = tk.Frame(self.main, bd=0, highlightthickness=0)
        self.header.grid(row=0, column=0, columnspan=2, sticky="ew", padx=16, pady=(16, 10))
        self.header.columnconfigure(0, weight=1)

        self.title_var = tk.StringVar(value="Boss Chess")
        self.subtitle_var = tk.StringVar(value="A polished local chess lab with trainer, meme, cheat, and variant modes.")
        self.mode_badge_var = tk.StringVar(value="")
        ttk.Label(self.header, textvariable=self.title_var, style="Boss.Header.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(self.header, textvariable=self.subtitle_var, style="Boss.Subtitle.TLabel").grid(row=1, column=0, sticky="w", pady=(2, 0))
        ttk.Label(self.header, textvariable=self.mode_badge_var, style="Boss.Tag.TLabel", anchor="e").grid(row=0, column=1, rowspan=2, sticky="e")

        left = tk.Frame(self.main, bd=0, highlightthickness=0)
        left.grid(row=1, column=0, sticky="ns", padx=(16, 12), pady=(0, 16))
        right = tk.Frame(self.main, bd=0, highlightthickness=0)
        right.grid(row=1, column=1, sticky="nsew", padx=(0, 16), pady=(0, 16))
        right.columnconfigure(0, weight=1)

        board_toolbar = tk.Frame(left, bd=0, highlightthickness=0)
        board_toolbar.pack(fill="x", pady=(0, 10))
        ttk.Button(board_toolbar, text="Flip", style="Boss.TButton", command=self._flip_board).pack(side="left")
        ttk.Button(board_toolbar, text="Reset View", style="Boss.TButton", command=self._reset_view).pack(side="left", padx=(8, 0))
        ttk.Button(board_toolbar, text="Settings", style="Boss.Primary.TButton", command=self._open_settings).pack(side="left", padx=(8, 0))

        board_card = ttk.Labelframe(left, text="Board", style="Boss.TLabelframe")
        board_card.pack(fill="both", expand=False)
        self.board_frame = tk.Frame(board_card, bd=0, highlightthickness=0)
        self.board_frame.pack(padx=8, pady=8)

        self.status_var = tk.StringVar(value="")
        self.eval_var = tk.StringVar(value="Press Eval to inspect the position.")
        self.stats_var = tk.StringVar(value="Stats pending.")
        self.white_captured_var = tk.StringVar(value="White captured: none")
        self.black_captured_var = tk.StringVar(value="Black captured: none")

        status_card = ttk.Labelframe(right, text="Status", style="Boss.TLabelframe")
        status_card.grid(row=0, column=0, sticky="ew")
        ttk.Label(status_card, textvariable=self.status_var, style="Boss.TLabel", justify="left").pack(anchor="w")

        row = ttk.Frame(right)
        row.grid(row=1, column=0, sticky="ew", pady=(12, 0))
        row.columnconfigure(0, weight=0)
        row.columnconfigure(1, weight=1)

        eval_wrap = ttk.Labelframe(row, text="Evaluation", style="Boss.TLabelframe")
        eval_wrap.grid(row=0, column=0, sticky="n")
        self.eval_canvas = tk.Canvas(eval_wrap, width=64, height=240, highlightthickness=1, highlightbackground="#555")
        self.eval_canvas.pack(side="left", padx=(0, 10))
        ttk.Label(eval_wrap, textvariable=self.eval_var, style="Boss.TLabel", justify="left").pack(side="left", fill="x", expand=True)

        right_stack = tk.Frame(row, bd=0, highlightthickness=0)
        right_stack.grid(row=0, column=1, sticky="nsew", padx=(12, 0))
        right_stack.columnconfigure(0, weight=1)

        self.history_canvas = tk.Canvas(right_stack, width=500, height=120, highlightthickness=1, highlightbackground="#444")
        self.history_canvas.pack(fill="x")

        captured_box = ttk.Labelframe(right_stack, text="Captured Pieces", style="Boss.TLabelframe")
        captured_box.pack(fill="x", pady=(12, 0))
        ttk.Label(captured_box, textvariable=self.white_captured_var, style="Boss.TLabel", justify="left").pack(anchor="w")
        ttk.Label(captured_box, textvariable=self.black_captured_var, style="Boss.TLabel", justify="left").pack(anchor="w", pady=(4, 0))

        stats_box = ttk.Labelframe(right_stack, text="Stats & Achievements", style="Boss.TLabelframe")
        stats_box.pack(fill="x", pady=(12, 0))
        ttk.Label(stats_box, textvariable=self.stats_var, style="Boss.TLabel", justify="left").pack(anchor="w")

        self.move_text = tk.Text(right_stack, height=9, wrap="word", font=("Consolas", 10), bd=0, highlightthickness=1)
        self.move_text.pack(fill="x", pady=(12, 8))
        self.move_text.configure(state="disabled")

        self.message_text = tk.Text(right_stack, height=11, wrap="word", font=("Consolas", 10), bd=0, highlightthickness=1)
        self.message_text.pack(fill="both", expand=True)
        self.message_text.configure(state="disabled")

        controls = ttk.Labelframe(right_stack, text="Controls", style="Boss.TLabelframe")
        controls.pack(fill="x", pady=(12, 0))

        buttons1 = tk.Frame(controls, bd=0, highlightthickness=0)
        buttons1.pack(fill="x")
        ttk.Button(buttons1, text="New Game", style="Boss.Primary.TButton", command=self._new_game).pack(side="left", padx=(0, 6))
        ttk.Button(buttons1, text="Undo", style="Boss.TButton", command=self._undo).pack(side="left", padx=(0, 6))
        ttk.Button(buttons1, text="AI Move", style="Boss.TButton", command=self._force_ai_turn).pack(side="left", padx=(0, 6))
        ttk.Button(buttons1, text="Eval", style="Boss.TButton", command=self._show_eval).pack(side="left", padx=(0, 6))
        ttk.Button(buttons1, text="PGN", style="Boss.TButton", command=self._show_pgn).pack(side="left")

        buttons2 = tk.Frame(controls, bd=0, highlightthickness=0)
        buttons2.pack(fill="x", pady=(8, 0))
        ttk.Button(buttons2, text="Report", style="Boss.TButton", command=self._show_report).pack(side="left", padx=(0, 6))
        ttk.Button(buttons2, text="Lesson", style="Boss.TButton", command=self._show_lesson).pack(side="left", padx=(0, 6))
        ttk.Button(buttons2, text="Practice", style="Boss.TButton", command=self._show_practice).pack(side="left", padx=(0, 6))
        ttk.Button(buttons2, text="Stats", style="Boss.TButton", command=self._show_stats).pack(side="left", padx=(0, 6))
        ttk.Button(buttons2, text="Explorer", style="Boss.TButton", command=self._show_explorer).pack(side="left")

        buttons3 = tk.Frame(controls, bd=0, highlightthickness=0)
        buttons3.pack(fill="x", pady=(8, 0))
        ttk.Button(buttons3, text="Export PGN", style="Boss.TButton", command=self._export_pgn).pack(side="left", padx=(0, 6))
        ttk.Button(buttons3, text="Save", style="Boss.TButton", command=self._save_game).pack(side="left", padx=(0, 6))
        ttk.Button(buttons3, text="Load", style="Boss.TButton", command=self._load_game).pack(side="left")

        save_row = tk.Frame(controls, bd=0, highlightthickness=0)
        save_row.pack(fill="x", pady=(10, 0))
        ttk.Label(save_row, text="Name:").pack(side="left")
        self.save_entry = ttk.Entry(save_row, width=20)
        self.save_entry.pack(side="left", padx=(8, 0))
        self.save_entry.insert(0, "autosave")

        options = ttk.Labelframe(right_stack, text="Modes & Theme", style="Boss.TLabelframe")
        options.pack(fill="x", pady=(12, 0))
        self.trainer_var = tk.BooleanVar(value=self.session.config.trainer)
        self.meme_var = tk.BooleanVar(value=self.session.config.meme)
        self.cheat_var = tk.BooleanVar(value=self.session.config.cheat)
        self.sound_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(options, text="Trainer", variable=self.trainer_var, command=self._sync_modes).pack(anchor="w")
        ttk.Checkbutton(options, text="Meme", variable=self.meme_var, command=self._sync_modes).pack(anchor="w")
        ttk.Checkbutton(options, text="Cheat", variable=self.cheat_var, command=self._sync_modes).pack(anchor="w")
        ttk.Checkbutton(options, text="Sound", variable=self.sound_var).pack(anchor="w")
        theme_row = tk.Frame(options, bd=0, highlightthickness=0)
        theme_row.pack(fill="x", pady=(8, 0))
        ttk.Label(theme_row, text="Theme:").pack(side="left")
        self.theme_var = tk.StringVar(value=self.theme.name)
        theme_box = ttk.Combobox(theme_row, textvariable=self.theme_var, values=list(THEMES.keys()), state="readonly", width=12)
        theme_box.pack(side="left", padx=(8, 0))
        theme_box.bind("<<ComboboxSelected>>", lambda _event: self._set_theme(self.theme_var.get()))

        self._build_board()

    def _apply_theme(self) -> None:
        palette = self.theme.palette
        self.root.configure(bg=palette["window"])
        self.main.configure(bg=palette["window"])
        self.header.configure(bg=palette["window"])
        self.main['bg'] = palette["window"]
        self._style_text_widget(self.move_text, palette)
        self._style_text_widget(self.message_text, palette)
        self.history_canvas.configure(bg=palette["surface"], highlightbackground=palette["panel_border"])
        self.eval_canvas.configure(bg=palette["surface"], highlightbackground=palette["panel_border"])
        self.board_frame.configure(bg=palette["surface"])
        for child in (self.board_frame,):
            try:
                child.configure(bg=palette["surface"])
            except tk.TclError:
                pass
        self._refresh_board_button_colors()
        self.refresh_all()

    def _style_text_widget(self, widget: tk.Text, palette: dict[str, str]) -> None:
        widget.configure(
            bg=palette["surface"],
            fg=palette["text"],
            insertbackground=palette["text"],
            highlightbackground=palette["panel_border"],
            highlightcolor=palette["accent"],
            relief="solid",
            borderwidth=1,
            padx=10,
            pady=10,
        )

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
                    image="",
                    compound="center",
                    width=74,
                    height=74,
                    bd=0,
                    highlightthickness=0,
                    relief="flat",
                    cursor="hand2",
                    command=lambda sq=square: self._square_clicked(sq),
                )
                button.grid(row=row, column=col, sticky="nsew")
                self.square_buttons[square] = button
        for i in range(8):
            self.board_frame.columnconfigure(i, weight=1)
            self.board_frame.rowconfigure(i, weight=1)

    def refresh_all(self) -> None:
        self._refresh_header()
        self._render_board()
        self._refresh_status()
        self._refresh_captured()
        self._refresh_moves()
        self._refresh_messages()
        self._refresh_stats()
        self._refresh_eval_bar()
        self._draw_eval_history()
        if self.session.state.board.is_game_over():
            self.eval_var.set(self._game_over_text())

    def _refresh_header(self) -> None:
        turn = "White" if self.session.state.board.turn == chess.WHITE else "Black"
        badges = [variant_label(self.session.state.variant), turn, self._mode_line_text()]
        self.mode_badge_var.set("  •  ".join(badges))

    def _mode_line_text(self) -> str:
        active: list[str] = []
        if self.session.config.trainer:
            active.append("Trainer")
        if self.session.config.meme:
            active.append("Meme")
        if self.session.config.cheat:
            active.append("Cheat")
        return ", ".join(active) if active else "Normal"

    def _render_board(self) -> None:
        palette = self.theme.palette
        board = self.session.state.board
        legal_targets = self._legal_targets()
        last_move = board.move_stack[-1] if board.move_stack else None
        selected = self.selected_square
        check_square = board.king(board.turn) if board.is_check() else None

        for square, button in self.square_buttons.items():
            piece = board.piece_at(square)
            image = self._piece_image(piece)
            button.configure(image=image, text="")
            button.image = image
            base = palette["board_light"] if (chess.square_file(square) + chess.square_rank(square)) % 2 == 0 else palette["board_dark"]
            if selected == square:
                base = palette["selected"]
            elif square in legal_targets:
                base = palette["hint"]
            elif last_move and square in {last_move.from_square, last_move.to_square}:
                base = palette["last"]
            elif check_square == square:
                base = palette["check"]
            fg = "#111111" if not piece or piece.color == chess.WHITE else "#f4f4f4"
            button.configure(bg=base, activebackground=base, fg=fg, highlightthickness=0, bd=0)

    def _piece_image(self, piece: chess.Piece | None):
        if piece is None:
            return ""
        return self._piece_images.get(piece.symbol(), "")

    def _refresh_board_button_colors(self) -> None:
        if not self.square_buttons:
            return
        self._render_board()

    def _refresh_status(self) -> None:
        status = self.session.status_text()
        if self.session.state.board.is_checkmate():
            winner = "White" if self.session.state.board.turn == chess.BLACK else "Black"
            status += f"\nCheckmate: {winner} wins."
        self.status_var.set(status)

    def _refresh_captured(self) -> None:
        self.white_captured_var.set(f"White captured: {self._captured_text(self.session.cheat.captured_white, white=True)}")
        self.black_captured_var.set(f"Black captured: {self._captured_text(self.session.cheat.captured_black, white=False)}")

    def _refresh_stats(self) -> None:
        self.stats_var.set(self.session.stats_text())

    def _refresh_moves(self) -> None:
        text = "Moves\n" + (self.session.pgn_text() if self.session.pgn_text() else "(no moves yet)")
        self._set_text(self.move_text, text)

    def _refresh_messages(self) -> None:
        self._set_text(self.message_text, "\n\n".join(self.message_lines[-16:]) if self.message_lines else "Ready.")

    def _refresh_eval_bar(self) -> None:
        palette = self.theme.palette
        self.eval_canvas.delete("all")
        self.eval_canvas.configure(bg=palette["surface"])
        if self.session.state.board.is_game_over():
            self.eval_canvas.create_rectangle(0, 0, 64, 240, fill=palette["surface_alt"], outline="")
            return
        analysis = self.session.engine.analyse(self.session.state.board, max_lines=3)
        self.eval_var.set(f"{analysis.summary}\nBest: {analysis.best_move.uci() if analysis.best_move else 'n/a'}")
        score = max(-1200, min(1200, analysis.best_score))
        white_portion = max(0.0, min(1.0, 0.5 - score / 2400.0))
        split = int(240 * white_portion)
        self.eval_canvas.create_rectangle(0, 0, 64, split, fill=palette["surface_alt"], outline="")
        self.eval_canvas.create_rectangle(0, split, 64, 240, fill=palette["window"], outline="")
        self.eval_canvas.create_line(0, 120, 64, 120, fill=palette["line"])
        self.eval_canvas.create_text(32, 16, text="W", fill=palette["text"])
        self.eval_canvas.create_text(32, 224, text="B", fill=palette["text"])

    def _draw_eval_history(self) -> None:
        palette = self.theme.palette
        self.history_canvas.delete("all")
        self.history_canvas.configure(bg=palette["surface"])
        history = self.session.eval_graph()
        self.history_canvas.create_text(10, 10, anchor="nw", text="Eval history", fill=palette["text"])
        if not history:
            self.history_canvas.create_text(10, 34, anchor="nw", text="No moves yet.", fill=palette["muted"])
            return
        points = history[-40:]
        width = 500
        height = 120
        base_y = height // 2
        self.history_canvas.create_line(0, base_y, width, base_y, fill=palette["line"])
        step = max(1, (width - 30) // max(1, len(points) - 1))
        coords: list[int] = []
        for i, score in enumerate(points):
            x = 16 + i * step
            y = int(base_y - max(-44, min(44, score / 30)))
            coords.extend([x, y])
        if len(coords) >= 4:
            self.history_canvas.create_line(*coords, fill=palette["accent"], width=2)
        self.history_canvas.create_text(390, 10, anchor="nw", text=f"Current: {points[-1] / 100:+.2f}", fill=palette["text"])

    def _set_text(self, widget: tk.Text, value: str) -> None:
        palette = self.theme.palette
        widget.configure(bg=palette["surface"], fg=palette["text"], highlightbackground=palette["panel_border"], highlightcolor=palette["accent"])
        widget.configure(state="normal")
        widget.delete("1.0", "end")
        widget.insert("end", value)
        widget.configure(state="disabled")

    def _set_theme(self, name: str) -> None:
        if name in THEMES:
            self.theme.name = name
            self._apply_theme()

    def _sync_modes(self) -> None:
        self.session.config.trainer = self.trainer_var.get()
        self.session.config.meme = self.meme_var.get()
        self.session.config.cheat = self.cheat_var.get()
        self.session.engine = self.session._build_engine()
        self.session.trainer = self.session.trainer.__class__(self.session.engine)
        self._append_message("Modes updated.")
        self.refresh_all()

    def _open_settings(self) -> None:
        dialog = SettingsDialog(self.root, self.session.config, self.theme.name)
        self.root.wait_window(dialog.window)
        if dialog.result and dialog.result.saved:
            variant_changed = (
                self.session.config.variant.name.value != dialog.result.variant
                or self.session.config.variant.chess960_seed != dialog.result.chess960_seed
            )
            self.session.config.engine.depth = dialog.result.depth
            self.session.config.engine.use_stockfish = dialog.result.use_stockfish
            self.session.config.engine.use_opening_book = dialog.result.use_opening_book
            self.session.config.engine.target_elo = dialog.result.target_elo
            self.session.config.engine.multi_pv = dialog.result.multi_pv
            self.session.config.trainer = dialog.result.trainer
            self.session.config.meme = dialog.result.meme
            self.session.config.cheat = dialog.result.cheat
            self.session.config.variant.name = GameVariant(dialog.result.variant)
            self.session.config.variant.chess960_seed = dialog.result.chess960_seed
            self.theme.name = dialog.result.theme
            self.theme_var.set(self.theme.name)
            self.session.engine = self.session._build_engine()
            self.session.trainer = self.session.trainer.__class__(self.session.engine)
            if variant_changed:
                self.session.reset()
                self._append_message("Variant changed; started a new game.")
            self._apply_theme()
            self.refresh_all()
            self._append_message("Settings updated.")

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
            self._append_message("That move is not legal or promotion was cancelled.")
            self.refresh_all()
            return
        board_before = self.session.state.board.copy(stack=False)
        moving_piece = board_before.piece_at(move.from_square)
        result = self.session.human_move(move)
        self._animate_and_finish(move, self._piece_image(moving_piece), lambda: self._after_human_move(result))

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
                dialog = PromotionDialog(self.root, source_piece.color)
                self.root.wait_window(dialog.window)
                if dialog.result is None:
                    return None
                promotions = (dialog.result,)

        for promotion in promotions:
            move = chess.Move(from_square, to_square, promotion=promotion)
            if move in board.legal_moves:
                return move
        return None

    def _legal_targets(self) -> set[int]:
        if self.selected_square is None:
            return set()
        return {move.to_square for move in self.session.state.board.legal_moves if move.from_square == self.selected_square}

    def _maybe_ai_turn(self) -> None:
        if self.animating or self.session.state.board.is_game_over() or self.session.state.board.turn != self.session.ai_color:
            return
        pre_board = self.session.state.board.copy(stack=False)
        outcome = self.session.ai_move()
        if outcome is None:
            return
        moving_piece = pre_board.piece_at(outcome.move.from_square)
        self._animate_and_finish(outcome.move, self._piece_image(moving_piece), lambda: self._after_ai_move(outcome))

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
            self._apply_theme()
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
        self._apply_theme()
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

    def _show_report(self) -> None:
        self._append_message(self.session.trainer_report_text())

    def _show_lesson(self) -> None:
        self._append_message(self.session.trainer_lesson_text())

    def _show_practice(self) -> None:
        self._append_message(self.session.trainer_puzzle_text())

    def _show_stats(self) -> None:
        self._append_message(self.session.stats_text())

    def _show_explorer(self) -> None:
        self._append_message(self.session.opening_explorer_text())

    def _export_pgn(self) -> None:
        name = simpledialog.askstring("Export PGN", "PGN filename (without extension):", parent=self.root)
        if not name:
            return
        try:
            path = self.session.export_pgn(name)
            self._append_message(f"Exported PGN to {path.as_posix()}")
        except Exception as exc:
            self._append_message(f"PGN export failed: {exc}")

    def _captured_text(self, piece_types: list[chess.PieceType], *, white: bool) -> str:
        if not piece_types:
            return "none"
        color = chess.WHITE if white else chess.BLACK
        return " ".join(UNICODE_PIECES[chess.Piece(piece_type, color).symbol()] for piece_type in piece_types)

    def _maybe_signal_event(self) -> None:
        board = self.session.state.board
        if board.is_check() or board.is_checkmate():
            self.root.bell()
        if board.is_checkmate():
            self._append_message("Checkmate!")
            self.session.game_over_report()

    def _animate_and_finish(self, move: chess.Move, piece_image, on_complete: Callable[[], None]) -> None:
        self.animating = True
        self.root.update_idletasks()
        start_button = self.square_buttons.get(move.from_square)
        end_button = self.square_buttons.get(move.to_square)
        if start_button is None or end_button is None:
            self.animating = False
            on_complete()
            return
        start_button.configure(text="", image="")
        end_button.configure(text="", image="")
        self.root.update_idletasks()
        start_x, start_y = start_button.winfo_x(), start_button.winfo_y()
        end_x, end_y = end_button.winfo_x(), end_button.winfo_y()
        width, height = start_button.winfo_width(), start_button.winfo_height()
        bg = start_button.cget("bg")
        if self._animation_label is not None:
            self._animation_label.destroy()
        label = tk.Label(self.board_frame, image=piece_image, bg=bg, bd=0, highlightthickness=0)
        self._animation_label = label
        label.image = piece_image
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
        return palette["board_light"] if (chess.square_file(square) + chess.square_rank(square)) % 2 == 0 else palette["board_dark"]

    def _piece_foreground(self, piece_symbol: str) -> str:
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
        self._apply_theme()
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

    def _refresh_messages(self) -> None:
        self._set_text(self.message_text, "\n\n".join(self.message_lines[-16:]) if self.message_lines else "Ready.")

    def _kick_ai_if_needed(self) -> None:
        if self.animating:
            self.root.after(120, self._kick_ai_if_needed)
            return
        if self.session.state.board.turn == self.session.ai_color and not self.session.state.board.is_game_over():
            self._maybe_ai_turn()
        self.root.after(150, self._kick_ai_if_needed)
