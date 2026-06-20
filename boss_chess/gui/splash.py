from __future__ import annotations

import tkinter as tk
from tkinter import ttk


def show_splash(duration_ms: int = 1100) -> None:
    root = tk.Tk()
    root.overrideredirect(True)
    root.attributes("-topmost", True)
    root.configure(bg="#0f172a")

    width, height = 420, 220
    screen_w = root.winfo_screenwidth()
    screen_h = root.winfo_screenheight()
    x = (screen_w - width) // 2
    y = (screen_h - height) // 2
    root.geometry(f"{width}x{height}+{x}+{y}")

    frame = tk.Frame(root, bg="#0f172a", bd=0, highlightthickness=2, highlightbackground="#334155")
    frame.pack(fill="both", expand=True, padx=12, pady=12)

    title = tk.Label(frame, text="Boss Chess", bg="#0f172a", fg="#f8fafc", font=("Segoe UI", 24, "bold"))
    title.pack(pady=(28, 4))
    subtitle = tk.Label(frame, text="Loading chess engine, GUI shell, and game modes...", bg="#0f172a", fg="#94a3b8", font=("Segoe UI", 10))
    subtitle.pack(pady=(0, 18))

    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass
    style.configure("Splash.Horizontal.TProgressbar", troughcolor="#1e293b", background="#38bdf8", thickness=12)

    bar = ttk.Progressbar(frame, mode="indeterminate", style="Splash.Horizontal.TProgressbar")
    bar.pack(fill="x", padx=34, pady=(0, 12))
    bar.start(10)

    footer = tk.Label(frame, text="Version preview", bg="#0f172a", fg="#64748b", font=("Segoe UI", 9))
    footer.pack(side="bottom", pady=(0, 16))

    root.after(duration_ms, root.destroy)
    root.mainloop()
