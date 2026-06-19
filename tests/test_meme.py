from boss_chess.memes.provider import MemeProvider


def test_meme_provider_returns_text():
    provider = MemeProvider()
    meme = provider.get_meme()
    assert isinstance(meme, str)
    assert meme.strip()
