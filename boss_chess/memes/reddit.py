from __future__ import annotations

from dataclasses import dataclass

try:
    import requests
except Exception:  # pragma: no cover
    requests = None


@dataclass(slots=True)
class RedditTitleFetcher:
    subreddit: str = "AnarchyChess"
    user_agent: str = "BossChess/1.0"
    timeout: int = 4

    def fetch_titles(self, limit: int = 25) -> list[str]:
        if requests is None:
            return []

        urls = [
            f"https://www.reddit.com/r/{self.subreddit}/hot.json?limit=20",
            f"https://www.reddit.com/r/{self.subreddit}/new.json?limit=20",
            f"https://www.reddit.com/r/{self.subreddit}/top.json?t=day&limit=20",
        ]
        out: list[str] = []
        headers = {"User-Agent": self.user_agent}

        for url in urls:
            try:
                response = requests.get(url, headers=headers, timeout=self.timeout)
                if response.status_code != 200:
                    continue
                payload = response.json()
                for child in payload.get("data", {}).get("children", []):
                    title = child.get("data", {}).get("title")
                    if title:
                        cleaned = str(title).strip()
                        if cleaned and cleaned not in out:
                            out.append(cleaned)
            except Exception:
                continue

        return out[:limit]
