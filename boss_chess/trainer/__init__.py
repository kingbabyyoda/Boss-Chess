from boss_chess.trainer.analysis import Trainer
from boss_chess.trainer.motifs import MotifResult, TacticalMotifDetector
from boss_chess.trainer.openings import OpeningRecognizer
from boss_chess.trainer.practice import PracticeMode
from boss_chess.trainer.puzzles import PuzzleGenerator
from boss_chess.trainer.report import GameReport, MoveReview, PracticePrompt

__all__ = [
    "Trainer",
    "OpeningRecognizer",
    "TacticalMotifDetector",
    "MotifResult",
    "PracticeMode",
    "PuzzleGenerator",
    "GameReport",
    "MoveReview",
    "PracticePrompt",
]
