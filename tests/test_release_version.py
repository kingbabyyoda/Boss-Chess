from __future__ import annotations

from boss_chess import __version__


def test_release_version_is_one_point_zero_point_zero() -> None:
    assert __version__ == "1.0.0"
