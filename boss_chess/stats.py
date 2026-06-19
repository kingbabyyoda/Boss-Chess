from __future__ import annotations

from dataclasses import dataclass, field

import chess


@dataclass(slots=True)
class Achievement:
    key: str
    title: str
    description: str
    unlocked: bool = False


@dataclass(slots=True)
class SessionStats:
    games_played: int = 0
    wins_white: int = 0
    wins_black: int = 0
    draws: int = 0
    moves_played: int = 0
    checkmates: int = 0
    openings_seen: dict[str, int] = field(default_factory=dict)
    achievements: dict[str, Achievement] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.achievements:
            self.achievements = {
                "first_game": Achievement("first_game", "First Game", "Play your first game."),
                "first_win": Achievement("first_win", "First Win", "Win a game against the engine."),
                "first_checkmate": Achievement("first_checkmate", "Checkmate", "Finish a game by checkmate."),
                "opening_student": Achievement("opening_student", "Opening Student", "See 3 different openings."),
                "marathon": Achievement("marathon", "Marathon", "Play 50 moves in a session."),
            }

    def record_move(self, opening_name: str | None = None) -> None:
        self.moves_played += 1
        if opening_name:
            self.openings_seen[opening_name] = self.openings_seen.get(opening_name, 0) + 1
        if self.moves_played >= 1:
            self.unlock("first_game")
        if self.moves_played >= 50:
            self.unlock("marathon")
        if len(self.openings_seen) >= 3:
            self.unlock("opening_student")

    def record_game_end(self, result: str, winner: chess.Color | None = None, checkmate: bool = False) -> None:
        self.games_played += 1
        if result == "1-0":
            self.wins_white += 1
            self.unlock("first_win")
        elif result == "0-1":
            self.wins_black += 1
            self.unlock("first_win")
        else:
            self.draws += 1
        if checkmate:
            self.checkmates += 1
            self.unlock("first_checkmate")

    def unlock(self, key: str) -> None:
        if key in self.achievements:
            self.achievements[key].unlocked = True

    def unlocked_achievements(self) -> list[Achievement]:
        return [achievement for achievement in self.achievements.values() if achievement.unlocked]

    def summary_lines(self) -> list[str]:
        return [
            f"Games played: {self.games_played}",
            f"White wins: {self.wins_white}",
            f"Black wins: {self.wins_black}",
            f"Draws: {self.draws}",
            f"Moves played: {self.moves_played}",
            f"Checkmates: {self.checkmates}",
        ]
