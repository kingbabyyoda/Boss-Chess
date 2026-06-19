# Architecture

This project is split into small modules so features can grow without turning into one giant file.

- `boss_chess/engine/` handles chess evaluation and move choice.
- `boss_chess/trainer/` handles move explanations and review.
- `boss_chess/memes/` handles meme text and Reddit fetch attempts.
- `boss_chess/cheat_events/` handles unfair boss-style events.
- `boss_chess/ui/` handles the terminal interface.
