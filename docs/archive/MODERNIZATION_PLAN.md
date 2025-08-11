# TwitchBot Modernization Plan for Ubuntu 24.04 + Python 3.12

## Overview
This project requires careful modernization due to critical VirtualBox integration and major breaking changes in TwitchIO (v1.1.0 → v3.1.0). The plan prioritizes incremental updates with testing at each stage.

## Phase 1: Infrastructure & VirtualBox Foundation (Weeks 1-2)

### 1.1 Development Environment Setup
- **Tool Choice**: Use **uv** for dependency management (10-100x faster, Rust-based, Docker-friendly)
- Set up Ubuntu 24.04 development environment
- Install Python 3.12 via uv
- Create `pyproject.toml` to replace `requirements.txt`

### 1.2 VirtualBox Integration (CRITICAL PATH)
- **Challenge**: Official vboxapi has Python 3.12 compatibility issues
- **Solution Options**:
  1. **Primary**: Try `pyvbox` package (more compatible than official vboxapi)
  2. **Fallback**: Implement VBoxManage CLI wrapper with subprocess calls
- Test VirtualBox integration thoroughly before proceeding
- Create abstraction layer to switch between implementations if needed

### 1.3 Docker Foundation
- Create multi-stage Dockerfile with uv
- Base image: `ubuntu:24.04` with VirtualBox dependencies
- Separate Python deps installation for layer caching
- Mount VirtualBox socket/API for host communication

## Phase 2: Core Dependencies Update (Weeks 3-4)

### 2.1 Safe Dependencies First
Update non-breaking dependencies:
- `aiohttp`: 3.6.2 → 3.9+ (mostly backward compatible)
- `attrs`, `idna`, `multidict`, `yarl`: Latest versions
- Remove deprecated `pkg-resources==0.0.0`

### 2.2 Python Code Compatibility
- Run with Python 3.12 and fix any syntax/import issues
- Update async/await patterns if needed
- Fix any deprecated warnings

## Phase 3: TwitchIO Migration (Weeks 5-8) - MAJOR BREAKING CHANGES

### 3.1 TwitchIO v3.1.0 Migration (COMPLEX)
**Breaking Changes Requiring Code Rewrite**:
- **IRC Removal**: Chat now via EventSub (not IRC)
- **PubSub Deprecated**: Use EventSub for all real-time events
- **Authentication**: App tokens auto-generated, OAuth flow changed
- **API Changes**: Complete constructor and event system redesign

### 3.2 Migration Strategy
1. **Keep v1.1.0 working** in parallel during migration
2. **Create new TwitchBot implementation** alongside existing
3. **Map old commands to new EventSub system**:
   - Chat commands: `!help`, `!flag`, `!hint`, etc.
   - Channel point redemptions
   - Subscriptions and bits
4. **Test authentication flow** with new Twitch app tokens
5. **Gradual cutover** once feature parity achieved

## Phase 4: Integration & Testing (Weeks 9-10)

### 4.1 End-to-end Testing
- VM control through Twitch chat
- Flag capture system
- Hint system
- Leaderboard functionality
- Channel point redemptions

### 4.2 Performance Optimization
- Leverage uv's speed improvements
- Optimize Docker build times
- Test VirtualBox integration under load

## Phase 5: Deployment Strategy (Week 11)

### 5.1 Docker Deployment
- **Base**: `ubuntu:24.04` with VirtualBox runtime
- **Dependencies**: uv for fast package installation
- **Volumes**: VirtualBox VMs and configuration data
- **Network**: Host network access for VirtualBox API

### 5.2 Production Considerations
- VirtualBox host requirements (nested virtualization)
- Security: VM isolation, Twitch token management  
- Monitoring: VM state, chat connectivity, error logging
- Backup: Challenge state, user data, VM snapshots

## Risk Mitigation

### High-Risk Items
1. **VirtualBox SDK compatibility** - Test early, have CLI fallback ready
2. **TwitchIO v3 migration** - Major rewrite required, keep v1 working during transition
3. **Twitch API changes** - Authentication flow completely different

### Rollback Strategy
- Keep current working version in separate branch
- Docker enables easy rollback to previous versions
- Feature flags for gradual TwitchIO v3 migration

## Alternative Deployment Options

### Docker (Recommended)
- **Pros**: Isolation, reproducibility, VirtualBox dependencies contained
- **Cons**: Nested virtualization complexity

### uv + systemd (Alternative)
- **Pros**: Direct host VirtualBox access, simpler networking
- **Cons**: System dependency management, harder to reproduce

### Nix (Advanced)
- **Pros**: Perfect reproducibility, declarative config
- **Cons**: Steep learning curve, VirtualBox integration complexity

## Success Metrics
- [ ] VirtualBox VM control via Python 3.12
- [ ] TwitchIO v3 chat commands functional
- [ ] EventSub replaces PubSub successfully
- [ ] Docker deployment working with host VirtualBox
- [ ] All original features preserved (flags, hints, leaderboard)
- [ ] Performance improved with uv dependency management

**Estimated Timeline**: 11 weeks with 2-3 week buffer for TwitchIO migration complexity.

## Current Dependencies Analysis

### From requirements.txt (2020 versions):
```
aiohttp==3.6.2          # → 3.9+ (backward compatible)
async-timeout==3.0.1    # → Latest (or remove if aiohttp 3.9+)
attrs==19.3.0          # → Latest
chardet==3.0.4         # → Latest  
idna==2.10             # → Latest
jedi==0.17.1           # → Latest (dev dependency)
multidict==4.7.6       # → Latest
parso==0.7.0           # → Latest (jedi dependency)
pkg-resources==0.0.0   # → REMOVE (deprecated)
twitchio==1.1.0        # → 3.1.0 (MAJOR BREAKING CHANGES)
vboxapi==1.0           # → pyvbox or VBoxManage CLI wrapper
virtualbox==2.0.0      # → pyvbox or remove
websockets==8.1        # → Latest
yarl==1.4.2            # → Latest
```

### Key Migration Challenges:
1. **TwitchIO 1.1.0 → 3.1.0**: Complete rewrite required
2. **VirtualBox SDK**: Python 3.12 compatibility issues
3. **Authentication**: Twitch OAuth flow changed significantly

## File Structure After Modernization:
```
twitchbot/
├── pyproject.toml              # Replaces requirements.txt
├── Dockerfile                  # Multi-stage Docker build
├── docker-compose.yml          # Development environment
├── MODERNIZATION_PLAN.md       # This file
├── CLAUDE.md                   # Updated for new architecture
├── core/
│   ├── adapters/               # New VirtualBox abstraction
│   │   ├── vbox_interface.py   # Abstract interface
│   │   ├── pyvbox_adapter.py   # pyvbox implementation
│   │   └── cli_adapter.py      # VBoxManage CLI fallback
│   └── twitch/                 # New TwitchIO v3 implementation
│       ├── bot_v3.py           # New EventSub-based bot
│       └── migration.py        # Migration utilities
└── legacy/                     # Keep old version during transition
    └── bots/
        └── twitch.py           # Original v1.1.0 implementation
```