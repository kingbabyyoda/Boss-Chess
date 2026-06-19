from __future__ import annotations

from pathlib import Path

import chess

from boss_chess.replay import export_pgn, load_pgn
from boss_chess.stats import SessionStats
from boss_chess.state import GameState


def test_pgn_export_and_import_round_trip(tmp_path: Path) -> None:
    state = GameState()
    for uci in ["e2e4", "e7e5", "g1f3", "b8c6"]:
        state.push(chess.Move.from_uci(uci))

    pgn_path = tmp_path / "game.pgn"
    summary = export_pgn(state, pgn_path)
    restored = load_pgn(pgn_path)

    assert summary.ply_count == 4
    assert pgn_path.exists()
    assert restored.move_history == state.move_history
    assert restored.board.fen() == state.board.fen()


def test_session_stats_unlocks_basic_achievements() -> None:
    stats = SessionStats()
    stats.record_move("Italian Game")
    stats.record_move("Queen's Gambit")
    stats.record_move("Sicilian Defense")
    stats.record_game_end("1-0", winner=chess.WHITE, checkmate=True)

    unlocked = {achievement.key for achievement in stats.unlocked_achievements()}

    assert "first_game" in unlocked
    assert "first_win" in unlocked
    assert "first_checkmate" in unlocked
    assert "opening_student" in unlocked
