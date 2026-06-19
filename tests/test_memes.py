from __future__ import annotations

from pathlib import Path

from boss_chess.memes.provider import MemeProvider
from boss_chess.memes.reddit import RedditTitleFetcher


class DummyFetcher(RedditTitleFetcher):
    def __init__(self, titles: list[str]):
        super().__init__(subreddit="AnarchyChess")
        self._titles = titles

    def fetch_titles(self, limit: int = 25) -> list[str]:
        return self._titles[:limit]


def test_meme_provider_persists_cache(tmp_path: Path) -> None:
    cache_path = tmp_path / "meme_cache.json"
    provider = MemeProvider(cache_path=cache_path, fetcher=DummyFetcher(["holy hell", "actual zombie"]), autoload=False)

    titles = provider.refresh()

    assert titles == ["holy hell", "actual zombie"]
    assert cache_path.exists()
    assert provider.status_line().startswith("Meme feed:")

    reloaded = MemeProvider(cache_path=cache_path, fetcher=DummyFetcher([]), autoload=True)
    assert reloaded.cached_titles() == ["holy hell", "actual zombie"]
    assert reloaded.get_meme() in {"holy hell", "actual zombie"}


def test_meme_provider_context_line_includes_personality_and_title(tmp_path: Path) -> None:
    provider = MemeProvider(cache_path=tmp_path / "cache.json", fetcher=DummyFetcher(["new response just dropped"]), autoload=False)
    provider.refresh()
    context = provider.get_context_line()

    assert "[" in context
    assert "|" in context
    assert "new response just dropped" in context
