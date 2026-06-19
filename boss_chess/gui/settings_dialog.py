from __future__ import annotations

from dataclasses import dataclass

import tkinter as tk
from tkinter import ttk

from boss_chess.types import GameConfig


@dataclass(slots=True)
class SettingsResult:
    saved: bool
    depth: int
    use_stockfish: bool
    use_opening_book: bool
    target_elo: int
    multi_pv: int
    trainer: bool
    meme: bool
    cheat: bool
    theme: str


class SettingsDialog:
    def __init__(self, parent: tk.Tk, config: GameConfig, theme_name: str):
        self.parent = parent
        self.config = config
        self.theme_name = theme_name
        self.result: SettingsResult | None = None
        self.window = tk.Toplevel(parent)
        self.window.title("Boss Chess Settings")
        self.window.transient(parent)
        self.window.grab_set()
        self.window.resizable(False, False)

        self.depth_var = tk.IntVar(value=config.engine.depth)
        self.stockfish_var = tk.BooleanVar(value=config.engine.use_stockfish)
        self.book_var = tk.BooleanVar(value=config.engine.use_opening_book)
        self.elo_var = tk.IntVar(value=config.engine.target_elo)
        self.multi_pv_var = tk.IntVar(value=config.engine.multi_pv)
        self.trainer_var = tk.BooleanVar(value=config.trainer)
        self.meme_var = tk.BooleanVar(value=config.meme)
        self.cheat_var = tk.BooleanVar(value=config.cheat)
        self.theme_var = tk.StringVar(value=theme_name)

        frame = ttk.Frame(self.window, padding=12)
        frame.pack(fill="both", expand=True)

        row = 0
        self._label_entry(frame, "Search depth", self.depth_var, row); row += 1
        self._check(frame, "Use Stockfish", self.stockfish_var, row); row += 1
        self._check(frame, "Use opening book", self.book_var, row); row += 1
        self._label_entry(frame, "Target Elo", self.elo_var, row); row += 1
        self._label_entry(frame, "Analysis lines", self.multi_pv_var, row); row += 1
        self._check(frame, "Trainer", self.trainer_var, row); row += 1
        self._check(frame, "Meme", self.meme_var, row); row += 1
        self._check(frame, "Cheat", self.cheat_var, row); row += 1

        ttk.Label(frame, text="Theme").grid(row=row, column=0, sticky="w", pady=4)
        ttk.Combobox(frame, textvariable=self.theme_var, values=["Classic", "Midnight", "Neon"], state="readonly", width=16).grid(row=row, column=1, sticky="w", pady=4)
        row += 1

        buttons = ttk.Frame(frame)
        buttons.grid(row=row, column=0, columnspan=2, sticky="e", pady=(12, 0))
        ttk.Button(buttons, text="Cancel", command=self._cancel).pack(side="right", padx=(6, 0))
        ttk.Button(buttons, text="Save", command=self._save).pack(side="right")

        self.window.protocol("WM_DELETE_WINDOW", self._cancel)

    def _label_entry(self, parent: ttk.Frame, label: str, variable: tk.Variable, row: int) -> None:
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", pady=4)
        ttk.Entry(parent, textvariable=variable, width=18).grid(row=row, column=1, sticky="w", pady=4)

    def _check(self, parent: ttk.Frame, label: str, variable: tk.BooleanVar, row: int) -> None:
        ttk.Checkbutton(parent, text=label, variable=variable).grid(row=row, column=0, columnspan=2, sticky="w", pady=2)

    def _save(self) -> None:
        self.result = SettingsResult(
            saved=True,
            depth=int(self.depth_var.get()),
            use_stockfish=bool(self.stockfish_var.get()),
            use_opening_book=bool(self.book_var.get()),
            target_elo=int(self.elo_var.get()),
            multi_pv=int(self.multi_pv_var.get()),
            trainer=bool(self.trainer_var.get()),
            meme=bool(self.meme_var.get()),
            cheat=bool(self.cheat_var.get()),
            theme=str(self.theme_var.get()),
        )
        self.window.destroy()

    def _cancel(self) -> None:
        self.result = SettingsResult(
            saved=False,
            depth=self.config.engine.depth,
            use_stockfish=self.config.engine.use_stockfish,
            use_opening_book=self.config.engine.use_opening_book,
            target_elo=self.config.engine.target_elo,
            multi_pv=self.config.engine.multi_pv,
            trainer=self.config.trainer,
            meme=self.config.meme,
            cheat=self.config.cheat,
            theme=self.theme_name,
        )
        self.window.destroy()
