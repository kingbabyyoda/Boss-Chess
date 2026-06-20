from __future__ import annotations

import tkinter as tk
from tkinter import messagebox

from boss_chess.gui.window import BossChessApp
from boss_chess.types import GameConfig


class ProductionBossChessApp(BossChessApp):
    def __init__(self, session):
        super().__init__(session)
        self._install_menu_bar()
        self.root.protocol("WM_DELETE_WINDOW", self._confirm_exit)
        self._append_message("Production shell loaded.")
        self.refresh_all()

    def _install_menu_bar(self) -> None:
        menubar = tk.Menu(self.root)

        file_menu = tk.Menu(menubar, tearoff=False)
        file_menu.add_command(label="New Game", command=self._new_game, accelerator="Ctrl+N")
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
        self.root.bind_all("<Control-n>", lambda _event: self._new_game())
        self.root.bind_all("<Control-s>", lambda _event: self._save_game())
        self.root.bind_all("<Control-o>", lambda _event: self._load_game())
        self.root.bind_all("<Control-z>", lambda _event: self._undo())
        self.root.bind_all("<Control-f>", lambda _event: self._flip_board())
        self.root.bind_all("<Control-e>", lambda _event: self._show_eval())

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
