from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import chess

from boss_chess.cheat_events.core import CheatController
from boss_chess.engine.engine import ChessEngine
from boss_chess.memes.provider import MemeProvider
from boss_chess.persistence import load_game, save_game
from boss_chess.state import GameState
from boss_chess.trainer.analysis import Trainer
from boss_chess.types import GameConfig


@dataclass(slots=True)
class AiMoveOutcome:
    move: chess.Move
    messages: list[str]


@dataclass(slots=True)
class GuiSession:
    config: GameConfig
    state: GameState = field(default_factory=GameState)
    engine: ChessEngine = field(init=False)
    trainer: Trainer = field(init=False)
    memes: MemeProvider = field(default_factory=MemeProvider)
    cheat: CheatController = field(default_factory=CheatController)
    ai_color: chess.Color = field(init=False)
    saves_dir: Path = field(default_factory=lambda: Path("saves"))

    def __post_init__(self) -> None:
        self.engine = self._build_engine()
        self.trainer = Trainer(self.engine)
        self.ai_color = chess.BLACK if not self.config.ai_plays_white else chess.WHITE)
        self.saves_dir.mkdir(parents=True, exist_ok=True)
