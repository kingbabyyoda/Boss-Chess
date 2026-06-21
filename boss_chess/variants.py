from __future__ import annotations

from enum import Enum

import chess

try:
    import chess.variant as chess_variant
except Exception:  # pragma: no cover
    chess_variant = None


class GameVariant(str, Enum):
    STANDARD = "standard"
    CHESS960 = "chess960"
    KING_OF_THE_HILL = "king_of_the_hill"
    THREE_CHECK = "three_check"
    ATOMIC = "atomic"
    RACING_KINGS = "racing_kings"


VARIANT_LABELS = {
    GameVariant.STANDARD.value: "Standard",
    GameVariant.CHESS960.value: "Chess960",
    GameVariant.KING_OF_THE_HILL.value: "King of the Hill",
    GameVariant.THREE_CHECK.value: "Three-check",
    GameVariant.ATOMIC.value: "Atomic",
    GameVariant.RACING_KINGS.value: "Racing Kings",
}


_VARIANT_ALIASES = {
    "standard": GameVariant.STANDARD,
    "chess960": GameVariant.CHESS960,
    "chess_960": GameVariant.CHESS960,
    "king_of_the_hill": GameVariant.KING_OF_THE_HILL,
    "kingofthehill": GameVariant.KING_OF_THE_HILL,
    "king of the hill": GameVariant.KING_OF_THE_HILL,
    "three_check": GameVariant.THREE_CHECK,
    "threecheck": GameVariant.THREE_CHECK,
    "three-check": GameVariant.THREE_CHECK,
    "atomic": GameVariant.ATOMIC,
    "racing_kings": GameVariant.RACING_KINGS,
    "racingkings": GameVariant.RACING_KINGS,
    "racing kings": GameVariant.RACING_KINGS,
}


def normalize_variant(value: str | GameVariant) -> GameVariant:
    if isinstance(value, GameVariant):
        return value
    raw = str(value).strip().lower()
    key = raw.replace("-", " ").replace("_", " ")
    key = " ".join(key.split())
    compact = key.replace(" ", "")
    return _VARIANT_ALIASES.get(raw) or _VARIANT_ALIASES.get(key) or _VARIANT_ALIASES.get(compact) or GameVariant.STANDARD


def variant_label(value: str | GameVariant) -> str:
    return VARIANT_LABELS.get(normalize_variant(value).value, "Standard")


def create_board(variant: str | GameVariant = GameVariant.STANDARD, starting_fen: str | None = None, chess960_seed: int = 0) -> chess.Board:
    variant_enum = normalize_variant(variant)
    if variant_enum == GameVariant.STANDARD:
        return chess.Board(starting_fen or chess.STARTING_FEN)
    if variant_enum == GameVariant.CHESS960:
        factory = getattr(chess.Board, "from_chess960_pos", None)
        if callable(factory):
            try:
                return factory(max(0, min(959, int(chess960_seed))))
            except Exception:
                pass
        return chess.Board(starting_fen or chess.STARTING_FEN, chess960=True)

    if chess_variant is not None:
        names = {
            GameVariant.KING_OF_THE_HILL: "KingOfTheHillBoard",
            GameVariant.THREE_CHECK: "ThreeCheckBoard",
            GameVariant.ATOMIC: "AtomicBoard",
            GameVariant.RACING_KINGS: "RacingKingsBoard",
        }
        cls_name = names.get(variant_enum)
        if cls_name and hasattr(chess_variant, cls_name):
            return getattr(chess_variant, cls_name)()

    return chess.Board(starting_fen or chess.STARTING_FEN)
