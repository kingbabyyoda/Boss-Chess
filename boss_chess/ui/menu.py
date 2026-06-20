from __future__ import annotations

from copy import deepcopy

from boss_chess.types import GameConfig, GameVariant


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


def ask_choice(prompt: str, choices: list[str], default_index: int = 0) -> str:
    while True:
        options = "/".join(f"{choice}" if i != default_index else f"[{choice}]" for i, choice in enumerate(choices))
        response = input(f"{prompt} {options} ").strip().lower()
        if not response:
            return choices[default_index]
        for choice in choices:
            if response == choice.lower():
                return choice
        print(f"Choose one of: {', '.join(choices)}")


def configure_game(base_config: GameConfig | None = None) -> GameConfig:
    config = deepcopy(base_config) if base_config is not None else GameConfig()
    print("Choose your modes:")
    config.trainer = ask_bool("Enable trainer mode?", config.trainer)
    config.meme = ask_bool("Enable meme mode?", config.meme)
    config.cheat = ask_bool("Enable cheat mode?", config.cheat)
    config.ai_plays_white = ask_bool("Should the AI play White?", config.ai_plays_white)

    print("\nGame variant:")
    variant_choice = ask_choice("Select variant", ["standard", "chess960", "king_of_the_hill", "three_check", "atomic", "racing_kings"], config.variant.name.value and ["standard", "chess960", "king_of_the_hill", "three_check", "atomic", "racing_kings"].index(config.variant.name.value))
    config.variant.name = GameVariant(variant_choice)
    if variant_choice == "chess960":
        config.variant.chess960_seed = ask_int("Chess960 seed", config.variant.chess960_seed, 0, 959)

    print("\nMultiplayer:")
    mp_mode = ask_choice("Multiplayer mode", ["offline", "host", "join"], ["offline", "host", "join"].index(config.multiplayer.mode) if config.multiplayer.mode in {"offline", "host", "join"} else 0)
    config.multiplayer.mode = mp_mode
    mp_username = input(f"Username [{config.multiplayer.username}] ").strip() or config.multiplayer.username
    config.multiplayer.username = mp_username
    if mp_mode == "join":
        config.multiplayer.host = input(f"Host address [{config.multiplayer.host}] ").strip() or config.multiplayer.host
        config.multiplayer.port = ask_int("Host port", config.multiplayer.port, 1, 65535)
    elif mp_mode == "host":
        config.multiplayer.port = ask_int("Listen port", config.multiplayer.port, 1, 65535)

    print("\nStrong AI settings:")
    config.engine.depth = ask_int("Search depth (higher = stronger, slower)", config.engine.depth, 1, 8)
    config.engine.use_opening_book = ask_bool("Use the built-in opening book?", config.engine.use_opening_book)
    config.engine.use_stockfish = ask_bool("Use Stockfish if available?", config.engine.use_stockfish)
    if config.engine.use_stockfish:
        config.engine.stockfish_path = input(f"Stockfish path [{config.engine.stockfish_path or ''}] ").strip() or config.engine.stockfish_path
    config.engine.target_elo = ask_int("Target Elo (approx)", config.engine.target_elo, 400, 3500)
    config.engine.multi_pv = ask_int("Analysis lines to show", config.engine.multi_pv, 1, 5)

    print("\nAppearance and accessibility:")
    config.piece_set = ask_choice("Piece set", ["Classic", "Slate", "Neon"], ["Classic", "Slate", "Neon"].index(config.piece_set) if config.piece_set in {"Classic", "Slate", "Neon"} else 0)
    config.ui_scale = float(ask_choice("UI scale", ["0.9", "1.0", "1.15", "1.3"], ["0.9", "1.0", "1.15", "1.3"].index(f"{config.ui_scale:g}" if f"{config.ui_scale:g}" in {"0.9", "1.0", "1.15", "1.3"} else "1.0")))
    config.reduce_motion = ask_bool("Reduce motion?", config.reduce_motion)
    config.high_contrast = ask_bool("High contrast mode?", config.high_contrast)
    if config.high_contrast:
        config.piece_set = "Neon"

    return config
