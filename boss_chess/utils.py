from __future__ import annotations

import random
from typing import Iterable

import chess


def square_name(square: int) -> str:
    return chess.square_name(square)


def pick(items: Iterable[str], fallback: str = "") -> str:
    seq = list(items)
    if not seq:
        return fallback
    return random.choice(seq)
