# Repository Guidelines

## Project Structure & Module Organization
- `src/`: Source tree (use src-layout).
  - `thonline/`: Package root.
    - `v1/`: Current implementation.
      - `core/`: Domain logic and runtime.
        - `objects/`: Data models (challenge, profile, token, etc.).
        - `state/`: Persistence and state orchestration (`FileStore`, stores, API).
        - `vm/`: Hypervisor integration (VirtualBox service).
        - `interactive.py`: Interactive CLI loop.
        - `settings.py`: Defaults (logging, delays, objective).
      - `bots/`: Platform adapters (e.g., `twitch.py`).
      - `twitchbot.py`: Entry point module.
    - `v2/`: Next-gen scaffold (`__main__.py`, WIP/experimental).
- Default data dir: `$HOME/.config/twitchbot/`.

### Read-only Policy
- `src/thonline/v1` is frozen and read-only. Do not modify code in this directory. All new work, refactors, and fixes should be implemented in `src/thonline/v2` or via adapters/shims outside `v1`.
- The repository sets filesystem permissions to read-only for `src/thonline/v1`. If you must temporarily adjust for local debugging, restore with `chmod -R u+w src/thonline/v1` and revert to read-only after.

### Git Hooks
- A pre-commit hook blocks commits that modify any path under `src/thonline/v1`.
- Default path: `.git/hooks/pre-commit` (installed by this repo).
- One-time bypass (discouraged): `ALLOW_V1_MODS=1 git commit -m "..."`.

## Build, Test, and Development Commands
- Create venv: `python3 -m venv .venv && source .venv/bin/activate`.
- Install deps: `pip install -r requirements.txt`.
- Run locally (v1): `PYTHONPATH=src python -m thonline.v1.twitchbot`.
- VirtualBox SDK (Ubuntu):
  - `export VBOX_INSTALL_PATH=/usr/lib/virtualbox`
  - `python sdk/installer/vboxapisetup.py install`
- Optional (uv): `uv venv && uv sync` (see `MIGRATION.md`).

## Coding Style & Naming Conventions
- Python, 4-space indentation, PEP 8.
- Naming: `snake_case` for functions/vars, `PascalCase` for classes, lowercase module names.
- Logging via `logging`; defaults in `src/thonline/v1/core/settings.py` (update, don’t hardcode paths).
- Keep modules cohesive by domain (e.g., new models under `src/thonline/v1/core/objects/`).

## Testing Guidelines
- Framework: `pytest` (recommended).
- Layout: mirror the src tree (e.g., `tests/thonline/v1/core/state/test_filestore.py`).
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
