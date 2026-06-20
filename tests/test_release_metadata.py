from __future__ import annotations

from boss_chess import __version__
from boss_chess.cli import main as cli_main


def test_package_version_is_pinned() -> None:
    assert __version__ == "0.2.0"


def test_installable_cli_exists() -> None:
    assert callable(cli_main)
