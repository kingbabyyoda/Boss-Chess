from __future__ import annotations

import tkinter as tk
from tkinter import messagebox

from boss_chess.gui.window import BossChessApp


class ProductionBossChessApp(BossChessApp):
    def __init__(self, session):
        super().__init__(session)
        self._install_menu_bar()
        self._install_quick_actions()
        self._install_status_strip()
        self.root.protocol("WM_DELETE_WINDOW", self._confirm_exit)
        self._append_message("Production shell loaded.")
        self.refresh_all()

    def _install_quick_actions(self) -> None:
        palette = self.theme.palette
        self.quick_bar = tk.Frame(self.header, bg=palette["window"], highlightthickness=1, highlightbackground=palette["panel_border"])
        self.quick_bar.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(10, 0))
        for i in range(6):
            self.quick_bar.columnconfigure(i, weight=0)
        self.quick_bar.columnconfigure(6, weight=1)

        tk.Label(
            self.quick_bar,
            text="Quick actions",
            bg=palette["window"],
            fg=palette["muted"],
            font=("Segoe UI", 9, "bold"),
            padx=12,
            pady=8,
        ).grid(row=0, column=0, sticky="w")
        tk.Button(self.quick_bar, text="New Game", command=self._new_game_flow, bg=palette["surface"], fg=palette["text"], bd=0, padx=10, pady=6).grid(row=0, column=1, padx=(0, 6), pady=6)
        tk.Button(self.quick_bar, text="Save", command=self._save_game, bg=palette["surface"], fg=palette["text"], bd=0, padx=10, pady=6).grid(row=0, column=2, padx=(0, 6), pady=6)
        tk.Button(self.quick_bar, text="Load", command=self._load_game, bg=palette["surface"], fg=palette["text"], bd=0, padx=10, pady=6).grid(row=0, column=3, padx=(0, 6), pady=6)
        tk.Button(self.quick_bar, text="Eval", command=self._show_eval, bg=palette["surface"], fg=palette["text"], bd=0, padx=10, pady=6).grid(row=0, column=4, padx=(0, 6), pady=6)
        tk.Button(self.quick_bar, text="Export PGN", command=self._export_pgn, bg=palette["surface"], fg=palette["text"], bd=0, padx=10, pady=6).grid(row=0, column=5, padx=(0, 6), pady=6)
        tk.Button(self.quick_bar, text="About", command=self._show_about, bg=palette["surface"], fg=palette["text"], bd=0, padx=10, pady=6).grid(row=0, column=6, sticky="e", padx=(0, 12), pady=6)

    def _install_status_strip(self) -> None:
        palette = self.theme.palette
        self.root.grid_rowconfigure(1, weight=0)
        self.status_bar = tk.Frame(self.root, bg=palette["surface"], highlightthickness=1, highlightbackground=palette["panel_border"])
        self.status_bar.grid(row=1, column=0, sticky="ew")
        self.status_bar.columnconfigure(0, weight=1)
        self.status_bar.columnconfigure(1, weight=0)
        self.status_bar.columnconfigure(2, weight=0)
        self.status_left = tk.StringVar(value="Ready")
        self.status_center = tk.StringVar(value="Variant: standard")
        self.status_right = tk.StringVar(value="Modes: normal")
        tk.Label(self.status_bar, textvariable=self.status_left, bg=palette["surface"], fg=palette["text"], anchor="w", padx=12, pady=6).grid(row=0, column=0, sticky="ew")
        tk.Label(self.status_bar, textvariable=self.status_center, bg=palette["surface"], fg=palette["muted"], anchor="e", padx=12, pady=6).grid(row=0, column=1, sticky="e")
        tk.Label(self.status_bar, textvariable=self.status_right, bg=palette["surface"], fg=palette["muted"], anchor="e", padx=12, pady=6).grid(row=0, column=2, sticky="e")
        self._refresh_status_strip()

    def _refresh_status_strip(self) -> None:
        board = self.session.state.board
        turn = "White" if board.turn == tk.TRUE else "Black"
        last = self.session.state.move_history[-1].uci() if self.session.state.move_history else "none"
        self.status_left.set(f"Turn: {turn}   Last move: {last}")
        self.status_center.set(f"Variant: {self.session.state.variant}")
        modes = []
        if self.session.config.trainer:
            modes.append("Trainer")
        if self.session.config.meme:
            modes.append("Meme")
        if self.session.config.cheat:
            modes.append("Cheat")
        self.status_right.set("Modes: " + (", ".join(modes) if modes else "Normal"))

    def refresh_all(self) -> None:
        super().refresh_all()
        if hasattr(self, "status_left"):
            self._refresh_status_strip()

    def _install_menu_bar(self) -> None:
        menubar = tk.Menu(self.root)

        file_menu = tk.Menu(menubar, tearoff=False)
        file_menu.add_command(label="New Game", command=self._new_game_flow, accelerator="Ctrl+N")
        file_menu.add_command(label="Save", command=self._save_game, accelerator="Ctrl+S")
        file_menu.add_command(label="Load", command=self._load_game, accelerator="Ctrl+O")
        file_menu.add_separator()
        file_menu.add_command(label="Export PGN", command=self._export_pgn)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self._confirm_exit, accelerator="Alt+F4")
        menubar.add_cascade(label="File", menu=file_menu)

        game_menu = tk.Menu(menubar, tearoff=False)
        game_menu.add_command(label="Undo Move", command=self._undo, accelerator="Ctrl+Z")
        game_menu.add_command(label="Flip Board", command=self._flip_board, accelerator="Ctrl+F")
        game_menu.add_command(label="Reset View", command=self._reset_view)
        game_menu.add_separator()
        game_menu.add_command(label="Show Eval", command=self._show_eval, accelerator="Ctrl+E")
        game_menu.add_command(label="Show Stats", command=self._show_stats)
        game_menu.add_command(label="Opening Explorer", command=self._show_explorer)
        menubar.add_cascade(label="Game", menu=game_menu)

        view_menu = tk.Menu(menubar, tearoff=False)
        view_menu.add_command(label="Theme: Classic", command=lambda: self._set_theme("Classic"))
        view_menu.add_command(label="Theme: Midnight", command=lambda: self._set_theme("Midnight"))
        view_menu.add_command(label="Theme: Neon", command=lambda: self._set_theme("Neon"))
        view_menu.add_separator()
        view_menu.add_command(label="Toggle Trainer", command=self._toggle_trainer)
        view_menu.add_command(label="Toggle Meme", command=self._toggle_meme)
        view_menu.add_command(label="Toggle Cheat", command=self._toggle_cheat)
        menubar.add_cascade(label="View", menu=view_menu)

        help_menu = tk.Menu(menubar, tearoff=False)
        help_menu.add_command(label="Welcome", command=self._show_welcome)
        help_menu.add_command(label="About Boss Chess", command=self._show_about)
        menubar.add_cascade(label="Help", menu=help_menu)

        self.root.config(menu=menubar)
        self.root.bind_all("<Control-n>", lambda _event: self._new_game_flow())
        self.root.bind_all("<Control-s>", lambda _event: self._save_game())
        self.root.bind_all("<Control-o>", lambda _event: self._load_game())
        self.root.bind_all("<Control-z>", lambda _event: self._undo())
        self.root.bind_all("<Control-f>", lambda _event: self._flip_board())
        self.root.bind_all("<Control-e>", lambda _event: self._show_eval())

    def _new_game_flow(self) -> None:
        if not messagebox.askyesno("New Game", "Start a fresh game and discard the current board?"):
            return
        if messagebox.askyesno("New Game", "Reset the camera view and return to Classic theme?"):
            self._reset_view()
        self._new_game()
        self._append_message("New game started.")

    def _toggle_trainer(self) -> None:
        self.trainer_var.set(not self.trainer_var.get())
        self._sync_modes()

    def _toggle_meme(self) -> None:
        self.meme_var.set(not self.meme_var.get())
        self._sync_modes()

    def _toggle_cheat(self) -> None:
        self.cheat_var.set(not self.cheat_var.get())
        self._sync_modes()

    def _show_welcome(self) -> None:
        self._append_message(
            "Welcome to Boss Chess. Use the left board to move, the right panels to review the position, and the menus for file, game, view, and help actions."
        )

    def _show_about(self) -> None:
        messagebox.showinfo(
            "About Boss Chess",
            "Boss Chess\n\nA Python chess app with trainer mode, meme mode, cheat mode, variants, and a polished desktop GUI.\n\nMilestone 12: production shell.",
            parent=self.root,
        )

    def _confirm_exit(self) -> None:
        if messagebox.askyesno("Exit Boss Chess", "Close Boss Chess?"):
            self.root.destroy()
