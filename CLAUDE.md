# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Twitch bot for "Twitch Hacks Online" - a CTF (Capture The Flag) platform that integrates with Twitch chat to manage virtual machine challenges. The bot allows streamers to run interactive hacking challenges where viewers can control VMs, capture flags, and compete on leaderboards through Twitch chat commands.

## Modernization Status

**This project is currently undergoing modernization.** See `MODERNIZATION_PLAN_V4.md` for the complete modernization roadmap, which includes:
- Migration to Python 3.12 with full async/await
- Dual hypervisor support (VirtualBox + KVM/QEMU)
- Modern TwitchIO 3.x with EventSub WebSocket
- Clean architecture with FastAPI, SQLAlchemy 2.0, and Pydantic
- Production deployment with Docker and monitoring

Legacy modernization plans (V1-V3) have been archived to `docs/archive/` for reference.

## Key Architecture

### Core Components

- **State Management**: Central `State` class (`core/state/__init__.py`) manages all application state including profiles, challenges, Twitch connections, and VM instances
- **Storage Layer**: Abstract storage interface (`core/state/store.py`) with FileStore implementation (`core/state/filestore.py`) for persistence
- **Twitch Integration**: TwitchBot class (`bots/twitch.py`) extends twitchio.ext.commands.Bot for chat/API integration
- **VM Management**: VirtualBox integration (`core/vm/virtualbox.py`) for controlling challenge VMs
- **Interactive Console**: Command-line interface (`core/interactive.py`) for bot management

### Object Models

Key domain objects in `core/objects/`:
- **Profile**: Twitch channel configuration and user management
- **Challenge**: VM-based CTF challenge with flags, hints, and objectives  
- **Flag**: Capturable challenge objectives with point values
- **Hint**: Progressive clues for challenge levels
- **User**: Twitch user state and interaction permissions
- **Token**: OAuth token management for Twitch API

### Data Flow

1. **Initialization**: Load profile → Load associated challenge → Initialize VM connection → Connect to Twitch
2. **Runtime**: Twitch events → State updates → VM commands → Challenge progression → Leaderboard updates
3. **Persistence**: All changes automatically saved through the store layer

## Development Commands

### Running the Application
```bash
# Install dependencies
pip install -r requirements.txt

# Configure VirtualBox SDK (Ubuntu)
cd sdk/installer
export VBOX_INSTALL_PATH='/usr/lib/virtualbox' 
python vboxapisetup.py install

# Run the bot
python twitchbot.py
```

### Configuration
- Edit `core/settings.py` for default configuration
- Default file storage location: `$HOME/.config/twitchbot/`
- Use interactive console `help` command for bot management

### No Test Framework
The project does not include automated tests or linting configuration. Manual testing is done through the interactive console.

## Development Guidelines

### Code Organization
- Follow existing module structure under `core/`
- New VM providers should extend the abstract interface pattern used by VirtualBox
- Storage implementations should inherit from `AbstractStore`
- All Twitch commands are implemented in the TwitchBot class using twitchio decorators

### State Management
- All persistent state flows through the central State class
- Use the store abstraction for data persistence 
- Challenge state is automatically saved after flag captures and configuration changes
- VM state is managed independently but coordinated through the State class

### Error Handling
- Custom exceptions are defined in `core/exceptions.py`
- Console commands handle exceptions gracefully with user-friendly messages
- VM operations include proper cleanup and state management

### Dependencies
- **twitchio**: Twitch API and chat integration
- **vboxapi/virtualbox**: VirtualBox VM control 
- **aiohttp**: Async HTTP for Twitch API calls

### Security Considerations
- OAuth tokens are managed through the Token object with proper string representation hiding
- User permissions are enforced through the profile's allow/deny lists and mod status
- VM access is controlled through the hotseat system and user interaction permissions