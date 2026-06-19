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
    depth = ask_int("Search depth (higher = stronger, slower)", 3, 1, 5)

    config = GameConfig()
    config.trainer = trainer
    config.meme = meme
    config.cheat = cheat
    config.ai_plays_white = ai_white
    config.engine.depth = depth
    return config
