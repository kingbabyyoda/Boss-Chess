import chess

from boss_chess.cheat_events.core import CheatController
from boss_chess.persistence import load_game, save_game
from boss_chess.state import GameState
from boss_chess.types import GameConfig


def test_save_and_load_round_trip(tmp_path):
    state = GameState()
    state.push(chess.Move.from_uci("e2e4"))
    state.push(chess.Move.from_uci("e7e5"))

    config = GameConfig(trainer=True, meme=True, cheat=True, ai_plays_white=False)
    cheat = CheatController()
    cheat.last_event = "The board is suspicious."

    path = tmp_path / "save.json"
    save_game(path, state, config, chess.BLACK, cheat)

    loaded = load_game(path)
    assert loaded.state.board.fen() == state.board.fen()
    assert [m.uci() for m in loaded.state.move_history] == ["e2e4", "e7e5"]
    assert loaded.config.trainer is True
    assert loaded.config.meme is True
    assert loaded.config.cheat is True
    assert loaded.ai_color == chess.BLACK
    assert loaded.cheat.last_event == "The board is suspicious."
