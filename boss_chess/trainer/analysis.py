from __future__ import annotations

from dataclasses import dataclass, field

import chess

from boss_chess.engine.engine import ChessEngine
from boss_chess.trainer.motifs import MotifResult, TacticalMotifDetector
from boss_chess.trainer.openings import OpeningRecognizer
from boss_chess.trainer.puzzles import PuzzleGenerator
from boss_chess.trainer.report import GameReport, MoveReview, PracticePrompt


@dataclass(slots=True)
class Trainer:
    engine: ChessEngine
    opening_recognizer: OpeningRecognizer = field(default_factory=OpeningRecognizer)
    motif_detector: TacticalMotifDetector = field(default_factory=TacticalMotifDetector)
    puzzle_generator: PuzzleGenerator = field(default_factory=PuzzleGenerator)
    reviews: list[MoveReview] = field(default_factory=list)

    def review_move(self, board_before: chess.Board, played_move: chess.Move) -> str:
        review = self.analyse_move(board_before, played_move)
        self.reviews.append(review)
        if review.best_move == played_move:
            return (
                f"Trainer: great move in {review.opening_name}. "
                f"Motif: {review.motif.name}. {self.engine.analyse(board_before).summary}"
            )

        details = [
            f"Trainer: opening {review.opening_name}.",
            f"Trainer: best move was {review.best_move.uci() if review.best_move else 'n/a' }.",
            f"Trainer: your move was {review.verdict}.",
            f"Trainer: accuracy {review.accuracy:.0f}% | centipawn loss ~ {review.centipawn_loss}.",
            f"Trainer: motif {review.motif.name} — {review.motif.explanation}",
            f"Trainer: {review.explanation}",
        ]
        return "\n".join(details)

    def analyse_move(self, board_before: chess.Board, played_move: chess.Move) -> MoveReview:
        analysis = self.engine.analyse(board_before, max_lines=self.engine.multi_pv)
        best = analysis.best_move
        played_board = board_before.copy(stack=False)
        if played_move in board_before.legal_moves:
            played_board.push(played_move)
        played_score = self.engine.score_position(played_board)
        best_score = analysis.best_score
        centipawn_loss = self._centipawn_loss(board_before, played_score, best_score)
        accuracy = self.estimate_accuracy(centipawn_loss)
        verdict = self._verdict(centipawn_loss)
        motif = self.motif_detector.detect(board_before, played_move)
        opening_name = self.opening_recognizer.identify(list(board_before.move_stack))
        explanation = self._explain_move(board_before, played_move, best, motif, opening_name)
        return MoveReview(
            move=played_move,
            best_move=best,
            centipawn_loss=centipawn_loss,
            accuracy=accuracy,
            verdict=verdict,
            motif=motif,
            opening_name=opening_name,
            explanation=explanation,
        )

    def analyse_opening(self, board: chess.Board) -> str:
        name = self.opening_recognizer.identify(list(board.move_stack))
        plan = self.opening_recognizer.suggest_plan(board)
        return f"Opening: {name}\nPlan: {plan}"

    def lesson_text(self, board: chess.Board) -> str:
        opening = self.opening_recognizer.identify(list(board.move_stack))
        plan = self.opening_recognizer.suggest_plan(board)
        puzzle = self.puzzle_generator.generate(board)
        return "\n".join(
            [
                f"Opening: {opening}",
                f"Plan: {plan}",
                f"Motif to look for: {puzzle.theme}",
                f"Practice clue: {puzzle.clue}",
                f"Target move: {puzzle.target_move}",
            ]
        )

    def practice_prompt(self, board: chess.Board, side_to_move: chess.Color | None = None) -> PracticePrompt:
        return self.puzzle_generator.generate(board, side_to_move=side_to_move)

    def game_report(self, board: chess.Board | None = None) -> GameReport:
        opening_name = self.opening_recognizer.identify(list(board.move_stack)) if board is not None else self._opening_from_reviews()
        if not self.reviews:
            return GameReport(
                opening_name=opening_name,
                move_count=0,
                average_accuracy=0.0,
                average_centipawn_loss=0.0,
                best_move_count=0,
                inaccuracies=0,
                mistakes=0,
                blunders=0,
                motifs={},
                highlights=["No trainer reviews recorded yet."],
            )

        total_accuracy = sum(review.accuracy for review in self.reviews)
        total_cpl = sum(review.centipawn_loss for review in self.reviews)
        best_count = sum(1 for review in self.reviews if review.best_move == review.move)
        inaccuracies = sum(1 for review in self.reviews if review.verdict == "an inaccuracy")
        mistakes = sum(1 for review in self.reviews if review.verdict == "a mistake")
        blunders = sum(1 for review in self.reviews if review.verdict == "a blunder")
        motif_counts: dict[str, int] = {}
        highlights: list[str] = []
        for review in self.reviews:
            motif_counts[review.motif.name] = motif_counts.get(review.motif.name, 0) + 1
            if review.verdict in {"a mistake", "a blunder"}:
                highlights.append(f"{review.move.uci()}: {review.verdict} — {review.explanation}")
        return GameReport(
            opening_name=opening_name,
            move_count=len(self.reviews),
            average_accuracy=total_accuracy / len(self.reviews),
            average_centipawn_loss=total_cpl / len(self.reviews),
            best_move_count=best_count,
            inaccuracies=inaccuracies,
            mistakes=mistakes,
            blunders=blunders,
            motifs=motif_counts,
            highlights=highlights,
        )

    def report_text(self, board: chess.Board | None = None) -> str:
        return "\n".join(self.game_report(board).summary_lines())

    def estimate_accuracy(self, centipawn_loss: int) -> float:
        if centipawn_loss <= 10:
            return 99.0
        if centipawn_loss <= 25:
            return 96.0
        if centipawn_loss <= 50:
            return 90.0
        if centipawn_loss <= 100:
            return 80.0
        if centipawn_loss <= 200:
            return 65.0
        return max(5.0, 65.0 - (centipawn_loss - 200) * 0.05)

    def _centipawn_loss(self, board: chess.Board, played_score: int, best_score: int) -> int:
        if board.turn == chess.WHITE:
            return max(0, best_score - played_score)
        return max(0, played_score - best_score)

    def _verdict(self, cpl: int) -> str:
        if cpl < 25:
            return "solid"
        if cpl < 75:
            return "an inaccuracy"
        if cpl < 150:
            return "a mistake"
        return "a blunder"

    def _explain_move(self, board: chess.Board, played: chess.Move, best: chess.Move | None, motif: MotifResult, opening_name: str) -> str:
        if best is None:
            return f"The engine could not find a stable best move in {opening_name}."
        if played == best:
            return f"{played.uci()} matches the engine line and fits the {opening_name} plan."
        return (
            f"Best move {best.uci()} keeps the evaluation better. "
            f"Your move {played.uci()} is tagged as {motif.name.lower()} and {self._move_nature(board, played)}."
        )

    def _move_nature(self, board: chess.Board, move: chess.Move) -> str:
        parts: list[str] = []
        piece = board.piece_at(move.from_square)
        if piece:
            if piece.piece_type in (chess.KNIGHT, chess.BISHOP):
                parts.append("develops a minor piece")
            elif piece.piece_type == chess.PAWN:
                parts.append("claims space with a pawn")
            elif piece.piece_type == chess.ROOK:
                parts.append("activates a rook")
            elif piece.piece_type == chess.QUEEN:
                parts.append("moves the queen")
        if board.is_capture(move):
            parts.append("wins material")
        if board.gives_check(move):
            parts.append("gives check")
        if move.promotion:
            parts.append("promotes a pawn")
        return ", ".join(parts) or "keeps the position flexible"

    def _opening_from_reviews(self) -> str:
        if not self.reviews:
            return "Unclassified opening"
        return self.reviews[0].opening_name
