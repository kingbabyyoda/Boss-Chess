# Boss Chess

A local Python chess project with four stacked modes:

- **Normal mode** — plays a solid game of chess.
- **Trainer mode** — explains mistakes and suggests better moves.
- **Meme mode** — adds AnarchyChess-style jokes and can pull recent post titles from `r/AnarchyChess`.
- **Cheat mode** — intentionally unfair local-only chaos that can rewrite the board.

This repo is set up as a clean, GitHub-style Python project with a package layout, config, tests, docs, and a terminal launcher.

## Features

- Clean multi-file structure
- Package-based code in `boss_chess/`
- Legal move validation with `python-chess`
- Alpha-beta search with quiescence and transposition-table caching
- Heuristic evaluation with piece-square tables, king safety, mobility, and passed pawns
- Trainer feedback loop
- Meme provider with Reddit fallback cache
- Boss-style cheat events
- Save-friendly architecture
- Tests and GitHub Actions workflow

## Requirements

- Python 3.11 or newer
- `python-chess`
- `requests` (optional, used for meme fetching)

## Install

```bash
pip install -r requirements.txt
```

## Run

```bash
python main.py
```

## Project layout

```text
Boss-Chess-main/
├── main.py
├── pyproject.toml
├── requirements.txt
├── README.md
├── LICENSE
├── .gitignore
├── .github/workflows/ci.yml
├── boss_chess/
│   ├── __init__.py
│   ├── config.py
│   ├── game.py
│   ├── state.py
│   ├── types.py
│   ├── utils.py
│   ├── engine/
│   ├── modes/
│   ├── trainer/
│   ├── memes/
│   ├── cheat_events/
│   └── ui/
├── docs/
├── saves/
├── logs/
└── tests/
```

## Modes

### Normal
Plays a legal chess game using the built-in engine. Optional Stockfish support can be added later without changing the architecture.

### Trainer
After your move, the trainer prints a short analysis:
- best move
- move quality
- estimated centipawn loss
- a short explanation

### Meme
Meme mode can:
- print joke commentary
- use cached AnarchyChess-style one-liners
- fetch recent `r/AnarchyChess` post titles if network access is available

### Cheat
Cheat mode is meant for a local single-player boss fight. It can:
- delete a piece
- teleport a piece
- spawn a reinforcement
- resurrect a captured piece
- grant an extra turn
- corrupt the board state

## Controls

Use UCI moves such as:

```text
e2e4
g1f3
e7e8q
```

Other commands:
- `help`
- `undo`
- `fen`
- `new`
- `modes`
- `quit`

## Roadmap

- Add GUI with drag-and-drop pieces
- Add Stockfish support
- Add opening book support
- Add puzzle mode
- Add PGN import/export
- Add richer cheat events
- Add persistent save files
- Add a polished achievements system

## License

MIT
