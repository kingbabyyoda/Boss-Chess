from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional

import chess


class Mode(str, Enum):
    NORMAL = "normal"
    TRAINER = "trainer"
    MEME = "meme"
    CHEAT = "cheat"


@dataclass(slots=True)
class EngineConfig:
    depth: int = 3
    use_stockfish: bool = False
    stockfish_path: Optional[str] = None
    use_opening_book: bool = True
    target_elo: int = 1800
    multi_pv: int = 3


@dataclass(slots=True)
class GameConfig:
    ai_plays_white: bool = False
    trainer: bool = False
    meme: bool = False
    cheat: bool = False
    engine: EngineConfig = field(default_factory=EngineConfig)


@dataclass(slots=True)
class AnalysisResult:
    best_move: Optional[chess.Move]
    best_score: int
    top_lines: List[tuple[chess.Move, int]]
    summary: str = ""
