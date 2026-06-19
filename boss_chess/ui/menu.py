from __future__ import annotations

from boss_chess.types import GameConfig


def ask_bool(prompt: str, default: bool = False) -> bool:
    suffix = "[Y/n]" if default else "[y/N]"
    while True:
        response = input(f"{prompt} {suffix} ").strip().lower()
        if not response:
            return default
        if response in {"y", "yes", "true", "1"}:
            return True
        if response in {"n", "no", "false", "0"}:
            return False
        print("Please answer y or n.")


def ask_int(prompt: str, default: int, minimum: int = 1, maximum: int = 8) -> int:
    while True:
        response = input(f"{prompt} [{default}] ").strip()
        if not response:
            return default
        try:
            value = int(response)
        except ValueError:
            value = None
        if value is not None and minimum <= value <= maximum:
            return value
        print(f"Enter a number between {minimum} and {maximum}.")


def configure_game() -> GameConfig:
    print("Choose your modes:")
    trainer = ask_bool("Enable trainer mode?", False)
    meme = ask_bool("Enable meme mode?", False)
    cheat = ask_bool("Enable cheat mode?", False)
    ai_white = ask_bool("Should the AI play White?", False)

    print("\nStrong AI settings:")
    depth = ask_int("Search depth (higher = stronger, slower)", 4, 1, 6)
    use_opening_book = ask_bool("Use the built-in opening book?", True)
    use_stockfish = ask_bool("Use Stockfish if available?", False)
    stockfish_path = None
    if use_stockfish:
        stockfish_path = input("Stockfish path (blank to use STOCKFISH_PATH): ").strip() or None
    target_elo = ask_int("Target Elo (approx)", 1800, 400, 3500)
    multi_pv = ask_int("Analysis lines to show", 3, 1, 5)

    config = GameConfig()
    config.trainer = trainer
    config.meme = meme
    config.cheat = cheat
    config.ai_plays_white = ai_white
    config.engine.depth = depth
    config.engine.use_opening_book = use_opening_book
    config.engine.use_stockfish = use_stockfish
    config.engine.stockfish_path = stockfish_path
    config.engine.target_elo = target_elo
    config.engine.multi_pv = multi_pv
    return config
