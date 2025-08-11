# Repository Guidelines

## Project Structure & Module Organization
- `core/`: Domain logic and runtime.
  - `objects/`: Data models (challenge, profile, token, etc.).
  - `state/`: Persistence and state orchestration (`FileStore`, stores, API).
  - `vm/`: Hypervisor integration (VirtualBox service).
  - `interactive.py`: Interactive CLI loop.
  - `settings.py`: Defaults (logging, delays, objective).
- `bots/`: Platform adapters (e.g., `twitch.py`).
- `twitchbot.py`: Entry point.
- Default data dir: `$HOME/.config/twitchbot/`.

## Build, Test, and Development Commands
- Create venv: `python3 -m venv .venv && source .venv/bin/activate`.
- Install deps: `pip install -r requirements.txt`.
- Run locally: `python twitchbot.py`.
- VirtualBox SDK (Ubuntu):
  - `export VBOX_INSTALL_PATH=/usr/lib/virtualbox`
  - `python sdk/installer/vboxapisetup.py install`
- Optional (uv): `uv venv && uv sync` (see `MIGRATION.md`).

## Coding Style & Naming Conventions
- Python, 4-space indentation, PEP 8.
- Naming: `snake_case` for functions/vars, `PascalCase` for classes, lowercase module names.
- Logging via `logging`; defaults in `core/settings.py` (update, don’t hardcode paths).
- Keep modules cohesive by domain (e.g., new models under `core/objects/`).

## Testing Guidelines
- Framework: `pytest` (recommended).
- Layout: mirror source tree (e.g., `tests/state/test_filestore.py`).
- Naming: `test_*.py`, functions `test_*`.
- Run: `pytest -q`.
- Focus: state transitions, object serialization, and VM control guards (no real VM start in CI).

## Commit & Pull Request Guidelines
- Commits: imperative mood; optionally prefix ticket (e.g., `BOT-25: Add leaderboard command`).
- Subject ≤ 72 chars; body explains why/how; group related changes.
- PRs include: clear summary, linked issues, validation steps, and any config changes (`settings.py`, SDK notes). Add console logs/screenshots when behavior changes.

## Security & Configuration Tips
- Never commit tokens, secrets, or files from `$HOME/.config/twitchbot/`.
- Linux-focused; ensure VirtualBox and SDK installed before running.
- Store credentials locally (see token object); avoid hardcoding in code.
- For modernization and alternative tooling, see `MIGRATION.md`.
