# Unified TwitchBot Modernization Plan

## Core Philosophy: Rewrite, Don't Patch

This plan adopts the "Clean Slate" philosophy. We will execute a complete rewrite of the application to eliminate all existing technical debt and establish a modern, maintainable, and performant architecture. The target architecture, components, and code will be those defined in the **TwitchBot Modernization Plan V4**. The initial setup and environment configuration will be guided by the practical steps outlined in the **Migration Guide**.

---

## Phase 0: Foundation & Environment Setup

This phase focuses on preparing a modern, reproducible development environment.

### 1. Git & Tooling Setup
- **Create Branch**: Isolate all work on a new branch.
  ```bash
  git switch -c modernize/clean-slate
````

  - **Install `uv`**: Use `uv` for all Python package and virtual environment management.
    ```bash
    curl -LsSf [https://astral.sh/uv/install.sh](https://astral.sh/uv/install.sh) | sh
    source $HOME/.cargo/env 
    ```
  - **Create Virtual Environment**:
    ```bash
    uv venv
    source .venv/bin/activate
    ```

### 2\. OS & Hypervisor Setup (Ubuntu 24.04)

  - **Install VirtualBox**:
    ```bash
    sudo apt update && sudo apt install virtualbox virtualbox-dkms -y
    ```
  - **Configure User Permissions**: Add your user to the `vboxusers` group to grant access to the hypervisor. **A re-login is required after this step.**
    ```bash
    sudo usermod -aG vboxusers $USER
    echo "✅ Action Required: Please log out and log back in for group changes to take effect."
    ```
  - **Install VirtualBox SDK**:
    ```bash
    # Note: The path to the SDK may vary. This assumes a standard installation.
    export VBOX_INSTALL_PATH=/usr/lib/virtualbox
    python ${VBOX_INSTALL_PATH}/sdk/installer/vboxapisetup.py install
    ```
  - **Sanity Check**: Verify that the Python SDK can connect to VirtualBox.
    ```bash
    python -c "import virtualbox; print(f'VirtualBox SDK Version: {virtualbox.VirtualBox().version}')"
    ```

### 3\. Project Scaffolding

  - **Create Directory Structure**: Build the clean architecture directory structure as defined in Plan V4.
    ```bash
    mkdir -p src/twitchbot/{api/routes,application/{commands,queries,services},core,domain,infrastructure/{storage,twitch,vm},legacy} tests/{unit,integration,e2e} docs
    touch src/twitchbot/{__init__.py,main.py,cli.py}
    # ... create all other __init__.py files and placeholder .py files ...
    ```
  - **Create `pyproject.toml`**: Create the `pyproject.toml` file exactly as specified in **Plan V4**.
  - **Install Dependencies**: Use `uv` to install all dependencies from your new `pyproject.toml`.
    ```bash
    uv sync
    ```
  - **Setup CI/CD**: Implement the linting (`ruff`, `black`), formatting, and testing workflow from the **Migration Guide** using GitHub Actions.

-----

## Phase 1: Modern VM Abstraction Layer

**Goal**: Implement the dual-hypervisor support with a clean, async-first interface.

1.  **Define `VMController` Interface**: Create `src/twitchbot/infrastructure/vm/base.py` with the `VMController` abstract base class from Plan V4. This defines the contract for all hypervisor interactions.
2.  **Implement `VirtualBoxController`**: Create `src/twitchbot/infrastructure/vm/virtualbox.py`. Write the new implementation from scratch, following the async, retry, and error-handling patterns in Plan V4. Do not reuse legacy code.
3.  **Implement `KVMController`**: Create the KVM implementation in `src/twitchbot/infrastructure/vm/kvm.py`.
4.  **Create `VMControllerFactory`**: Implement the factory to select the correct controller based on configuration.

-----

## Phase 2: Modern Twitch & Configuration

**Goal**: Replace the entire Twitch integration with a modern EventSub-based client and robust configuration.

1.  **Implement Pydantic Settings**: Create `src/twitchbot/core/config.py` with the `AppConfig`, `TwitchConfig`, etc., from Plan V4. Use a `.env` file for local development.
2.  **Implement `ModernTwitchClient`**: Create `src/twitchbot/infrastructure/twitch/client.py`. This client will use `httpx` and the `twitchio.ext.eventsub` WebSocket client. It should not use any legacy IRC functionality.
3.  **Define Domain Events**: Create `src/twitchbot/domain/events.py` to define structured events like `ChatMessageEvent` and `ChannelPointRedemptionEvent`.

-----

## Phase 3: Modern Storage Layer

**Goal**: Replace all file-based storage with a professional, async-first database layer.

1.  **Define SQLAlchemy 2.0 Models**: Create `src/twitchbot/infrastructure/storage/models.py` with all the necessary tables (`User`, `Challenge`, `Flag`, etc.) using the modern `Mapped` and `AsyncAttrs` syntax.
2.  **Implement Repository Pattern**: Create `src/twitchbot/infrastructure/storage/repositories.py`. Implement classes like `UserRepository` and `ChallengeRepository` that encapsulate all database query logic.
3.  **Setup Database Connection**: Create `src/twitchbot/infrastructure/storage/database.py` to manage the async engine and session creation.

-----

## Phase 4: Application Services & Business Logic

**Goal**: Rebuild the core application logic on top of the new, clean infrastructure layers.

1.  **Implement Domain Services**: Create `src/twitchbot/application/services/game_service.py`. This service will orchestrate actions like capturing flags and getting hints by using the repositories and VM controller, but will contain no infrastructure-specific code itself.
2.  **Implement Command Handlers**: Create `src/twitchbot/application/commands/chat_commands.py`. The `ChatCommandHandler` will parse messages and delegate actions to the `GameService`.

-----

## Phase 5: API, CLI, & Deployment

**Goal**: Expose application functionality through a modern web API and a powerful CLI, and prepare for production deployment.

1.  **Build FastAPI App**: Create `src/twitchbot/main.py` and the associated API routers in `src/twitchbot/api/routes/`. Use FastAPI's dependency injection to provide services to the API endpoints.
2.  **Build Typer CLI**: Create `src/twitchbot/cli.py` to provide a scriptable, non-interactive command-line interface for administration and testing.
3.  **Containerize**: Implement the `Dockerfile` and `docker-compose.yml` from Plan V4 to create a production-ready, containerized deployment with monitoring.

-----

## Phase 6: Data Migration & Final Verification

**Goal**: Bring in old data and verify the entire system end-to-end.

1.  **Implement `LegacyMigrator`**: Create the `src/twitchbot/legacy/bridge.py` module. Write the logic to read from old pickle/JSON files and use the new repositories to write the data into the database.
2.  **Run Migration**: Execute the migration script via the Typer CLI.
3.  **Full System Verification**:
      - Use the **Verification Checklist** from the **Migration Guide** as a basis.
      - Test all `!commands` in a test Twitch channel.
      - Verify VM operations (`start`, `stop`, `type`) work via moderator commands.
      - Check the FastAPI health endpoint.
      - Use the Typer CLI to check system status (`twitchbot-admin status`).
