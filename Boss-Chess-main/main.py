from __future__ import annotations

import sys


def main() -> int:
    try:
        from boss_chess.ui.menu import configure_game
        from boss_chess.game import run_game
    except ModuleNotFoundError as exc:
        missing = exc.name or "a required package"
        print(f"Missing dependency: {missing}")
        print("Install requirements with: pip install -r requirements.txt")
        return 1

    print("Boss Chess")
    print("A modular chess project with normal, trainer, meme, and cheat modes.")
    config = configure_game()
    run_game(config)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
