from __future__ import annotations

import chess

from boss_chess.engine.engine import ChessEngine
from boss_chess.trainer.analysis import Trainer
from boss_chess.trainer.openings import OpeningRecognizer


def test_opening_recognizer_identifies_italian_game() -> None:
    board = chess.Board()
    for uci in ["e2e4", "e7e5", "g1f3", "b8c6", "f1c4"]:
        board.push(chess.Move.from_uci(uci))

    recognizer = OpeningRecognizer()
    assert recognizer.identify(list(board.move_stack)) == "Italian Game"
    assert "development" in recognizer.suggest_plan(board).lower()


def test_trainer_produces_report_and_practice_prompt() -> None:
    engine = ChessEngine(depth=2, use_opening_book=True, use_stockfish=False)
    trainer = Trainer(engine)
    board = chess.Board()

    report_text = trainer.report_text(board)
    lesson_text = trainer.lesson_text(board)
    prompt = trainer.practice_prompt(board)

    assert "Opening:" in report_text
    assert "Average accuracy" in report_text or "No trainer reviews" in report_text
    assert "Opening:" in lesson_text
    assert prompt.board_fen == board.fen()
    assert prompt.target_move
    assert prompt.clue
