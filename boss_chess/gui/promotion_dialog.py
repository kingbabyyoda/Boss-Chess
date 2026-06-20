from __future__ import annotations

import tkinter as tk
from tkinter import ttk

import chess


PROMOTION_LABELS = {
    chess.QUEEN: "Queen",
    chess.ROOK: "Rook",
    chess.BISHOP: "Bishop",
    chess.KNIGHT: "Knight",
}


class PromotionDialog:
    def __init__(self, parent: tk.Tk, color: chess.Color):
        self.parent = parent
        self.color = color
        self.result: int | None = None

        self.window = tk.Toplevel(parent)
        self.window.title("Choose Promotion")
        self.window.transient(parent)
        self.window.grab_set()
        self.window.resizable(False, False)
        self.window.configure(bg="#0f172a")

        frame = ttk.Frame(self.window, padding=14)
        frame.pack(fill="both", expand=True)

        title = "Promote pawn to"
        ttk.Label(frame, text=title, font=("Segoe UI", 13, "bold")).pack(anchor="w")
        ttk.Label(frame, text="Pick the piece for your pawn promotion.").pack(anchor="w", pady=(2, 12))

        button_row = ttk.Frame(frame)
        button_row.pack(fill="x")
        for piece_type in (chess.QUEEN, chess.ROOK, chess.BISHOP, chess.KNIGHT):
            ttk.Button(button_row, text=PROMOTION_LABELS[piece_type], command=lambda pt=piece_type: self._choose(pt)).pack(side="left", padx=(0, 8))

        ttk.Button(frame, text="Cancel", command=self._cancel).pack(anchor="e", pady=(12, 0))
        self.window.protocol("WM_DELETE_WINDOW", self._cancel)

    def _choose(self, piece_type: int) -> None:
        self.result = piece_type
        self.window.destroy()

    def _cancel(self) -> None:
        self.result = None
        self.window.destroy()
