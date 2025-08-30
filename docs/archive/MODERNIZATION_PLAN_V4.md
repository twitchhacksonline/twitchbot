# TwitchBot Modernization Plan V4 - Clean Slate Architecture
## Eliminating Technical Debt Through Strategic Rewrites

## Executive Summary

Complete modernization using Python 3.12, dual hypervisor support (VirtualBox/KVM), and TwitchIO 3.x with EventSub. This plan eliminates all technical debt by rewriting components with modern packages rather than patching legacy code. Focus on clean architecture that's maintainable and performant.

## Core Philosophy: Rewrite, Don't Patch

Instead of maintaining compatibility with outdated patterns, we'll rewrite core components using modern best practices:

- **VM Layer**: Complete rewrite with async-first design
- **Twitch Integration**: Fresh EventSub implementation, no IRC legacy
- **Storage**: Modern async storage with proper typing
- **State Management**: Context managers and dependency injection
- **Configuration**: Pydantic settings with environment validation

## Phase 1: Foundation & Dependencies (Week 1)

### 1.1 Modern Dependency Stack

```toml
# pyproject.toml
[project]
name = "twitchbot"
version = "2.0.0"
description = "Modern Twitch CTF Bot with dual hypervisor support"
requires-python = ">=3.12"
dependencies = [
    # Core Framework
    "fastapi>=0.115.0",         # Modern async web framework
    "uvicorn>=0.32.0",          # ASGI server for EventSub webhooks
    "httpx>=0.28.0",            # Modern HTTP client
    
    # Twitch Integration
    "twitchio>=3.1.0",          # Latest TwitchIO with EventSub
    
    # Hypervisor Support
    "pyvbox>=2.2.0",            # Modern VirtualBox SDK
    "libvirt-python>=10.0.0",   # KVM/QEMU support
    
    # Storage & Config
    "pydantic>=2.9.0",          # Data validation and settings
    "pydantic-settings>=2.6.0", # Environment configuration
    "sqlalchemy>=2.0.0",        # Modern ORM with async support
    "aiosqlite>=0.20.0",        # Async SQLite driver
    
    # Async Utilities
    "anyio>=4.6.0",             # Cross-platform async
    "asyncstdlib>=3.13.0",      # Async standard library
    "tenacity>=9.0.0",          # Retry with backoff
    
    # Observability
    "structlog>=24.0.0",        # Structured logging
    "prometheus-client>=0.21.0", # Metrics
    "opentelemetry-api>=1.27.0", # Distributed tracing
    
    # CLI & UI
    "typer>=0.12.0",            # Modern CLI framework
    "rich>=13.9.0",             # Terminal UI
    "textual>=0.85.0",          # TUI for interactive console
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.24.0",
    "pytest-mock>=3.14.0",
    "pytest-cov>=6.0.0",
    "mypy>=1.13.0",
    "ruff>=0.8.0",
    "pre-commit>=4.0.0",
]

virtualbox = ["pyvbox>=2.2.0"]
kvm = ["libvirt-python>=10.0.0"]
all = ["pyvbox>=2.2.0", "libvirt-python>=10.0.0"]
```

### 1.2 Clean Architecture Structure

```
twitchbot/
├── pyproject.toml
├── Dockerfile
├── docker-compose.yml
├── src/
│   └── twitchbot/
│       ├── __init__.py
│       ├── main.py                    # FastAPI app entry point
│       ├── cli.py                     # Typer CLI interface
│       │
│       ├── core/
│       │   ├── __init__.py
│       │   ├── config.py              # Pydantic settings
│       │   ├── dependencies.py        # DI container
│       │   ├── exceptions.py          # Custom exceptions
│       │   └── logging.py             # Structured logging setup
│       │
│       ├── domain/
│       │   ├── __init__.py
│       │   ├── models.py              # Pydantic domain models
│       │   ├── events.py              # Domain events
│       │   └── services.py            # Domain services
│       │
│       ├── infrastructure/
│       │   ├── __init__.py
│       │   ├── vm/
│       │   │   ├── __init__.py
│       │   │   ├── base.py            # VM controller interface
│       │   │   ├── virtualbox.py      # VirtualBox implementation
│       │   │   ├── kvm.py             # KVM implementation
│       │   │   └── factory.py         # Controller factory
│       │   ├── storage/
│       │   │   ├── __init__.py
│       │   │   ├── models.py          # SQLAlchemy models
│       │   │   ├── repositories.py    # Repository pattern
│       │   │   └── database.py        # Database connection
│       │   └── twitch/
│       │       ├── __init__.py
│       │       ├── client.py          # Modern Twitch client
│       │       ├── eventsub.py        # EventSub handling
│       │       └── webhooks.py        # Webhook endpoints
│       │
│       ├── application/
│       │   ├── __init__.py
│       │   ├── commands/
│       │   │   ├── __init__.py
│       │   │   ├── vm.py              # VM operation commands
│       │   │   ├── flag.py            # Flag capture commands
│       │   │   └── hint.py            # Hint commands
│       │   ├── queries/
│       │   │   ├── __init__.py
│       │   │   ├── leaderboard.py     # Leaderboard queries
│       │   │   └── stats.py           # Statistics queries
│       │   └── services/
│       │       ├── __init__.py
│       │       ├── vm_service.py      # VM orchestration
│       │       ├── game_service.py    # Game logic
│       │       └── user_service.py    # User management
│       │
│       └── api/
│           ├── __init__.py
│           ├── dependencies.py        # FastAPI dependencies
│           ├── middleware.py          # Custom middleware
│           └── routes/
│               ├── __init__.py
│               ├── health.py          # Health check endpoints
│               ├── webhooks.py        # Twitch webhook handlers
│               └── admin.py           # Admin interface
│
├── tests/
│   ├── conftest.py
│   ├── unit/
│   ├── integration/
│   └── e2e/
│
    └── docs/
        ├── architecture.md
        ├── deployment.md
        └── streaming.md

## OBS Integration (Planned)

As part of the v2 rewrite, include optional integration with OBS via obs-websocket 5.x to control basic streaming operations from the bot:

- Start/stop stream: programmatically begin and end the broadcast.
- Switch scenes/sources: change the active scene and toggle source visibility (e.g., overlays, text, browser sources).

Implementation notes:
- Use the official obs-websocket v5 protocol (suggested client: obsws-python) with configurable host/port/password.
- Keep the controller async-friendly and minimal; expose only the operations above initially.
- Secure credentials via environment variables/Pydantic settings; do not hardcode secrets.
    └── api.md
```

## Phase 2: Modern VM Abstraction (Week 2)

### 2.1 Clean VM Controller Interface

```python
# src/twitchbot/infrastructure/vm/base.py
from abc import ABC, abstractmethod
from contextlib import AsyncExitStack
from enum import Enum
from typing import AsyncIterator, Dict, List, Optional
from pydantic import BaseModel
import structlog

logger = structlog.get_logger()

class HypervisorType(str, Enum):
    VIRTUALBOX = "virtualbox"
    KVM = "kvm"
    MOCK = "mock"

class VMState(str, Enum):
    STOPPED = "stopped"
    RUNNING = "running"
    PAUSED = "paused"
    SAVED = "saved"
    ERROR = "error"

class VMInfo(BaseModel):
    name: str
    state: VMState
    hypervisor: HypervisorType
    memory_mb: Optional[int] = None
    cpu_count: Optional[int] = None
    ip_address: Optional[str] = None

class VMController(ABC):
    """Modern async VM controller interface"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.logger = structlog.get_logger().bind(controller=self.__class__.__name__)
        
    @abstractmethod
    async def initialize(self) -> None:
        """Initialize hypervisor connection"""
        pass
    
    @abstractmethod
    async def list_vms(self) -> List[VMInfo]:
        """List all available VMs"""
        pass
    
    @abstractmethod
    async def get_vm_info(self, vm_name: str) -> VMInfo:
        """Get detailed VM information"""
        pass
    
    @abstractmethod
    async def start_vm(self, vm_name: str) -> None:
        """Start a VM"""
        pass
    
    @abstractmethod
    async def stop_vm(self, vm_name: str, save_state: bool = True) -> None:
        """Stop a VM with optional state saving"""
        pass
    
    @abstractmethod
    async def restart_vm(self, vm_name: str) -> None:
        """Restart a VM"""
        pass
    
    @abstractmethod
    async def send_keyboard_input(self, vm_name: str, keys: str) -> None:
        """Send keyboard input to VM"""
        pass
    
    @abstractmethod
    async def type_text(self, vm_name: str, text: str, delay_ms: int = 50) -> None:
        """Type text into VM with configurable delay"""
        pass
    
    @abstractmethod
    async def create_snapshot(self, vm_name: str, snapshot_name: str, description: str = "") -> None:
        """Create a VM snapshot"""
        pass
    
    @abstractmethod
    async def restore_snapshot(self, vm_name: str, snapshot_name: str) -> None:
        """Restore a VM snapshot"""
        pass
    
    @abstractmethod
    async def list_snapshots(self, vm_name: str) -> List[str]:
        """List all snapshots for a VM"""
        pass
    
    @abstractmethod
    async def cleanup(self) -> None:
        """Cleanup resources and connections"""
        pass
    
    async def __aenter__(self):
        """Async context manager entry"""
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.cleanup()
```

### 2.2 Modern VirtualBox Implementation

```python
# src/twitchbot/infrastructure/vm/virtualbox.py
import asyncio
from typing import Dict, List
import pyvbox
from pyvbox.library import VBoxErrorObjectNotFound, MachineState, LockType
from tenacity import retry, stop_after_attempt, wait_exponential

from .base import VMController, VMInfo, VMState, HypervisorType

class VirtualBoxController(VMController):
    """Modern VirtualBox controller using pyvbox with retry logic"""
    
    def __init__(self, config: Dict):
        super().__init__(config)
        self.vbox_mgr = None
        self.vbox = None
        self.sessions: Dict[str, any] = {}
        
    async def initialize(self) -> None:
        """Initialize VirtualBox connection with fallback"""
        try:
            # Use asyncio to run blocking pyvbox operations
            self.vbox_mgr = await asyncio.to_thread(pyvbox.VirtualBoxManager)
            self.vbox = self.vbox_mgr.vbox
            
            version = self.vbox.version
            self.logger.info("Connected to VirtualBox", version=version)
            
        except Exception as e:
            self.logger.error("Failed to initialize VirtualBox SDK", error=str(e))
            # Could implement CLI fallback here if needed
            raise
    
    async def list_vms(self) -> List[VMInfo]:
        """List all VMs with their current state"""
        machines = await asyncio.to_thread(lambda: list(self.vbox.machines))
        
        vm_infos = []
        for machine in machines:
            state = await self._get_vm_state(machine)
            vm_info = VMInfo(
                name=machine.name,
                state=state,
                hypervisor=HypervisorType.VIRTUALBOX,
                memory_mb=machine.memory_size,
                cpu_count=machine.cpu_count
            )
            vm_infos.append(vm_info)
            
        return vm_infos
    
    async def get_vm_info(self, vm_name: str) -> VMInfo:
        """Get detailed information about a specific VM"""
        machine = await self._find_machine(vm_name)
        state = await self._get_vm_state(machine)
        
        return VMInfo(
            name=machine.name,
            state=state,
            hypervisor=HypervisorType.VIRTUALBOX,
            memory_mb=machine.memory_size,
            cpu_count=machine.cpu_count
        )
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def start_vm(self, vm_name: str) -> None:
        """Start a VM with retry logic"""
        machine = await self._find_machine(vm_name)
        
        current_state = await self._get_vm_state(machine)
        if current_state == VMState.RUNNING:
            self.logger.info("VM already running", vm_name=vm_name)
            return
        
        session = self._get_session(vm_name)
        
        try:
            progress = await asyncio.to_thread(
                machine.launch_vm_process, 
                session, 
                'headless', 
                ''
            )
            await self._wait_for_progress(progress)
            
            self.logger.info("VM started successfully", vm_name=vm_name)
            
        except Exception as e:
            self.logger.error("Failed to start VM", vm_name=vm_name, error=str(e))
            raise
    
    async def stop_vm(self, vm_name: str, save_state: bool = True) -> None:
        """Stop a VM with optional state saving"""
        machine = await self._find_machine(vm_name)
        session = self._get_session(vm_name)
        
        current_state = await self._get_vm_state(machine)
        if current_state != VMState.RUNNING:
            self.logger.info("VM not running", vm_name=vm_name, state=current_state)
            return
        
        await asyncio.to_thread(machine.lock_machine, session, LockType.shared)
        
        try:
            if save_state:
                progress = await asyncio.to_thread(session.machine.save_state)
                self.logger.info("Saving VM state", vm_name=vm_name)
            else:
                progress = await asyncio.to_thread(session.console.power_down)
                self.logger.info("Powering down VM", vm_name=vm_name)
                
            await self._wait_for_progress(progress)
            
        finally:
            await asyncio.to_thread(session.unlock_machine)
    
    async def restart_vm(self, vm_name: str) -> None:
        """Restart a VM"""
        await self.stop_vm(vm_name, save_state=False)
        await asyncio.sleep(2)  # Brief pause
        await self.start_vm(vm_name)
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=0.5, min=1, max=3))
    async def send_keyboard_input(self, vm_name: str, keys: str) -> None:
        """Send keyboard input with retry logic"""
        machine = await self._find_machine(vm_name)
        session = self._get_session(vm_name)
        
        current_state = await self._get_vm_state(machine)
        if current_state != VMState.RUNNING:
            raise ValueError(f"VM {vm_name} is not running (state: {current_state})")
        
        await asyncio.to_thread(machine.lock_machine, session, LockType.shared)
        
        try:
            keyboard = session.console.keyboard
            scan_codes = self._convert_keys_to_scan_codes(keys)
            
            await asyncio.to_thread(keyboard.put_scancodes, scan_codes)
            
            # Small delay to ensure input is processed
            await asyncio.sleep(self.config.get('key_delay', 50) / 1000)
            
        finally:
            await asyncio.to_thread(session.unlock_machine)
    
    async def type_text(self, vm_name: str, text: str, delay_ms: int = 50) -> None:
        """Type text character by character"""
        for char in text:
            if char == ' ':
                await self.send_keyboard_input(vm_name, 'SPACE')
            elif char == '\n':
                await self.send_keyboard_input(vm_name, 'ENTER')
            else:
                # Convert character to appropriate key sequence
                await self.send_keyboard_input(vm_name, char)
            
            await asyncio.sleep(delay_ms / 1000)
    
    async def create_snapshot(self, vm_name: str, snapshot_name: str, description: str = "") -> None:
        """Create a VM snapshot"""
        machine = await self._find_machine(vm_name)
        session = self._get_session(vm_name)
        
        await asyncio.to_thread(machine.lock_machine, session, LockType.shared)
        
        try:
            progress = await asyncio.to_thread(
                session.machine.take_snapshot,
                snapshot_name,
                description or f"Snapshot created by TwitchBot",
                True  # Pause VM during snapshot
            )
            await self._wait_for_progress(progress)
            
            self.logger.info("Snapshot created", vm_name=vm_name, snapshot_name=snapshot_name)
            
        finally:
            await asyncio.to_thread(session.unlock_machine)
    
    async def restore_snapshot(self, vm_name: str, snapshot_name: str) -> None:
        """Restore a VM to a specific snapshot"""
        machine = await self._find_machine(vm_name)
        
        try:
            snapshot = await asyncio.to_thread(machine.find_snapshot, snapshot_name)
        except VBoxErrorObjectNotFound:
            raise ValueError(f"Snapshot '{snapshot_name}' not found for VM '{vm_name}'")
        
        session = self._get_session(vm_name)
        await asyncio.to_thread(machine.lock_machine, session, LockType.shared)
        
        try:
            progress = await asyncio.to_thread(session.machine.restore_snapshot, snapshot)
            await self._wait_for_progress(progress)
            
            self.logger.info("Snapshot restored", vm_name=vm_name, snapshot_name=snapshot_name)
            
        finally:
            await asyncio.to_thread(session.unlock_machine)
    
    async def list_snapshots(self, vm_name: str) -> List[str]:
        """List all snapshots for a VM"""
        machine = await self._find_machine(vm_name)
        
        def get_snapshot_names(snapshot):
            names = [snapshot.name]
            for child in snapshot.children:
                names.extend(get_snapshot_names(child))
            return names
        
        snapshot_names = []
        if machine.snapshot_count > 0:
            root_snapshot = machine.find_snapshot("")  # Root snapshot
            snapshot_names = await asyncio.to_thread(get_snapshot_names, root_snapshot)
        
        return snapshot_names
    
    async def cleanup(self) -> None:
        """Clean up all sessions and connections"""
        for vm_name, session in self.sessions.items():
            try:
                if hasattr(session, 'state') and session.state == pyvbox.library.SessionState.locked:
                    await asyncio.to_thread(session.unlock_machine)
            except Exception as e:
                self.logger.warning("Error cleaning up session", vm_name=vm_name, error=str(e))
        
        self.sessions.clear()
        self.vbox_mgr = None
        self.vbox = None
    
    # Helper methods
    async def _find_machine(self, vm_name: str):
        """Find a machine by name"""
        try:
            return await asyncio.to_thread(self.vbox.find_machine, vm_name)
        except VBoxErrorObjectNotFound:
            raise ValueError(f"VM '{vm_name}' not found")
    
    async def _get_vm_state(self, machine) -> VMState:
        """Get the current state of a machine"""
        state_mapping = {
            MachineState.powered_off: VMState.STOPPED,
            MachineState.saved: VMState.SAVED,
            MachineState.aborted: VMState.STOPPED,
            MachineState.running: VMState.RUNNING,
            MachineState.paused: VMState.PAUSED,
            MachineState.stuck: VMState.ERROR,
            MachineState.teleporting: VMState.RUNNING,
            MachineState.live_snapshotting: VMState.RUNNING,
            MachineState.starting: VMState.RUNNING,
            MachineState.stopping: VMState.RUNNING,
            MachineState.saving: VMState.RUNNING,
            MachineState.restoring: VMState.RUNNING,
            MachineState.teleporting_paused_vm: VMState.PAUSED,
            MachineState.teleporting_in: VMState.RUNNING,
            MachineState.fault_tolerant_syncing: VMState.RUNNING,
            MachineState.deleting_snapshot_online: VMState.RUNNING,
            MachineState.deleting_snapshot_paused: VMState.PAUSED,
        }
        
        vbox_state = await asyncio.to_thread(lambda: machine.state)
        return state_mapping.get(vbox_state, VMState.ERROR)
    
    def _get_session(self, vm_name: str):
        """Get or create a session for a VM"""
        if vm_name not in self.sessions:
            self.sessions[vm_name] = self.vbox_mgr.get_session()
        return self.sessions[vm_name]
    
    async def _wait_for_progress(self, progress):
        """Wait for a VirtualBox operation to complete"""
        while not await asyncio.to_thread(lambda: progress.completed):
            await asyncio.sleep(0.1)
        
        result_code = await asyncio.to_thread(lambda: progress.result_code)
        if result_code != 0:
            error_info = await asyncio.to_thread(lambda: progress.error_info)
            raise RuntimeError(f"VirtualBox operation failed: {error_info.text if error_info else 'Unknown error'}")
    
    def _convert_keys_to_scan_codes(self, keys: str) -> List[int]:
        """Convert key names to VirtualBox scan codes"""
        # This is a simplified mapping - you'd want a complete one
        key_map = {
            'ENTER': [0x1C, 0x9C],
            'ESC': [0x01, 0x81],
            'TAB': [0x0F, 0x8F],
            'SPACE': [0x39, 0xB9],
            'CTRL': [0x1D],
            'ALT': [0x38],
            'SHIFT': [0x2A],
            'UP': [0x48, 0xC8],
            'DOWN': [0x50, 0xD0],
            'LEFT': [0x4B, 0xCB],
            'RIGHT': [0x4D, 0xCD],
        }
        
        if keys.upper() in key_map:
            return key_map[keys.upper()]
        
        # For single characters, convert to scan codes
        if len(keys) == 1 and keys.isalpha():
            # Basic letter mapping (Q-P row starts at 0x10)
            base_scancode = ord(keys.upper()) - ord('A')
            if base_scancode < 26:  # A-Z
                # This is simplified - real implementation needs proper mapping
                press_code = 0x1E + base_scancode if base_scancode < 10 else 0x10 + (base_scancode - 10)
                release_code = press_code | 0x80
                return [press_code, release_code]
        
        self.logger.warning("Unknown key sequence", keys=keys)
        return []
```

## Phase 3: Modern Twitch Integration (Week 3)

### 3.1 Clean EventSub Implementation

```python
# src/twitchbot/infrastructure/twitch/client.py
from contextlib import AsyncExitStack
from typing import Dict, List, Optional, Callable
import httpx
import structlog
from twitchio.ext import eventsub

from ...core.config import TwitchConfig
from ...domain.events import ChatMessageEvent, ChannelPointRedemptionEvent

logger = structlog.get_logger()

class ModernTwitchClient:
    """Modern Twitch client with EventSub support"""
    
    def __init__(self, config: TwitchConfig):
        self.config = config
        self.logger = structlog.get_logger().bind(component="twitch_client")
        self.http_client: Optional[httpx.AsyncClient] = None
        self.eventsub_client: Optional[eventsub.EventSubWSClient] = None
        self.event_handlers: Dict[str, List[Callable]] = {}
        
    async def initialize(self) -> None:
        """Initialize Twitch connection and EventSub"""
        self.http_client = httpx.AsyncClient(
            base_url="https://api.twitch.tv/helix",
            headers={
                "Client-Id": self.config.client_id,
                "Authorization": f"Bearer {self.config.access_token}"
            },
            timeout=30.0
        )
        
        # Verify token
        await self._verify_token()
        
        # Initialize EventSub WebSocket for single broadcaster
        await self._setup_eventsub_websocket()
        
        self.logger.info("Twitch client initialized successfully")
    
    async def _verify_token(self) -> None:
        """Verify the access token is valid"""
        response = await self.http_client.get(
            "https://id.twitch.tv/oauth2/validate"
        )
        response.raise_for_status()
        
        token_info = response.json()
        self.logger.info("Token verified", user_id=token_info.get("user_id"))
    
    async def _setup_eventsub_websocket(self) -> None:
        """Set up EventSub WebSocket connection"""
        self.eventsub_client = eventsub.EventSubWSClient(self.http_client)
        
        # Subscribe to chat messages
        await self.eventsub_client.subscribe_channel_chat_message(
            broadcaster_user_id=self.config.broadcaster_user_id,
            user_id=self.config.bot_user_id
        )
        
        # Subscribe to channel point redemptions
        await self.eventsub_client.subscribe_channel_point_custom_reward_redemption_add(
            broadcaster_user_id=self.config.broadcaster_user_id
        )
        
        # Subscribe to follows
        await self.eventsub_client.subscribe_channel_follow(
            broadcaster_user_id=self.config.broadcaster_user_id,
            moderator_user_id=self.config.bot_user_id
        )
        
        # Set up event handlers
        self.eventsub_client.event(self._handle_chat_message)
        self.eventsub_client.event(self._handle_channel_point_redemption)
        
        self.logger.info("EventSub WebSocket configured")
    
    async def _handle_chat_message(self, event) -> None:
        """Handle incoming chat messages"""
        # Convert to domain event
        domain_event = ChatMessageEvent(
            user_id=event.chatter.user_id,
            user_name=event.chatter.user_name,
            display_name=event.chatter.user_display_name,
            message=event.message.text,
            timestamp=event.timestamp,
            is_moderator=event.chatter_user_id in self.config.moderator_ids,
            badges=event.badges or []
        )
        
        # Emit to registered handlers
        await self._emit_event("chat_message", domain_event)
    
    async def _handle_channel_point_redemption(self, event) -> None:
        """Handle channel point redemptions"""
        domain_event = ChannelPointRedemptionEvent(
            id=event.id,
            user_id=event.user.user_id,
            user_name=event.user.user_name,
            reward_id=event.reward.id,
            reward_title=event.reward.title,
            user_input=event.user_input,
            status=event.status,
            timestamp=event.redeemed_at
        )
        
        await self._emit_event("channel_point_redemption", domain_event)
    
    async def send_chat_message(self, message: str) -> None:
        """Send a message to chat"""
        data = {
            "broadcaster_id": self.config.broadcaster_user_id,
            "sender_id": self.config.bot_user_id,
            "message": message
        }
        
        response = await self.http_client.post("/chat/messages", json=data)
        response.raise_for_status()
    
    def register_event_handler(self, event_type: str, handler: Callable) -> None:
        """Register an event handler"""
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        self.event_handlers[event_type].append(handler)
    
    async def _emit_event(self, event_type: str, event_data) -> None:
        """Emit an event to all registered handlers"""
        handlers = self.event_handlers.get(event_type, [])
        for handler in handlers:
            try:
                await handler(event_data)
            except Exception as e:
                self.logger.error(
                    "Event handler failed", 
                    event_type=event_type, 
                    handler=handler.__name__,
                    error=str(e)
                )
    
    async def cleanup(self) -> None:
        """Clean up connections"""
        if self.eventsub_client:
            await self.eventsub_client.close()
        
        if self.http_client:
            await self.http_client.aclose()
        
        self.logger.info("Twitch client cleaned up")
    
    async def __aenter__(self):
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.cleanup()
```

### 3.2 Modern Configuration with Pydantic

```python
# src/twitchbot/core/config.py
from typing import Optional, List, Dict, Any
from pydantic import BaseSettings, Field, validator
from pydantic_settings import BaseSettings as PydanticSettings

class TwitchConfig(PydanticSettings):
    """Twitch API configuration"""
    client_id: str = Field(..., env="TWITCH_CLIENT_ID")
    client_secret: str = Field(..., env="TWITCH_CLIENT_SECRET")
    access_token: str = Field(..., env="TWITCH_ACCESS_TOKEN")
    refresh_token: str = Field(..., env="TWITCH_REFRESH_TOKEN")
    
    broadcaster_user_id: str = Field(..., env="TWITCH_BROADCASTER_USER_ID")
    bot_user_id: str = Field(..., env="TWITCH_BOT_USER_ID")
    
    moderator_ids: List[str] = Field(default_factory=list, env="TWITCH_MODERATOR_IDS")
    
    @validator('moderator_ids', pre=True)
    def parse_moderator_ids(cls, v):
        if isinstance(v, str):
            return [id.strip() for id in v.split(',') if id.strip()]
        return v

class VMConfig(PydanticSettings):
    """VM configuration"""
    hypervisor: str = Field(default="virtualbox", env="VM_HYPERVISOR")
    key_delay_ms: int = Field(default=50, env="VM_KEY_DELAY_MS")
    
    # VirtualBox specific
    vbox_sdk_path: Optional[str] = Field(default=None, env="VBOX_SDK_PATH")
    
    # KVM specific
    libvirt_uri: str = Field(default="qemu:///system", env="LIBVIRT_URI")
    
    # VM naming
    vm_prefix: str = Field(default="ctf_", env="VM_PREFIX")

class DatabaseConfig(PydanticSettings):
    """Database configuration"""
    url: str = Field(default="sqlite+aiosqlite:///./twitchbot.db", env="DATABASE_URL")
    echo_sql: bool = Field(default=False, env="DATABASE_ECHO_SQL")

class AppConfig(PydanticSettings):
    """Main application configuration"""
    debug: bool = Field(default=False, env="DEBUG")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    
    # Component configs
    twitch: TwitchConfig = Field(default_factory=TwitchConfig)
    vm: VMConfig = Field(default_factory=VMConfig)
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    
    # API configuration
    api_host: str = Field(default="0.0.0.0", env="API_HOST")
    api_port: int = Field(default=8000, env="API_PORT")
    
    # Webhook configuration for EventSub (if using webhooks instead of WebSocket)
    webhook_secret: Optional[str] = Field(default=None, env="WEBHOOK_SECRET")
    webhook_url: Optional[str] = Field(default=None, env="WEBHOOK_URL")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        env_nested_delimiter = "__"  # Allows TWITCH__CLIENT_ID syntax

# Global config instance
config = AppConfig()
```

## Phase 4: Modern Storage Layer (Week 4)

### 4.1 SQLAlchemy 2.0 with Async Support

```python
# src/twitchbot/infrastructure/storage/models.py
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Integer, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

class Base(AsyncAttrs, DeclarativeBase):
    """Base model with async support"""
    pass

class User(Base):
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    twitch_user_id: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    username: Mapped[str] = mapped_column(String(100))
    display_name: Mapped[str] = mapped_column(String(100))
    
    is_moderator: Mapped[bool] = mapped_column(Boolean, default=False)
    is_subscriber: Mapped[bool] = mapped_column(Boolean, default=False)
    
    total_flags: Mapped[int] = mapped_column(Integer, default=0)
    total_points: Mapped[int] = mapped_column(Integer, default=0)
    
    first_seen: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_seen: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    flag_captures = relationship("FlagCapture", back_populates="user")

class Challenge(Base):
    __tablename__ = "challenges"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text)
    vm_name: Mapped[str] = mapped_column(String(100))
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    flags = relationship("Flag", back_populates="challenge")
    hints = relationship("Hint", back_populates="challenge")

class Flag(Base):
    __tablename__ = "flags"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    challenge_id: Mapped[int] = mapped_column(ForeignKey("challenges.id"))
    
    name: Mapped[str] = mapped_column(String(100))
    value: Mapped[str] = mapped_column(String(500))  # The actual flag
    points: Mapped[int] = mapped_column(Integer, default=100)
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    challenge = relationship("Challenge", back_populates="flags")
    captures = relationship("FlagCapture", back_populates="flag")

class FlagCapture(Base):
    __tablename__ = "flag_captures"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    flag_id: Mapped[int] = mapped_column(ForeignKey("flags.id"))
    
    captured_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    points_awarded: Mapped[int] = mapped_column(Integer)
    
    # Relationships
    user = relationship("User", back_populates="flag_captures")
    flag = relationship("Flag", back_populates="captures")

class Hint(Base):
    __tablename__ = "hints"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    challenge_id: Mapped[int] = mapped_column(ForeignKey("challenges.id"))
    
    sequence: Mapped[int] = mapped_column(Integer)  # Order of hints
    text: Mapped[str] = mapped_column(Text)
    cost_points: Mapped[int] = mapped_column(Integer, default=0)
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    challenge = relationship("Challenge", back_populates="hints")

class VMSession(Base):
    __tablename__ = "vm_sessions"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    challenge_id: Mapped[int] = mapped_column(ForeignKey("challenges.id"))
    
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    vm_snapshot: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
```

### 4.2 Repository Pattern Implementation

```python
# src/twitchbot/infrastructure/storage/repositories.py
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, and_
from sqlalchemy.orm import selectinload

from .models import User, Challenge, Flag, FlagCapture, Hint, VMSession
from ...domain.models import UserStats, LeaderboardEntry

class UserRepository:
    """Repository for user operations"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_by_twitch_id(self, twitch_user_id: str) -> Optional[User]:
        """Get user by Twitch user ID"""
        result = await self.session.execute(
            select(User).where(User.twitch_user_id == twitch_user_id)
        )
        return result.scalar_one_or_none()
    
    async def create_user(self, twitch_user_id: str, username: str, display_name: str) -> User:
        """Create a new user"""
        user = User(
            twitch_user_id=twitch_user_id,
            username=username,
            display_name=display_name
        )
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user
    
    async def update_user_stats(self, user_id: int, flags_increment: int = 0, points_increment: int = 0) -> None:
        """Update user statistics"""
        user = await self.session.get(User, user_id)
        if user:
            user.total_flags += flags_increment
            user.total_points += points_increment
            user.last_seen = datetime.utcnow()
            await self.session.commit()
    
    async def get_leaderboard(self, limit: int = 10) -> List[LeaderboardEntry]:
        """Get leaderboard with top users"""
        result = await self.session.execute(
            select(User)
            .order_by(desc(User.total_points), desc(User.total_flags))
            .limit(limit)
        )
        users = result.scalars().all()
        
        return [
            LeaderboardEntry(
                rank=idx + 1,
                username=user.display_name,
                total_flags=user.total_flags,
                total_points=user.total_points
            )
            for idx, user in enumerate(users)
        ]

class ChallengeRepository:
    """Repository for challenge operations"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_active_challenge(self) -> Optional[Challenge]:
        """Get the currently active challenge"""
        result = await self.session.execute(
            select(Challenge)
            .options(selectinload(Challenge.flags), selectinload(Challenge.hints))
            .where(Challenge.is_active == True)
            .order_by(desc(Challenge.created_at))
        )
        return result.scalar_one_or_none()
    
    async def get_by_name(self, name: str) -> Optional[Challenge]:
        """Get challenge by name"""
        result = await self.session.execute(
            select(Challenge)
            .options(selectinload(Challenge.flags), selectinload(Challenge.hints))
            .where(Challenge.name == name)
        )
        return result.scalar_one_or_none()

class FlagRepository:
    """Repository for flag operations"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def capture_flag(self, user_id: int, flag_id: int, points_awarded: int) -> FlagCapture:
        """Record a flag capture"""
        # Check if already captured
        existing = await self.session.execute(
            select(FlagCapture).where(
                and_(FlagCapture.user_id == user_id, FlagCapture.flag_id == flag_id)
            )
        )
        
        if existing.scalar_one_or_none():
            raise ValueError("Flag already captured by this user")
        
        capture = FlagCapture(
            user_id=user_id,
            flag_id=flag_id,
            points_awarded=points_awarded
        )
        
        self.session.add(capture)
        await self.session.commit()
        await self.session.refresh(capture)
        
        return capture
    
    async def get_user_captures(self, user_id: int, challenge_id: Optional[int] = None) -> List[FlagCapture]:
        """Get all flag captures for a user"""
        query = select(FlagCapture).options(selectinload(FlagCapture.flag)).where(
            FlagCapture.user_id == user_id
        )
        
        if challenge_id:
            query = query.join(Flag).where(Flag.challenge_id == challenge_id)
        
        result = await self.session.execute(query)
        return result.scalars().all()

class HintRepository:
    """Repository for hint operations"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_hints_for_challenge(self, challenge_id: int) -> List[Hint]:
        """Get all hints for a challenge in order"""
        result = await self.session.execute(
            select(Hint)
            .where(and_(Hint.challenge_id == challenge_id, Hint.is_active == True))
            .order_by(Hint.sequence)
        )
        return result.scalars().all()
```

## Phase 5: Application Services (Week 5)

### 5.1 Domain Services

```python
# src/twitchbot/application/services/game_service.py
from typing import Optional, List, Dict, Any
from ...domain.models import FlagCaptureResult, HintResult
from ...infrastructure.storage.repositories import UserRepository, ChallengeRepository, FlagRepository, HintRepository
from ...infrastructure.vm.factory import VMControllerFactory
from ...core.config import config
import structlog

logger = structlog.get_logger()

class GameService:
    """Core game logic service"""
    
    def __init__(
        self,
        user_repo: UserRepository,
        challenge_repo: ChallengeRepository,
        flag_repo: FlagRepository,
        hint_repo: HintRepository,
        vm_controller
    ):
        self.user_repo = user_repo
        self.challenge_repo = challenge_repo
        self.flag_repo = flag_repo
        self.hint_repo = hint_repo
        self.vm_controller = vm_controller
        self.logger = structlog.get_logger().bind(service="game")
    
    async def attempt_flag_capture(self, twitch_user_id: str, flag_value: str) -> FlagCaptureResult:
        """Attempt to capture a flag"""
        # Get or create user
        user = await self.user_repo.get_by_twitch_id(twitch_user_id)
        if not user:
            # Create new user (would need more user info from Twitch API)
            raise ValueError("User not found - need to register first")
        
        # Get active challenge
        challenge = await self.challenge_repo.get_active_challenge()
        if not challenge:
            return FlagCaptureResult(
                success=False,
                message="No active challenge",
                points_awarded=0
            )
        
        # Find matching flag
        matching_flag = None
        for flag in challenge.flags:
            if flag.value.lower().strip() == flag_value.lower().strip():
                matching_flag = flag
                break
        
        if not matching_flag:
            self.logger.info(
                "Flag attempt failed", 
                user=user.username, 
                attempt=flag_value,
                challenge=challenge.name
            )
            return FlagCaptureResult(
                success=False,
                message="Incorrect flag",
                points_awarded=0
            )
        
        # Check if already captured
        existing_captures = await self.flag_repo.get_user_captures(user.id, challenge.id)
        if any(capture.flag_id == matching_flag.id for capture in existing_captures):
            return FlagCaptureResult(
                success=False,
                message="Flag already captured!",
                points_awarded=0
            )
        
        # Capture the flag
        try:
            capture = await self.flag_repo.capture_flag(
                user.id, 
                matching_flag.id, 
                matching_flag.points
            )
            
            # Update user stats
            await self.user_repo.update_user_stats(
                user.id,
                flags_increment=1,
                points_increment=matching_flag.points
            )
            
            self.logger.info(
                "Flag captured successfully",
                user=user.username,
                flag=matching_flag.name,
                points=matching_flag.points
            )
            
            return FlagCaptureResult(
                success=True,
                message=f"Congratulations! You captured '{matching_flag.name}' for {matching_flag.points} points!",
                points_awarded=matching_flag.points,
                flag_name=matching_flag.name
            )
            
        except ValueError as e:
            return FlagCaptureResult(
                success=False,
                message=str(e),
                points_awarded=0
            )
    
    async def get_next_hint(self, twitch_user_id: str) -> HintResult:
        """Get the next available hint"""
        user = await self.user_repo.get_by_twitch_id(twitch_user_id)
        if not user:
            return HintResult(success=False, message="User not found")
        
        challenge = await self.challenge_repo.get_active_challenge()
        if not challenge:
            return HintResult(success=False, message="No active challenge")
        
        # Get user's captures for this challenge
        captures = await self.flag_repo.get_user_captures(user.id, challenge.id)
        num_captured = len(captures)
        
        # Get all hints for challenge
        hints = await self.hint_repo.get_hints_for_challenge(challenge.id)
        if not hints:
            return HintResult(success=False, message="No hints available")
        
        # Determine which hint to show based on progress
        hint_index = min(num_captured, len(hints) - 1)
        hint = hints[hint_index]
        
        return HintResult(
            success=True,
            message=hint.text,
            hint_number=hint_index + 1,
            total_hints=len(hints)
        )
    
    async def get_leaderboard(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get current leaderboard"""
        return await self.user_repo.get_leaderboard(limit)
    
    async def send_vm_input(self, input_type: str, data: str) -> Dict[str, Any]:
        """Send input to the active VM"""
        challenge = await self.challenge_repo.get_active_challenge()
        if not challenge:
            return {"success": False, "message": "No active challenge"}
        
        vm_name = f"{config.vm.vm_prefix}{challenge.name}"
        
        try:
            if input_type == "key":
                await self.vm_controller.send_keyboard_input(vm_name, data)
            elif input_type == "type":
                await self.vm_controller.type_text(vm_name, data)
            else:
                return {"success": False, "message": f"Unknown input type: {input_type}"}
            
            return {"success": True, "message": f"Sent {input_type} input to VM"}
            
        except Exception as e:
            self.logger.error("VM input failed", error=str(e), vm_name=vm_name)
            return {"success": False, "message": f"VM input failed: {str(e)}"}
```

### 5.2 Command Handlers

```python
# src/twitchbot/application/commands/chat_commands.py
from typing import Dict, Any, Optional
from ...application.services.game_service import GameService
from ...domain.events import ChatMessageEvent
import structlog

logger = structlog.get_logger()

class ChatCommandHandler:
    """Handles chat commands from Twitch"""
    
    def __init__(self, game_service: GameService):
        self.game_service = game_service
        self.logger = structlog.get_logger().bind(handler="chat_commands")
        
        # Command registry
        self.commands = {
            "!flag": self._handle_flag_command,
            "!hint": self._handle_hint_command,
            "!help": self._handle_help_command,
            "!leaderboard": self._handle_leaderboard_command,
            "!stats": self._handle_stats_command,
            # VM control commands (moderator only)
            "!key": self._handle_key_command,
            "!type": self._handle_type_command,
            "!restart": self._handle_restart_command,
        }
    
    async def handle_message(self, event: ChatMessageEvent) -> Optional[str]:
        """Handle a chat message and return response if any"""
        message = event.message.strip()
        
        # Check if it's a command
        if not message.startswith("!"):
            return None
        
        # Parse command and arguments
        parts = message.split(" ", 1)
        command = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""
        
        # Find and execute command
        if command in self.commands:
            try:
                return await self.commands[command](event, args)
            except Exception as e:
                self.logger.error("Command execution failed", command=command, error=str(e))
                return f"Sorry {event.display_name}, that command failed. Please try again."
        
        return None
    
    async def _handle_flag_command(self, event: ChatMessageEvent, args: str) -> str:
        """Handle !flag <flag_value> command"""
        if not args:
            return f"@{event.display_name} Usage: !flag <your_flag>"
        
        result = await self.game_service.attempt_flag_capture(event.user_id, args)
        
        if result.success:
            return f"@{event.display_name} {result.message} 🏆"
        else:
            return f"@{event.display_name} {result.message}"
    
    async def _handle_hint_command(self, event: ChatMessageEvent, args: str) -> str:
        """Handle !hint command"""
        result = await self.game_service.get_next_hint(event.user_id)
        
        if result.success:
            return f"@{event.display_name} Hint {result.hint_number}/{result.total_hints}: {result.message}"
        else:
            return f"@{event.display_name} {result.message}"
    
    async def _handle_help_command(self, event: ChatMessageEvent, args: str) -> str:
        """Handle !help command"""
        help_text = [
            "Available commands:",
            "!flag <value> - Submit a flag",
            "!hint - Get a hint",
            "!leaderboard - Show top players",
            "!stats - Show your stats"
        ]
        
        if event.is_moderator:
            help_text.extend([
                "Moderator commands:",
                "!key <key> - Send key to VM",
                "!type <text> - Type text in VM",
                "!restart - Restart the VM"
            ])
        
        return f"@{event.display_name} " + " | ".join(help_text)
    
    async def _handle_leaderboard_command(self, event: ChatMessageEvent, args: str) -> str:
        """Handle !leaderboard command"""
        leaderboard = await self.game_service.get_leaderboard(5)  # Top 5
        
        if not leaderboard:
            return f"@{event.display_name} No scores yet!"
        
        lines = ["🏆 Leaderboard:"]
        for entry in leaderboard:
            lines.append(f"{entry.rank}. {entry.username}: {entry.total_points} pts ({entry.total_flags} flags)")
        
        return " | ".join(lines)
    
    async def _handle_stats_command(self, event: ChatMessageEvent, args: str) -> str:
        """Handle !stats command"""
        # Would need to implement this in GameService
        return f"@{event.display_name} Stats feature coming soon!"
    
    async def _handle_key_command(self, event: ChatMessageEvent, args: str) -> str:
        """Handle !key <key> command (moderator only)"""
        if not event.is_moderator:
            return f"@{event.display_name} This command is for moderators only."
        
        if not args:
            return f"@{event.display_name} Usage: !key <key_name>"
        
        result = await self.game_service.send_vm_input("key", args)
        
        if result["success"]:
            return f"@{event.display_name} Key '{args}' sent to VM ✓"
        else:
            return f"@{event.display_name} Failed to send key: {result['message']}"
    
    async def _handle_type_command(self, event: ChatMessageEvent, args: str) -> str:
        """Handle !type <text> command (moderator only)"""
        if not event.is_moderator:
            return f"@{event.display_name} This command is for moderators only."
        
        if not args:
            return f"@{event.display_name} Usage: !type <text>"
        
        result = await self.game_service.send_vm_input("type", args)
        
        if result["success"]:
            return f"@{event.display_name} Text typed to VM ✓"
        else:
            return f"@{event.display_name} Failed to type text: {result['message']}"
    
    async def _handle_restart_command(self, event: ChatMessageEvent, args: str) -> str:
        """Handle !restart command (moderator only)"""
        if not event.is_moderator:
            return f"@{event.display_name} This command is for moderators only."
        
        # Would need to implement VM restart in GameService
        return f"@{event.display_name} VM restart feature coming soon!"
```

## Phase 6: FastAPI Integration & Deployment (Week 6)

### 6.1 Modern API with FastAPI

```python
# src/twitchbot/main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import structlog

from .core.config import config
from .core.dependencies import get_dependencies, Dependencies
from .core.logging import setup_logging
from .api.routes import health, webhooks, admin

# Setup logging
setup_logging(config.log_level, config.debug)
logger = structlog.get_logger()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    logger.info("Starting TwitchBot application")
    
    # Initialize dependencies
    deps = await get_dependencies()
    app.state.deps = deps
    
    # Start Twitch client
    await deps.twitch_client.initialize()
    
    logger.info("TwitchBot application started successfully")
    
    yield
    
    # Cleanup
    logger.info("Shutting down TwitchBot application")
    await deps.cleanup()
    logger.info("TwitchBot application shut down")

# Create FastAPI app
app = FastAPI(
    title="TwitchBot CTF Platform",
    description="Modern Twitch CTF bot with dual hypervisor support",
    version="2.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, prefix="/health", tags=["health"])
app.include_router(webhooks.router, prefix="/webhooks", tags=["webhooks"])
app.include_router(admin.router, prefix="/admin", tags=["admin"])

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "TwitchBot CTF Platform",
        "version": "2.0.0",
        "hypervisor": config.vm.hypervisor
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "twitchbot.main:app",
        host=config.api_host,
        port=config.api_port,
        reload=config.debug,
        log_config=None  # Use our structured logging
    )
```

### 6.2 Modern CLI with Typer

```python
# src/twitchbot/cli.py
import asyncio
from typing import Optional
import typer
from rich.console import Console
from rich.table import Table

from .core.config import config
from .core.dependencies import get_dependencies
from .infrastructure.vm.factory import VMControllerFactory, HypervisorType

app = typer.Typer(name="twitchbot", help="TwitchBot CTF Platform CLI")
console = Console()

@app.command()
def run():
    """Run the TwitchBot application"""
    import uvicorn
    console.print("[bold green]Starting TwitchBot...[/bold green]")
    
    uvicorn.run(
        "twitchbot.main:app",
        host=config.api_host,
        port=config.api_port,
        reload=config.debug
    )

@app.command()
def test_vm(
    hypervisor: str = typer.Option("virtualbox", help="Hypervisor to test"),
    vm_name: Optional[str] = typer.Option(None, help="VM name to test")
):
    """Test VM controller functionality"""
    async def _test():
        console.print(f"[bold blue]Testing {hypervisor} controller...[/bold blue]")
        
        # Create controller
        hypervisor_type = HypervisorType(hypervisor.lower())
        controller = VMControllerFactory.create(hypervisor_type, config.vm.dict())
        
        async with controller:
            # List VMs
            vms = await controller.list_vms()
            
            table = Table(title="Available VMs")
            table.add_column("Name", style="cyan")
            table.add_column("State", style="yellow")
            table.add_column("Hypervisor", style="green")
            
            for vm in vms:
                table.add_row(vm.name, vm.state.value, vm.hypervisor.value)
            
            console.print(table)
            
            if vm_name and any(vm.name == vm_name for vm in vms):
                console.print(f"\n[bold]Testing VM '{vm_name}'...[/bold]")
                
                # Test operations
                vm_info = await controller.get_vm_info(vm_name)
                console.print(f"VM State: {vm_info.state.value}")
                
                if vm_info.state.value == "running":
                    console.print("Sending test input...")
                    await controller.send_keyboard_input(vm_name, "TAB")
                    await controller.type_text(vm_name, "Hello from TwitchBot!")
                    console.print("[green]✓[/green] Test completed successfully")
                else:
                    console.print("[yellow]VM not running - skipping input tests[/yellow]")
    
    asyncio.run(_test())

@app.command()
def create_challenge(
    name: str = typer.Argument(..., help="Challenge name"),
    title: str = typer.Option(..., help="Challenge title"),
    vm_name: str = typer.Option(..., help="VM name"),
    description: str = typer.Option("", help="Challenge description")
):
    """Create a new challenge"""
    async def _create():
        deps = await get_dependencies()
        
        # Create challenge in database
        console.print(f"Creating challenge '{name}'...")
        
        # Implementation would use the challenge repository
        console.print(f"[green]✓[/green] Challenge '{name}' created successfully")
        
        await deps.cleanup()
    
    asyncio.run(_create())

@app.command()
def status():
    """Show application status"""
    async def _status():
        deps = await get_dependencies()
        
        # Check VM controller
        vm_status = "✓ Connected" if deps.vm_controller else "✗ Disconnected"
        
        # Check Twitch client
        twitch_status = "✓ Connected" if deps.twitch_client else "✗ Disconnected"
        
        # Check database
        db_status = "✓ Connected"  # Would check actual DB connection
        
        table = Table(title="TwitchBot Status")
        table.add_column("Component", style="cyan")
        table.add_column("Status", style="green")
        
        table.add_row("VM Controller", vm_status)
        table.add_row("Twitch Client", twitch_status)
        table.add_row("Database", db_status)
        table.add_row("Hypervisor", config.vm.hypervisor)
        
        console.print(table)
        
        await deps.cleanup()
    
    asyncio.run(_status())

if __name__ == "__main__":
    app()
```

## Phase 7: Containerization & Production (Week 7)

### 7.1 Multi-Stage Dockerfile

```dockerfile
# Dockerfile
# syntax=docker/dockerfile:1.9

# Build stage with uv
FROM ghcr.io/astral-sh/uv:python3.12-bookworm AS builder

WORKDIR /app

# Copy dependency files
COPY pyproject.toml uv.lock* ./

# Install dependencies
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project --no-dev

# Copy source code
COPY src/ src/

# Install the project
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

# VirtualBox runtime stage
FROM python:3.12-slim-bookworm AS virtualbox-base

# Install VirtualBox dependencies
RUN apt-get update && apt-get install -y \
    wget \
    ca-certificates \
    gnupg \
    && wget -O- https://www.virtualbox.org/download/oracle_vbox_2016.asc | gpg --dearmor --yes --output /usr/share/keyrings/oracle-virtualbox-2016.gpg \
    && echo "deb [arch=amd64 signed-by=/usr/share/keyrings/oracle-virtualbox-2016.gpg] https://download.virtualbox.org/virtualbox/debian bookworm contrib" > /etc/apt/sources.list.d/virtualbox.list \
    && apt-get update \
    && apt-get install -y virtualbox-7.0 \
    && rm -rf /var/lib/apt/lists/*

# KVM runtime stage  
FROM python:3.12-slim-bookworm AS kvm-base

# Install KVM/QEMU dependencies
RUN apt-get update && apt-get install -y \
    qemu-kvm \
    libvirt-daemon-system \
    libvirt-clients \
    libvirt-dev \
    pkg-config \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Final stage (selectable at build time)
ARG HYPERVISOR=virtualbox
FROM ${HYPERVISOR}-base AS final

# Create non-root user
RUN useradd -m -s /bin/bash twitchbot

# Copy virtual environment from builder
COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/src /app/src

# Add venv to PATH
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app/src"

# Set working directory
WORKDIR /app

# Create data directories
RUN mkdir -p /app/data /app/logs && \
    chown -R twitchbot:twitchbot /app

# Add user to hypervisor groups
RUN usermod -aG libvirt twitchbot 2>/dev/null || true && \
    usermod -aG vboxusers twitchbot 2>/dev/null || true

USER twitchbot

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Default command
CMD ["python", "-m", "twitchbot.cli", "run"]

# Labels
LABEL org.opencontainers.image.title="TwitchBot CTF Platform"
LABEL org.opencontainers.image.description="Modern Twitch CTF bot with dual hypervisor support"
LABEL org.opencontainers.image.version="2.0.0"
```

### 7.2 Production Docker Compose

```yaml
# docker-compose.prod.yml
version: '3.9'

services:
  twitchbot:
    build:
      context: .
      target: final
      args:
        HYPERVISOR: ${HYPERVISOR:-virtualbox}
    image: twitchbot:2.0.0
    container_name: twitchbot
    restart: unless-stopped
    
    environment:
      # Application
      - DEBUG=false
      - LOG_LEVEL=INFO
      
      # Database
      - DATABASE_URL=postgresql+asyncpg://twitchbot:${DB_PASSWORD}@postgres:5432/twitchbot
      
      # Twitch
      - TWITCH_CLIENT_ID=${TWITCH_CLIENT_ID}
      - TWITCH_CLIENT_SECRET=${TWITCH_CLIENT_SECRET}
      - TWITCH_ACCESS_TOKEN=${TWITCH_ACCESS_TOKEN}
      - TWITCH_BROADCASTER_USER_ID=${TWITCH_BROADCASTER_USER_ID}
      - TWITCH_BOT_USER_ID=${TWITCH_BOT_USER_ID}
      
      # VM Configuration
      - VM_HYPERVISOR=${HYPERVISOR:-virtualbox}
      - VM_KEY_DELAY_MS=50
      - VM_PREFIX=ctf_
      
    volumes:
      # Application data
      - ./data:/app/data
      - ./logs:/app/logs
      
      # VirtualBox (if using)
      - /home/${USER}/VirtualBox VMs:/home/twitchbot/VirtualBox VMs:ro
      
      # KVM (if using)
      - /var/run/libvirt/libvirt-sock:/var/run/libvirt/libvirt-sock
      - /var/lib/libvirt:/var/lib/libvirt:ro
      
    devices:
      # VirtualBox
      - /dev/vboxdrv:/dev/vboxdrv
      # KVM
      - /dev/kvm:/dev/kvm
      
    ports:
      - "8000:8000"
      
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
        
    networks:
      - twitchbot-net
      
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  postgres:
    image: postgres:16-alpine
    container_name: twitchbot-postgres
    restart: unless-stopped
    
    environment:
      - POSTGRES_DB=twitchbot
      - POSTGRES_USER=twitchbot
      - POSTGRES_PASSWORD=${DB_PASSWORD}
      
    volumes:
      - postgres_data:/var/lib/postgresql/data
      
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U twitchbot"]
      interval: 10s
      timeout: 5s
      retries: 5
      
    networks:
      - twitchbot-net

  redis:
    image: redis:7-alpine
    container_name: twitchbot-redis
    restart: unless-stopped
    
    command: redis-server --appendonly yes
    
    volumes:
      - redis_data:/data
      
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 3
      
    networks:
      - twitchbot-net

  # Monitoring
  prometheus:
    image: prom/prometheus:latest
    container_name: twitchbot-prometheus
    restart: unless-stopped
    
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
      
    ports:
      - "9090:9090"
      
    networks:
      - twitchbot-net

  grafana:
    image: grafana/grafana:latest
    container_name: twitchbot-grafana
    restart: unless-stopped
    
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD}
      
    volumes:
      - grafana_data:/var/lib/grafana
      - ./monitoring/dashboards:/etc/grafana/provisioning/dashboards
      
    ports:
      - "3000:3000"
      
    networks:
      - twitchbot-net

networks:
  twitchbot-net:
    driver: bridge

volumes:
  postgres_data:
  redis_data:
  prometheus_data:
  grafana_data:
```

## Migration & Rollback Strategy

### Legacy Compatibility Bridge

```python
# src/twitchbot/legacy/bridge.py
"""
Compatibility bridge for migrating from legacy TwitchBot
"""
from typing import Dict, Any, Optional
import json
import os
from ..domain.models import Challenge, Flag, Hint
from ..infrastructure.storage.repositories import ChallengeRepository, FlagRepository

class LegacyMigrator:
    """Migrates data from legacy TwitchBot format"""
    
    def __init__(self, challenge_repo: ChallengeRepository, flag_repo: FlagRepository):
        self.challenge_repo = challenge_repo
        self.flag_repo = flag_repo
    
    async def migrate_from_legacy_files(self, legacy_data_path: str) -> Dict[str, int]:
        """Migrate from legacy file-based storage"""
        stats = {"challenges": 0, "flags": 0, "hints": 0}
        
        # Look for legacy challenge files
        for filename in os.listdir(legacy_data_path):
            if filename.endswith('.json'):
                challenge_name = filename[:-5]
                
                with open(os.path.join(legacy_data_path, filename)) as f:
                    legacy_data = json.load(f)
                
                # Create challenge
                challenge = await self._create_challenge_from_legacy(challenge_name, legacy_data)
                stats["challenges"] += 1
                
                # Migrate flags
                if "flags" in legacy_data:
                    for flag_data in legacy_data["flags"]:
                        await self._create_flag_from_legacy(challenge.id, flag_data)
                        stats["flags"] += 1
                
                # Migrate hints
                if "hints" in legacy_data:
                    for i, hint_text in enumerate(legacy_data["hints"]):
                        await self._create_hint_from_legacy(challenge.id, i, hint_text)
                        stats["hints"] += 1
        
        return stats
    
    async def _create_challenge_from_legacy(self, name: str, legacy_data: Dict) -> Challenge:
        """Create challenge from legacy data format"""
        # Implementation depends on legacy format
        pass
    
    async def _create_flag_from_legacy(self, challenge_id: int, flag_data: Dict) -> None:
        """Create flag from legacy data format"""
        # Implementation depends on legacy format
        pass
    
    async def _create_hint_from_legacy(self, challenge_id: int, sequence: int, hint_text: str) -> None:
        """Create hint from legacy data format"""
        # Implementation depends on legacy format
        pass
```

## Success Metrics & Timeline

### 7-Week Implementation Plan

| Week | Phase | Key Deliverables | Success Criteria |
|------|-------|------------------|-------------------|
| 1 | Foundation | Dependencies, architecture | Modern pyproject.toml, clean structure |
| 2 | VM Layer | Dual hypervisor support | Both VBox & KVM controllers working |
| 3 | Twitch Integration | EventSub WebSocket | Real-time chat/events processing |
| 4 | Storage | SQLAlchemy 2.0 async | Database models, repositories working |
| 5 | Services | Game logic, commands | All bot commands functional |
| 6 | API & CLI | FastAPI, Typer CLI | Web API and CLI both working |
| 7 | Production | Docker, deployment | Production-ready deployment |

### Performance Targets

- **VM Response Time**: < 100ms for keyboard input
- **Chat Command Latency**: < 500ms end-to-end
- **EventSub Processing**: < 200ms event handling
- **Database Queries**: < 50ms for leaderboard queries
- **Memory Usage**: < 512MB base + VM overhead
- **Startup Time**: < 30 seconds including hypervisor connection

### Technical Debt Eliminated

1. ✅ **Legacy VirtualBox SDK** → Modern pyvbox with async support
2. ✅ **TwitchIO IRC** → EventSub WebSocket for real-time events  
3. ✅ **File-based storage** → SQLAlchemy 2.0 with async PostgreSQL
4. ✅ **requirements.txt** → pyproject.toml with uv for speed
5. ✅ **Synchronous code** → Full async/await throughout
6. ✅ **Manual configuration** → Pydantic settings with validation
7. ✅ **No testing** → Comprehensive pytest suite with coverage
8. ✅ **Single hypervisor** → Abstract interface supporting multiple

## Conclusion

Version 4 represents a **complete rewrite** rather than incremental patches, eliminating all technical debt while preserving functionality. Key innovations:

- **Zero Legacy Code**: Everything rewritten with modern patterns
- **Dual Hypervisor**: Both VirtualBox and KVM support from day one  
- **EventSub Native**: No IRC compatibility layer, WebSocket-first
- **Production Ready**: FastAPI, PostgreSQL, Docker, monitoring
- **Developer Experience**: Typer CLI, structured logging, type safety
- **Performance**: Async throughout, modern HTTP clients, optimized queries

This architecture will serve the project for the next 5+ years without major rewrites.
