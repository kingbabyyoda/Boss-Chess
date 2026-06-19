from __future__ import annotations

import random
from pathlib import Path

from boss_chess.memes.cache import MemeCache
from boss_chess.memes.personalities import PERSONALITIES, PERSONALITY_INTROS, VOICE_TAGS
from boss_chess.memes.reddit import RedditTitleFetcher

FALLBACK_MEMES = [
    "Holy hell!",
    "Google en passant.",
    "Actual zombie.",
    "Call the exorcist.",
    "New response just dropped.",
    "Brick the pipi.",
    "The knight has opinions.",
    "Material is temporary.",
    "The board is lying.",
    "The eval bar trembles.",
    "Premove into the void.",
    "The king is on a spiritual journey.",
]


class MemeProvider:
    def __init__(self, cache_path: Path | None = None, subreddit: str = "AnarchyChess") -> None:
        self.reddit = RedditTitleFetcher(subreddit=subreddit)
        self.cache = MemeCache(path=cache_path or Path("saves") / "meme_cache.json")
        self.cache.load()
        if not self.cache.titles:
            self.refresh()

    def get_meme(self) -> str:
        if self.cache.titles:
            return random.choice(self.cache.titles)
        fetched = self.refresh()
        if fetched:
            return random.choice(fetched)
        return random.choice(FALLBACK_MEMES)

    def personality(self) -> str:
        return random.choice(PERSONALITIES)

    def personality_intro(self, personality: str | None = None) -> str:
        tag = personality or self.personality()
        options = PERSONALITY_INTROS.get(tag, FALLBACK_MEMES)
        return random.choice(options)

    def voice_tags(self) -> list[str]:
        return list(VOICE_TAGS)

    def cached_titles(self) -> list[str]:
        return list(self.cache.titles)

    def refresh(self) -> list[str]:
        fetched = self.reddit.fetch_titles(limit=40)
        if fetched:
            self.cache.update(fetched, source=f"r/{self.reddit.subreddit}")
            return fetched
        if not self.cache.titles:
            self.cache.update(FALLBACK_MEMES, source="fallback")
        return list(self.cache.titles)

    def source_label(self) -> str:
        if self.cache.source.startswith("r/"):
            return f"live {self.cache.source} cache"
        return self.cache.source

    def status_line(self) -> str:
        if self.cache.titles:
            return f"Meme feed: {self.source_label()} ({len(self.cache.titles)} titles cached)"
        return "Meme feed: fallback"

    def get_context_line(self) -> str:
        personality = self.personality()
        intro = self.personality_intro(personality)
        title = self.get_meme()
        return f"[{personality}] {intro} | {title}"
