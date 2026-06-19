from __future__ import annotations

import random
from dataclasses import dataclass, field

import chess

PIECE_DAMAGE = {
    chess.PAWN: 18,
    chess.KNIGHT: 32,
    chess.BISHOP: 34,
    chess.ROOK: 50,
    chess.QUEEN: 90,
    chess.KING: 0,
}

BOSS_NAMES = [
    "The Chrome King",
    "The Neon Tyrant",
    "The Null Bishop",
    "The Algorithm Overlord",
    "The Final Queen",
]


@dataclass(slots=True)
class CheatController:
    last_event: str = "The boss stirs in the dark."
    extra_turns: int = 0
    chaos_level: int = 0
    boss_name: str = field(default_factory=lambda: random.choice(BOSS_NAMES))
    boss_max_hp: int = 1000
    boss_hp: int = 1000
    boss_phase: int = 1
    boss_intro_shown: bool = False
    captured_white: list[chess.PieceType] = field(default_factory=list)
    captured_black: list[chess.PieceType] = field(default_factory=list)
    event_log: list[str] = field(default_factory=list)

    def note_capture(self, piece: chess.Piece | None, ai_color: chess.Color | None = None) -> None:
        if piece is None:
            return
        if piece.color == chess.WHITE:
            self.captured_white.append(piece.piece_type)
        else:
            self.captured_black.append(piece.piece_type)

        if ai_color is None:
            return

        if piece.color == ai_color:
            damage = PIECE_DAMAGE.get(piece.piece_type, 10)
            self.boss_hp = max(0, self.boss_hp - damage)
            self.last_event = f"{self.boss_name} took {damage} damage."
        else:
            heal = max(4, PIECE_DAMAGE.get(piece.piece_type, 10) // 6)
            self.boss_hp = min(self.boss_max_hp, self.boss_hp + heal)
            self.last_event = f"{self.boss_name} fed on the attack and healed {heal}."
        self._sync_phase()

    def to_dict(self) -> dict[str, object]:
        return {
            "last_event": self.last_event,
            "extra_turns": self.extra_turns,
            "chaos_level": self.chaos_level,
            "boss_name": self.boss_name,
            "boss_max_hp": self.boss_max_hp,
            "boss_hp": self.boss_hp,
            "boss_phase": self.boss_phase,
            "boss_intro_shown": self.boss_intro_shown,
            "captured_white": [int(piece_type) for piece_type in self.captured_white],
            "captured_black": [int(piece_type) for piece_type in self.captured_black],
            "event_log": list(self.event_log),
        }

    @classmethod
    def from_dict(cls, data: dict[str, object] | None) -> "CheatController":
        if not isinstance(data, dict):
            return cls()
        controller = cls()
        controller.last_event = str(data.get("last_event", controller.last_event))
        controller.extra_turns = int(data.get("extra_turns", 0))
        controller.chaos_level = int(data.get("chaos_level", 0))
        controller.boss_name = str(data.get("boss_name", controller.boss_name))
        controller.boss_max_hp = max(1, int(data.get("boss_max_hp", controller.boss_max_hp)))
        controller.boss_hp = max(0, min(controller.boss_max_hp, int(data.get("boss_hp", controller.boss_hp))))
        controller.boss_phase = max(1, min(4, int(data.get("boss_phase", controller.boss_phase))))
        controller.boss_intro_shown = bool(data.get("boss_intro_shown", controller.boss_intro_shown))
        controller.captured_white = [chess.PieceType(int(v)) for v in data.get("captured_white", []) if isinstance(v, int) or str(v).isdigit()]
        controller.captured_black = [chess.PieceType(int(v)) for v in data.get("captured_black", []) if isinstance(v, int) or str(v).isdigit()]
        controller.event_log = [str(item) for item in data.get("event_log", []) if item is not None]
        controller._sync_phase()
        return controller

    def boss_meter(self) -> str:
        bar_width = 20
        hp_ratio = 0 if self.boss_max_hp <= 0 else self.boss_hp / self.boss_max_hp
        filled = max(0, min(bar_width, round(hp_ratio * bar_width)))
        bar = "█" * filled + "░" * (bar_width - filled)
        return f"{self.boss_name} HP [{bar}] {self.boss_hp}/{self.boss_max_hp} | Phase {self.boss_phase}/4"

    def intro_line(self) -> str:
        return f"{self.boss_name} awakens. Defeat it by taking its pieces apart."

    def note_victory_pressure(self) -> None:
        self.chaos_level += 1
        self._sync_phase()

    def apply(self, board: chess.Board, ai_color: chess.Color) -> None:
        self.chaos_level += 1
        self._sync_phase()

        if self.boss_phase >= 4:
            self._final_boss(board, ai_color)
            self._push_event_log()
            return

        phase_weights = self._weights_for_phase(self.boss_phase)
        roll = random.random()
        for cutoff, event in phase_weights:
            if roll <= cutoff:
                event(board, ai_color)
                break

        if self.boss_phase >= 3 and random.random() < 0.35:
            self._spawn_piece(board, ai_color, force_queen=True)

        if self.boss_phase >= 2 and random.random() < 0.45:
            self._grant_extra_turn()

        if self.boss_phase >= 3 and random.random() < 0.30:
            self._reality_rewrite(board, ai_color)

        self._push_event_log()

    def _weights_for_phase(self, phase: int):
        if phase <= 1:
            return [
                (0.15, self._delete_enemy_piece),
                (0.30, self._teleport_piece),
                (0.45, self._spawn_piece),
                (0.60, self._duplicate_piece),
                (0.74, self._resurrect_piece),
                (0.84, self._grant_extra_turn),
                (0.92, self._reality_rewrite),
                (1.00, self._boss_phase)
            ]
        if phase == 2:
            return [
                (0.18, self._delete_enemy_piece),
                (0.36, self._teleport_piece),
                (0.54, self._spawn_piece),
                (0.68, self._duplicate_piece),
                (0.80, self._resurrect_piece),
                (0.90, self._grant_extra_turn),
                (1.00, self._boss_phase)
            ]
        return [
            (0.20, self._delete_enemy_piece),
            (0.40, self._spawn_piece),
            (0.56, self._duplicate_piece),
            (0.70, self._resurrect_piece),
            (0.84, self._grant_extra_turn),
            (0.93, self._reality_rewrite),
            (1.00, self._boss_phase)
        ]

    def _sync_phase(self) -> None:
        hp_ratio = 0 if self.boss_max_hp <= 0 else self.boss_hp / self.boss_max_hp
        if hp_ratio > 0.75:
            self.boss_phase = 1
        elif hp_ratio > 0.50:
            self.boss_phase = 2
        elif hp_ratio > 0.25:
            self.boss_phase = 3
        else:
            self.boss_phase = 4

    def _push_event_log(self) -> None:
        self.event_log.append(self.last_event)
        self.event_log = self.event_log[-12:]

    def _enemy_squares(self, board: chess.Board, ai_color: chess.Color) -> list[int]:
        return [sq for sq, piece in board.piece_map().items() if piece.color != ai_color and piece.piece_type != chess.KING]

    def _ai_squares(self, board: chess.Board, ai_color: chess.Color) -> list[int]:
        return [sq for sq, piece in board.piece_map().items() if piece.color == ai_color and piece.piece_type != chess.KING]

    def _empty_squares(self, board: chess.Board) -> list[int]:
        return [sq for sq in chess.SQUARES if board.piece_at(sq) is None]

    def _delete_enemy_piece(self, board: chess.Board, ai_color: chess.Color) -> None:
        squares = self._enemy_squares(board, ai_color)
        if not squares:
            return
        sq = random.choice(squares)
        piece = board.piece_at(sq)
        board.remove_piece_at(sq)
        self.note_capture(piece)
        self.last_event = f"Reality deleted {chess.square_name(sq)}."

    def _teleport_piece(self, board: chess.Board, ai_color: chess.Color) -> None:
        own = self._ai_squares(board, ai_color)
        empty = self._empty_squares(board)
        if not own or not empty:
            return
        from_sq = random.choice(own)
        to_sq = random.choice(empty)
        piece = board.piece_at(from_sq)
        board.remove_piece_at(from_sq)
        board.set_piece_at(to_sq, piece)
        self.last_event = f"A piece teleported from {chess.square_name(from_sq)} to {chess.square_name(to_sq)}."

    def _spawn_piece(self, board: chess.Board, ai_color: chess.Color, force_queen: bool = False) -> None:
        empty = self._empty_squares(board)
        if not empty:
            return
        sq = random.choice(empty)
        piece_type = chess.QUEEN if force_queen else random.choice([chess.PAWN, chess.KNIGHT, chess.BISHOP, chess.ROOK, chess.QUEEN])
        board.set_piece_at(sq, chess.Piece(piece_type, ai_color))
        self.last_event = f"A forged {'queen' if force_queen else 'piece'} spawned on {chess.square_name(sq)}."

    def _duplicate_piece(self, board: chess.Board, ai_color: chess.Color) -> None:
        own = self._ai_squares(board, ai_color)
        empty = self._empty_squares(board)
        if not own or not empty:
            return
        source = random.choice(own)
        target = random.choice(empty)
        piece = board.piece_at(source)
        if piece is None:
            return
        board.set_piece_at(target, chess.Piece(piece.piece_type, piece.color))
        self.last_event = f"The board cloned {piece.symbol()} to {chess.square_name(target)}."

    def _resurrect_piece(self, board: chess.Board, ai_color: chess.Color) -> None:
        pool = self.captured_white if ai_color == chess.WHITE else self.captured_black
        if not pool:
            return
        empty = self._empty_squares(board)
        if not empty:
            return
        sq = random.choice(empty)
        piece_type = random.choice(pool)
        board.set_piece_at(sq, chess.Piece(piece_type, ai_color))
        self.last_event = f"A captured piece returned at {chess.square_name(sq)}."

    def _grant_extra_turn(self, *_args) -> None:
        self.extra_turns += 1
        if self.boss_phase >= 2:
            self.extra_turns += 1
        if self.boss_phase >= 4:
            self.extra_turns += 1
        self.last_event = "The boss stole an extra turn."

    def _reality_rewrite(self, board: chess.Board, ai_color: chess.Color) -> None:
        pieces = list(board.piece_map().items())
        if len(pieces) < 2:
            return
        (sq1, p1), (sq2, p2) = random.sample(pieces, 2)
        board.set_piece_at(sq1, p2)
        board.set_piece_at(sq2, p1)
        self.last_event = f"Reality rewrote itself between {chess.square_name(sq1)} and {chess.square_name(sq2)}."

    def _boss_phase(self, board: chess.Board, ai_color: chess.Color) -> None:
        self._spawn_piece(board, ai_color, force_queen=self.boss_phase >= 3)
        self._grant_extra_turn()
        if self.boss_phase >= 2:
            self._delete_enemy_piece(board, ai_color)
        if self.boss_phase >= 3:
            self._reality_rewrite(board, ai_color)
        self.last_event = f"Boss phase {self.boss_phase} crackles with power."

    def _final_boss(self, board: chess.Board, ai_color: chess.Color) -> None:
        self.extra_turns += 2
        self._spawn_piece(board, ai_color, force_queen=True)
        self._duplicate_piece(board, ai_color)
        self._delete_enemy_piece(board, ai_color)
        self._reality_rewrite(board, ai_color)
        self.last_event = f"Final phase engaged: {self.boss_name} breaks the board apart."
