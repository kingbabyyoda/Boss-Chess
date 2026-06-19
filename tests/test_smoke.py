from boss_chess.engine.evaluation import evaluate_board
from boss_chess.engine.search import choose_move
import chess


def test_evaluate_starting_board_is_numeric():
    board = chess.Board()
    score = evaluate_board(board)
    assert isinstance(score, int)


def test_choose_move_returns_legal_move():
    board = chess.Board()
    move = choose_move(board, depth=1)
    assert move in board.legal_moves
