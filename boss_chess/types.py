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


class GameVariant(str, Enum):
    STANDARD = "standard"
    CHESS960 = "chess960"
    KING_OF_THE_HILL = "king_of_the_hill"
    THREE_CHECK = "three_check"
    ATOMIC = "atomic"
    RACING_KINGS = "racing_kings"


@dataclass(slots=True)
class VariantConfig:
    name: GameVariant = GameVariant.STANDARD
    chess960_seed: int = 0


@dataclass(slots=True)
class MultiplayerConfig:
    mode: str = "offline"  # offline, host, join
    host: str = "127.0.0.1"
    port: int = 8765
    username: str = "Player"


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
    ui_scale: float = 1.0
    reduce_motion: bool = False
    high_contrast: bool = False
    piece_set: str = "Classic"
    engine: EngineConfig = field(default_factory=EngineConfig)
    variant: VariantConfig = field(default_factory=VariantConfig)
    multiplayer: MultiplayerConfig = field(default_factory=MultiplayerConfig)


@dataclass(slots=True)
class AnalysisResult:
    best_move: Optional[chess.Move]
    best_score: int
    top_lines: List[tuple[chess.Move, int]]
    summary: str = ""
