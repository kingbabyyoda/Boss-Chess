from __future__ import annotations

import chess

from boss_chess.cheat_events.core import CheatController


def test_boss_takes_damage_when_own_piece_is_captured() -> None:
    controller = CheatController(boss_hp=1000, boss_max_hp=1000)
    piece = chess.Piece(chess.QUEEN, chess.BLACK)

    controller.note_capture(piece, ai_color=chess.BLACK)

    assert controller.boss_hp < 1000
    assert controller.boss_phase >= 1


def test_boss_controller_round_trips_through_dict() -> None:
    controller = CheatController(
        boss_name="The Neon Tyrant",
        boss_hp=240,
        boss_max_hp=1000,
        boss_phase=4,
        boss_intro_shown=True,
        extra_turns=3,
        chaos_level=9,
    )
    data = controller.to_dict()
    restored = CheatController.from_dict(data)

    assert restored.boss_name == controller.boss_name
    assert restored.boss_hp == controller.boss_hp
    assert restored.boss_phase == controller.boss_phase
    assert restored.extra_turns == controller.extra_turns
    assert restored.chaos_level == controller.chaos_level


def test_boss_banner_mentions_health_and_phase() -> None:
    controller = CheatController(boss_name="The Chrome King", boss_hp=500, boss_max_hp=1000, boss_phase=2)
    banner = controller.boss_banner()

    assert banner[0] == "Boss Fight: The Chrome King"
    assert "Phase: Escalation" in banner[1]
    assert "500/1000" in banner[2]
