# Boss Chess

A local Python chess project with four stacked modes and a polished graphical interface:

- **Normal mode** — plays a solid game of chess.
- **Trainer mode** — explains mistakes and suggests better moves.
- **Meme mode** — adds AnarchyChess-style jokes and can pull recent post titles from `r/AnarchyChess`.
- **Cheat mode** — turns the AI into a boss fight with health, phases, and increasingly unfair abilities.
- **GUI mode** — a tkinter desktop window with a clickable board, animations, captured pieces, evaluation bar, save/load controls, and live status panels.

This repo is set up as a clean, GitHub-style Python project with a package layout, config, tests, docs, a terminal launcher, and a GUI launcher.

## Features

- Clean multi-file structure
- Package-based code in `boss_chess/`
- Legal move validation with `python-chess`
- Alpha-beta search with quiescence and transposition-table caching
- Optional Stockfish integration
- Built-in opening book for early-game play
- Heuristic evaluation with piece-square tables, king safety, mobility, and passed pawns
- Trainer feedback loop
- Meme provider with Reddit fallback cache
- Boss-style cheat events
- Boss health, phase changes, boss meter, and boss HUD lines
- Save-friendly architecture
- Tkinter GUI with clickable board and move animation
- Board flip and reset view controls
- Captured pieces display
- Evaluation bar
- Sound feedback
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

Terminal mode:

```bash
python main.py --terminal
```

GUI mode:

```bash
python main.py --gui
```

If you leave off the flag, Boss Chess asks which interface you want.

## Strong AI settings

At launch, you can choose:
- search depth
- opening book on/off
- Stockfish on/off
- Stockfish path
- target Elo
- analysis line count

If Stockfish is not available, Boss Chess falls back to the built-in engine automatically.

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
│   ├── gui/
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
Plays a legal chess game using the built-in engine or Stockfish when enabled.

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
- drop through boss phases as its health falls
- trigger a final-boss phase when the health bar gets low
- show boss HUD lines with the boss name, phase name, and HP meter

### GUI
The GUI mode includes:
- click-to-move board interaction
- animated moves
- board flipping
- captured pieces display
- evaluation meter
- save and load controls
- theme switching
- sound feedback
- live trainer/meme/cheat status

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
- `eval`
- `pgn`
- `save <name>`
- `load <name>`
- `saves`
- `new`
- `modes`
- `quit`

## Roadmap

- Add endgame tablebases
- Add puzzle mode
- Add PGN import/export
- Add richer cheat events
- Add persistent save/load files
- Add a polished achievements system

## License

MIT
