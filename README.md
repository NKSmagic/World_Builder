# World Builder

Quick CLI to manage world-building notes.

## Dev

- Activate venv:
  - `source .venv/bin/activate`
- Run:
  - `python -m world_builder.cli`
  - or after editable install: `world-builder`
- Format/lint:
  - `black . && ruff .`
- Test:
  - `pytest -q`

## Data layout

- Default data directory: `~/.local/share/world_builder`
- Each node is a `.txt` file named from the slug of its name, e.g. `avelon.txt`
- File format:
  - Line 1: Type (e.g., `Kingdom`)
  - Line 2: Parent name or `-` (no parent)
  - Lines 3+: Free-form notes

Example: 
- Kingdom
- Edoras
- Prosperous realm with ancient oaths.


## Commands

- Initialize data directory:
  - `world-builder init`
  - Custom dir: `world-builder init --dir ./data`

- Add a node:
  - `world-builder add "Avelon" -t Kingdom -p edoras -n "Prosperous realm."`
  - Overwrite existing: `--force`
  - Custom dir: `--dir ./data`

- List nodes:
  - `world-builder list`
  - Filter by type: `world-builder list -t Kingdom`
  - Custom dir: `--dir ./data`

- Show a node:
  - `world-builder show Avelon`
  - Custom dir: `--dir ./data`

- Edit a node in your $EDITOR:
  - `world-builder edit Avelon`
  - Set editor (examples): `export EDITOR=vim` or `export EDITOR="code -w"`

- Print tree of nodes:
  - `world-builder tree`
  - From a specific root name: `world-builder tree --root edoras`
  - Custom dir: `--dir ./data`

## Tips

- Names map to filenames via slug (lowercase, underscores). Use the same when referencing parents and roots.
- Keep parents as bare names (e.g., `edoras`), not paths.
- Common workflow:
  - `world-builder init`
  - `world-builder add "Edoras" -t Continent -p - -n "Eastern seas..."`
  - `world-builder add "Avelon" -t Kingdom -p edoras -n "Prosperous..."`

## Development

- Format/lint: `black . && ruff .`
- Tests: `pytest -q`
