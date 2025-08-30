# Migration Guide: Ubuntu 24.04, Python 3.12, Modern Deps

This guide describes a safe, incremental upgrade to Ubuntu 24.04 LTS, Python 3.12, and current library versions while keeping VirtualBox support. It reduces technical debt by moving to modern packaging, trimming dependencies, and introducing a pluggable hypervisor layer for future KVM/libvirt support.

## Goals
- Modern baseline: Ubuntu 24.04 + Python 3.12.
- Reproducible installs via uv + pyproject.toml.
- Keep VirtualBox 7.x; prepare for libvirt/KVM backend.
- Remove pinned transitive dependencies and outdated pins.

## Phase 0 — Prep and Cleanup
- Create branch: `git switch -c modernize/py312`.
- Move to `pyproject.toml`; keep only direct deps: `twitchio`, `virtualbox` (pyvbox).
- Install uv: `curl -LsSf https://astral.sh/uv/install.sh | sh`.
- Create env and add deps:
  - `uv venv && source .venv/bin/activate`
  - `uv add twitchio virtualbox`
- Export for legacy tooling: `uv export --frozen --format requirements-txt > requirements.txt`.

## Phase 1 — Ubuntu 24.04 + VirtualBox SDK
- `sudo apt install virtualbox virtualbox-dkms`.
- Install Oracle SDK:
  - `export VBOX_INSTALL_PATH=/usr/lib/virtualbox`
  - `python sdk/installer/vboxapisetup.py install`
- Sanity check: `python -c "import virtualbox; print(virtualbox.VirtualBox().version)"`.
 - Ensure permissions: add your user to `vboxusers` and re-login: `sudo usermod -aG vboxusers $USER`.

## Phase 2 — VirtualBox Integration Hardening
- Replace magic state check in `core/vm/virtualbox.py`:
  - `int(self.machine.state) == 5` → `self.machine.state == virtualbox.library.MachineState.running`.
- Add startup self-check (import pyvbox, create `VirtualBox()`), and log clear errors if SDK missing.
- Add a local smoke script to list VMs (no start) to validate SDK.
 - Parameterize launch mode: allow `gui` or `headless` via `core/settings.py` (servers often need headless). Validate keyboard injection works headless.
 - Document guest keyboard layout expectation (US layout recommended) and limitations of `put_keys()`.

## Phase 3 — TwitchIO Upgrade
- Upgrade to latest `twitchio` (2.x/3.x):
  - Use new Bot init (single `token`/`prefix`) and `twitchio.ext.pubsub` for PubSub.
  - Remove private usages (e.g., `_ws`); use official send APIs and PubSub callbacks.
- Create a thin adapter in `bots/twitch.py` (init/connect/send/pubsub handlers) to isolate the library surface.
 - OAuth scopes: consolidate to a single token with needed scopes (e.g., `chat:read`, `chat:edit`, `channel:read:redemptions`). Update profile storage and Interactive prompts.
 - Event loop model: replace thread + `run()` with async start/stop (`await bot.start()` / `await bot.close()`), or guard shared `state` with locks if keeping threads.

## Phase 4 — Dev UX and CI
- Makefile targets: `venv`, `install` (uv sync), `run`, `lint`, `format`.
- Lint/format: `ruff` and `black`; optional `mypy` for gradual typing.
- GitHub Actions (ubuntu-24.04, Python 3.12): `uv sync`, run lint/tests. Skip VM integration in CI; provide a local smoke test for VirtualBox.
- Gate VM-dependent tests behind `VM_TESTS=1`. Default CI only imports pyvbox and lists machines.

## Phase 5 — CLI Modernization
- Rationale: current `cmd` REPL is interactive-only, hard to script/test, and doesn’t expose new health/OAuth/headless flows well.
- Keep REPL for manual sessions (backward compatibility), but add a non-interactive admin CLI using Typer.
- Add a new `cli.py` which wraps `State` operations without `input()`; expose two entry points via `pyproject.toml`:
  - `twitchbot`: run the bot (service mode; flags like `--mode {gui,headless}`).
  - `twitchbot-admin`: admin commands for profiles/challenges/twitch/vm/health.
- Suggested subcommands:
  - `profile create|list|select`, `challenge create|list|select`.
  - `twitch init|connect|disconnect|status` (single OAuth token + scopes).
  - `vm start|stop|halt|snapshot --mode {gui,headless}`.
  - `health virtualbox|twitch` (SDK check, OAuth scope check).
  - optional: `migrate data --from-pickle --to-json`.
- Output: human-readable default; `--json` flag for scripting. Shell completion via `twitchbot-admin --install-completion`.
- Dependencies: `uv add typer rich` (Rich optional for nicer output).
- Testing: add CLI tests with `pytest` using Typer’s `CliRunner`.

## Hypervisor Abstraction (Future-Proofing)
- Add `core/vm/base.py` interface consumed by state/commands.
- Keep `VirtualBoxSrv` in `core/vm/virtualbox.py` as default.
- Plan experimental `core/vm/libvirt.py` backend using libvirt/KVM (better performance on Linux). Keyboard injection via QMP `send-key` or VNC; implement once feature parity (launch, snapshot, restore, keystrokes) is defined.

## Data and Logging Modernization (Optional but Recommended)
- Persistence: current profiles/challenges use pickle under `$HOME/.config/twitchbot/`. Consider migrating to a versioned JSON schema with a simple converter; at minimum, back up the directory before upgrading.
- Logging: default `twitchbot.log` in CWD can rotate poorly. Prefer XDG paths or systemd/journald for managed deployments; add rotation if file logging is kept.

## Deployment (Host Runtime)
- `uv venv && uv sync`.
- Configure tokens locally (do not commit secrets).
- Run: `python twitchbot.py`.

## Verification Checklist
- Bot connects and responds to `!help`.
- VirtualBox smoke runs; sample VM snapshot/restore validated.
- CI passes lint/tests; no private TwitchIO APIs remain.
- OAuth token has required scopes; PubSub redemptions received.
- Headless launch mode tested (if used); user is in `vboxusers`.
- Admin CLI works: `twitchbot-admin health virtualbox` passes; `vm start --mode headless` launches a sample VM.
