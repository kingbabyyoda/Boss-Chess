from __future__ import annotations

import argparse


def _choose_interface() -> str:
    while True:
        response = input("Launch terminal or GUI? [terminal/gui] ").strip().lower()
        if response in {"terminal", "t", "term"}:
            return "terminal"
        if response in {"gui", "g", "window"}:
            return "gui"
        print("Please type 'terminal' or 'gui'.")


def main() -> int:
    try:
        from boss_chess.ui.menu import configure_game
        from boss_chess.game import run_game
    except ModuleNotFoundError as exc:
        missing = exc.name or "a required package"
        print(f"Missing dependency: {missing}")
        print("Install requirements with: pip install -r requirements.txt")
        return 1

    parser = argparse.ArgumentParser(prog="boss-chess", add_help=True)
    parser.add_argument("--gui", action="store_true", help="Start the graphical interface")
    parser.add_argument("--terminal", action="store_true", help="Start the terminal interface")
    args = parser.parse_args()

    print("Boss Chess")
    print("A modular chess project with variants, multiplayer, trainer, meme, cheat, and GUI modes.")
    config = configure_game()

    interface = "terminal"
    if args.gui and not args.terminal:
        interface = "gui"
    elif args.terminal and not args.gui:
        interface = "terminal"
    elif not args.gui and not args.terminal:
        interface = _choose_interface()

    if config.multiplayer.mode in {"host", "join"} and interface == "gui":
        print("Multiplayer is currently terminal-first, so the GUI launcher will switch to terminal mode.")
        interface = "terminal"

    if interface == "gui":
        try:
            from boss_chess.gui.app import run_gui
        except ModuleNotFoundError as exc:
            missing = exc.name or "tkinter"
            print(f"GUI unavailable: {missing}")
            print("Falling back to terminal mode.")
            run_game(config)
            return 0
        run_gui(config)
    else:
        run_game(config)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
