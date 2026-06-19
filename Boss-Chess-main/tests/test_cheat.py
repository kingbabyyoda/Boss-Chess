import chess
from boss_chess.cheat_events.core import CheatController


def test_cheat_controller_initializes():
    cheat = CheatController()
    assert cheat.last_event
    assert cheat.extra_turns == 0


def test_cheat_controller_can_apply():
    board = chess.Board()
    cheat = CheatController()
    cheat.apply(board, chess.BLACK)
    assert isinstance(board, chess.Board)
