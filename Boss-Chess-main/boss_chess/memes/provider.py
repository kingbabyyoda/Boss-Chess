from __future__ import annotations

import random

try:
    import requests
except Exception:  # pragma: no cover
    requests = None

FALLBACK_MEMES = [
    "Holy hell!",
    "Google en passant.",
    "Actual zombie.",
    "Call the exorcist.",
    "New response just dropped.",
    "Brick the pipi.",
]

PERSONALITIES = [
    "Anarchy Goblin",
    "Grandmaster Menace",
    "Bongcloud Prophet",
    "Pipi Bricker",
]


class MemeProvider:
    def __init__(self) -> None:
        self.cache: list[str] = []

    def get_meme(self) -> str:
        if self.cache:
            return random.choice(self.cache)

        fetched = self._fetch_reddit_titles()
        if fetched:
            self.cache = fetched
            return random.choice(self.cache)

        return random.choice(FALLBACK_MEMES)

    def personality(self) -> str:
        return random.choice(PERSONALITIES)

    def _fetch_reddit_titles(self) -> list[str]:
        if requests is None:
            return []

        headers = {"User-Agent": "BossChess/0.1"}
        urls = [
            "https://www.reddit.com/r/AnarchyChess/hot.json?limit=20",
            "https://www.reddit.com/r/AnarchyChess/top.json?t=day&limit=20",
        ]
        out: list[str] = []

        for url in urls:
            try:
                response = requests.get(url, headers=headers, timeout=4)
                if response.status_code != 200:
                    continue
                payload = response.json()
                for child in payload.get("data", {}).get("children", []):
                    title = child.get("data", {}).get("title")
                    if title and title not in out:
                        out.append(title)
            except Exception:
                continue

        return out[:25]
