# TwitchBot Modernization Plan V3 - Dual Hypervisor Support
## VirtualBox (Enhanced SDK) + KVM/QEMU Support

## Executive Summary
Modernize the TwitchBot to support both VirtualBox (with improved Python SDK) and KVM/QEMU hypervisors. This approach maintains backward compatibility with existing VMs while enabling superior performance for new deployments.

## Architecture Overview

### Dual Hypervisor Strategy
- **VirtualBox**: Retain for existing VMs, upgrade to pyvbox SDK
- **KVM/QEMU**: Add support for new deployments and Linux hosts
- **Abstraction Layer**: Unified interface for both hypervisors
- **Runtime Selection**: Choose hypervisor based on configuration

## Phase 1: Hypervisor Abstraction Layer (Week 1-2)

### 1.1 Abstract VM Interface
```python
# core/vm/base.py
from abc import ABC, abstractmethod
from typing import Protocol, Optional, List, Dict, Any
from contextlib import asynccontextmanager
from enum import Enum

class HypervisorType(Enum):
    VIRTUALBOX = "virtualbox"
    KVM = "kvm"
    MOCK = "mock"  # For testing

class VMState(Enum):
    STOPPED = "stopped"
    RUNNING = "running"
    PAUSED = "paused"
    SAVED = "saved"

class VMController(ABC):
    """Abstract base class for VM controllers"""
    
    @abstractmethod
    async def initialize(self) -> None:
        """Initialize connection to hypervisor"""
        pass
    
    @abstractmethod
    async def list_vms(self) -> List[str]:
        """List available VMs"""
        pass
    
    @abstractmethod
    async def start(self, vm_name: str) -> None:
        """Start a VM"""
        pass
    
    @abstractmethod
    async def stop(self, vm_name: str, save_state: bool = True) -> None:
        """Stop a VM, optionally saving state"""
        pass
    
    @abstractmethod
    async def send_keys(self, vm_name: str, keys: str) -> None:
        """Send keyboard input to VM"""
        pass
    
    @abstractmethod
    async def type_text(self, vm_name: str, text: str) -> None:
        """Type text into VM"""
        pass
    
    @abstractmethod
    async def snapshot(self, vm_name: str, snapshot_name: str) -> None:
        """Create a VM snapshot"""
        pass
    
    @abstractmethod
    async def restore_snapshot(self, vm_name: str, snapshot_name: str) -> None:
        """Restore a VM snapshot"""
        pass
    
    @abstractmethod
    async def get_state(self, vm_name: str) -> VMState:
        """Get current VM state"""
        pass
    
    @abstractmethod
    async def cleanup(self) -> None:
        """Cleanup resources"""
        pass

class VMControllerFactory:
    """Factory for creating VM controllers"""
    
    @staticmethod
    def create(hypervisor: HypervisorType, **kwargs) -> VMController:
        """Create appropriate VM controller based on hypervisor type"""
        match hypervisor:
            case HypervisorType.VIRTUALBOX:
                from .virtualbox_controller import VirtualBoxController
                return VirtualBoxController(**kwargs)
            case HypervisorType.KVM:
                from .kvm_controller import KVMController
                return KVMController(**kwargs)
            case HypervisorType.MOCK:
                from .mock_controller import MockController
                return MockController(**kwargs)
            case _:
                raise ValueError(f"Unsupported hypervisor: {hypervisor}")
```

### 1.2 Enhanced VirtualBox Controller with pyvbox
```python
# core/vm/virtualbox_controller.py
import asyncio
from typing import List, Optional, Dict, Any
from contextlib import asynccontextmanager
import pyvbox
from pyvbox import VirtualBoxManager
from pyvbox.library import VBoxErrorObjectNotFound, MachineState
import logging

logger = logging.getLogger(__name__)

class VirtualBoxController(VMController):
    """Modern VirtualBox controller using pyvbox SDK"""
    
    def __init__(self, vbox_path: Optional[str] = None, delay: int = 50):
        self.vbox_path = vbox_path
        self.delay = delay
        self.vbox_mgr: Optional[VirtualBoxManager] = None
        self.vbox = None
        self.sessions: Dict[str, Any] = {}
        
    async def initialize(self) -> None:
        """Initialize VirtualBox connection"""
        try:
            # pyvbox handles the complexity of finding VirtualBox
            self.vbox_mgr = VirtualBoxManager()
            self.vbox = self.vbox_mgr.vbox
            logger.info(f"Connected to VirtualBox {self.vbox.version}")
        except Exception as e:
            logger.error(f"Failed to connect to VirtualBox: {e}")
            # Fallback to CLI mode if SDK fails
            logger.info("Falling back to VBoxManage CLI")
            from .vbox_cli_adapter import VBoxCLIAdapter
            self.__class__ = VBoxCLIAdapter
            await self.initialize()
    
    async def list_vms(self) -> List[str]:
        """List all VMs"""
        return [vm.name for vm in self.vbox.machines]
    
    async def start(self, vm_name: str) -> None:
        """Start a VM"""
        try:
            vm = self.vbox.find_machine(vm_name)
            session = self._get_session(vm_name)
            
            # Check current state
            if vm.state == MachineState.running:
                logger.info(f"VM {vm_name} is already running")
                return
                
            # Start the VM
            progress = vm.launch_vm_process(session, 'headless', '')
            await self._wait_for_progress(progress)
            logger.info(f"Started VM {vm_name}")
            
        except VBoxErrorObjectNotFound:
            raise ValueError(f"VM {vm_name} not found")
    
    async def stop(self, vm_name: str, save_state: bool = True) -> None:
        """Stop a VM"""
        vm = self.vbox.find_machine(vm_name)
        session = self._get_session(vm_name)
        
        if vm.state != MachineState.running:
            logger.info(f"VM {vm_name} is not running")
            return
        
        vm.lock_machine(session, pyvbox.library.LockType.shared)
        
        try:
            if save_state:
                progress = session.machine.save_state()
            else:
                progress = session.console.power_down()
            await self._wait_for_progress(progress)
        finally:
            session.unlock_machine()
    
    async def send_keys(self, vm_name: str, keys: str) -> None:
        """Send keyboard input using pyvbox keyboard API"""
        vm = self.vbox.find_machine(vm_name)
        session = self._get_session(vm_name)
        
        if vm.state != MachineState.running:
            raise RuntimeError(f"VM {vm_name} is not running")
        
        vm.lock_machine(session, pyvbox.library.LockType.shared)
        
        try:
            keyboard = session.console.keyboard
            # Convert key string to scan codes
            scan_codes = self._convert_to_scan_codes(keys)
            keyboard.put_scancodes(scan_codes)
            await asyncio.sleep(self.delay / 1000)  # Convert ms to seconds
        finally:
            session.unlock_machine()
    
    async def type_text(self, vm_name: str, text: str) -> None:
        """Type text into VM"""
        vm = self.vbox.find_machine(vm_name)
        session = self._get_session(vm_name)
        
        vm.lock_machine(session, pyvbox.library.LockType.shared)
        
        try:
            keyboard = session.console.keyboard
            # pyvbox can handle text directly in newer versions
            for char in text:
                scan_codes = self._char_to_scan_codes(char)
                keyboard.put_scancodes(scan_codes)
                await asyncio.sleep(self.delay / 1000)
        finally:
            session.unlock_machine()
    
    async def snapshot(self, vm_name: str, snapshot_name: str) -> None:
        """Create a VM snapshot"""
        vm = self.vbox.find_machine(vm_name)
        session = self._get_session(vm_name)
        
        vm.lock_machine(session, pyvbox.library.LockType.shared)
        
        try:
            progress = session.machine.take_snapshot(
                snapshot_name,
                f"Snapshot created by TwitchBot",
                True  # Pause VM if running
            )
            await self._wait_for_progress(progress)
            logger.info(f"Created snapshot {snapshot_name} for {vm_name}")
        finally:
            session.unlock_machine()
    
    async def restore_snapshot(self, vm_name: str, snapshot_name: str) -> None:
        """Restore a VM snapshot"""
        vm = self.vbox.find_machine(vm_name)
        snapshot = vm.find_snapshot(snapshot_name)
        session = self._get_session(vm_name)
        
        vm.lock_machine(session, pyvbox.library.LockType.shared)
        
        try:
            progress = session.machine.restore_snapshot(snapshot)
            await self._wait_for_progress(progress)
            logger.info(f"Restored snapshot {snapshot_name} for {vm_name}")
        finally:
            session.unlock_machine()
    
    async def get_state(self, vm_name: str) -> VMState:
        """Get VM state"""
        vm = self.vbox.find_machine(vm_name)
        
        state_mapping = {
            MachineState.powered_off: VMState.STOPPED,
            MachineState.running: VMState.RUNNING,
            MachineState.paused: VMState.PAUSED,
            MachineState.saved: VMState.SAVED,
        }
        
        return state_mapping.get(vm.state, VMState.STOPPED)
    
    def _get_session(self, vm_name: str):
        """Get or create session for VM"""
        if vm_name not in self.sessions:
            self.sessions[vm_name] = self.vbox_mgr.get_session()
        return self.sessions[vm_name]
    
    async def _wait_for_progress(self, progress):
        """Wait for VirtualBox operation to complete"""
        while not progress.completed:
            await asyncio.sleep(0.1)
        
        if progress.result_code != 0:
            raise RuntimeError(f"Operation failed: {progress.error_info.text}")
    
    def _convert_to_scan_codes(self, keys: str) -> List[int]:
        """Convert key string to VirtualBox scan codes"""
        # Implementation depends on key mapping
        # This is a simplified version
        scan_code_map = {
            'ENTER': [0x1C, 0x9C],
            'ESC': [0x01, 0x81],
            'TAB': [0x0F, 0x8F],
            'SPACE': [0x39, 0xB9],
            # Add more mappings as needed
        }
        return scan_code_map.get(keys.upper(), [])
    
    def _char_to_scan_codes(self, char: str) -> List[int]:
        """Convert character to scan codes"""
        # Simplified - real implementation needs full mapping
        if char.isalpha():
            # Basic letter mapping
            base = 0x10 if char.lower() <= 'm' else 0x1E
            offset = ord(char.lower()) - ord('a')
            code = base + offset
            return [code, code | 0x80]
        elif char == ' ':
            return [0x39, 0xB9]
        # Add more character mappings
        return []
    
    async def cleanup(self) -> None:
        """Cleanup sessions"""
        for session in self.sessions.values():
            try:
                if session.state == pyvbox.library.SessionState.locked:
                    session.unlock_machine()
            except:
                pass
        self.sessions.clear()
```

### 1.3 KVM/QEMU Controller Implementation
```python
# core/vm/kvm_controller.py
import asyncio
import libvirt
import libvirt_qemu
from typing import List, Optional, Dict, Any
from xml.etree import ElementTree as ET
import logging

logger = logging.getLogger(__name__)

class KVMController(VMController):
    """KVM/QEMU controller using libvirt"""
    
    def __init__(self, uri: str = 'qemu:///system', delay: int = 50):
        self.uri = uri
        self.delay = delay
        self.conn: Optional[libvirt.virConnect] = None
        
    async def initialize(self) -> None:
        """Initialize libvirt connection"""
        try:
            self.conn = libvirt.open(self.uri)
            logger.info(f"Connected to libvirt at {self.uri}")
            logger.info(f"Hypervisor: {self.conn.getType()}")
        except libvirt.libvirtError as e:
            logger.error(f"Failed to connect to libvirt: {e}")
            raise
    
    async def list_vms(self) -> List[str]:
        """List all VMs (domains)"""
        domains = self.conn.listAllDomains()
        return [domain.name() for domain in domains]
    
    async def start(self, vm_name: str) -> None:
        """Start a VM"""
        try:
            domain = self.conn.lookupByName(vm_name)
            
            if domain.isActive():
                logger.info(f"VM {vm_name} is already running")
                return
            
            domain.create()
            logger.info(f"Started VM {vm_name}")
            
        except libvirt.libvirtError as e:
            raise ValueError(f"Failed to start VM {vm_name}: {e}")
    
    async def stop(self, vm_name: str, save_state: bool = True) -> None:
        """Stop a VM"""
        domain = self.conn.lookupByName(vm_name)
        
        if not domain.isActive():
            logger.info(f"VM {vm_name} is not running")
            return
        
        if save_state:
            # Save VM state to file
            save_file = f"/var/lib/libvirt/qemu/save/{vm_name}.save"
            domain.save(save_file)
            logger.info(f"Saved VM {vm_name} state to {save_file}")
        else:
            # Graceful shutdown
            domain.shutdown()
            # Wait for shutdown or force after timeout
            for _ in range(30):
                await asyncio.sleep(1)
                if not domain.isActive():
                    break
            else:
                domain.destroy()  # Force shutdown
            logger.info(f"Stopped VM {vm_name}")
    
    async def send_keys(self, vm_name: str, keys: str) -> None:
        """Send keyboard input using QEMU monitor"""
        domain = self.conn.lookupByName(vm_name)
        
        if not domain.isActive():
            raise RuntimeError(f"VM {vm_name} is not running")
        
        # Convert keys to QEMU sendkey format
        qemu_keys = self._convert_to_qemu_keys(keys)
        
        # Use QEMU monitor command
        command = f'{{"execute":"send-key","arguments":{{"keys":{qemu_keys}}}}}'
        result = libvirt_qemu.qemuMonitorCommand(
            domain, command, 
            libvirt_qemu.VIR_DOMAIN_QEMU_MONITOR_COMMAND_DEFAULT
        )
        
        await asyncio.sleep(self.delay / 1000)
    
    async def type_text(self, vm_name: str, text: str) -> None:
        """Type text into VM"""
        domain = self.conn.lookupByName(vm_name)
        
        if not domain.isActive():
            raise RuntimeError(f"VM {vm_name} is not running")
        
        for char in text:
            qemu_keys = self._char_to_qemu_keys(char)
            command = f'{{"execute":"send-key","arguments":{{"keys":{qemu_keys}}}}}'
            libvirt_qemu.qemuMonitorCommand(
                domain, command,
                libvirt_qemu.VIR_DOMAIN_QEMU_MONITOR_COMMAND_DEFAULT
            )
            await asyncio.sleep(self.delay / 1000)
    
    async def snapshot(self, vm_name: str, snapshot_name: str) -> None:
        """Create a VM snapshot"""
        domain = self.conn.lookupByName(vm_name)
        
        # Create snapshot XML
        snapshot_xml = f"""
        <domainsnapshot>
            <name>{snapshot_name}</name>
            <description>Created by TwitchBot</description>
        </domainsnapshot>
        """
        
        flags = 0
        if domain.isActive():
            # Include memory state for running VMs
            flags = libvirt.VIR_DOMAIN_SNAPSHOT_CREATE_ATOMIC
        
        domain.snapshotCreateXML(snapshot_xml, flags)
        logger.info(f"Created snapshot {snapshot_name} for {vm_name}")
    
    async def restore_snapshot(self, vm_name: str, snapshot_name: str) -> None:
        """Restore a VM snapshot"""
        domain = self.conn.lookupByName(vm_name)
        snapshot = domain.snapshotLookupByName(snapshot_name)
        
        domain.revertToSnapshot(snapshot)
        logger.info(f"Restored snapshot {snapshot_name} for {vm_name}")
    
    async def get_state(self, vm_name: str) -> VMState:
        """Get VM state"""
        domain = self.conn.lookupByName(vm_name)
        state, _ = domain.state()
        
        state_mapping = {
            libvirt.VIR_DOMAIN_SHUTDOWN: VMState.STOPPED,
            libvirt.VIR_DOMAIN_SHUTOFF: VMState.STOPPED,
            libvirt.VIR_DOMAIN_RUNNING: VMState.RUNNING,
            libvirt.VIR_DOMAIN_PAUSED: VMState.PAUSED,
            libvirt.VIR_DOMAIN_PMSUSPENDED: VMState.SAVED,
        }
        
        return state_mapping.get(state, VMState.STOPPED)
    
    def _convert_to_qemu_keys(self, keys: str) -> str:
        """Convert key names to QEMU format"""
        qemu_key_map = {
            'ENTER': 'ret',
            'ESC': 'esc',
            'TAB': 'tab',
            'SPACE': 'spc',
            'CTRL': 'ctrl',
            'ALT': 'alt',
            'SHIFT': 'shift',
            # Add more mappings
        }
        
        qemu_key = qemu_key_map.get(keys.upper(), keys.lower())
        return f'[{{"type":"qcode","data":"{qemu_key}"}}]'
    
    def _char_to_qemu_keys(self, char: str) -> str:
        """Convert character to QEMU key codes"""
        if char == ' ':
            return '[{"type":"qcode","data":"spc"}]'
        elif char.isalpha():
            return f'[{{"type":"qcode","data":"{char.lower()}"}}]'
        # Add more character mappings
        return f'[{{"type":"qcode","data":"{char}"}}]'
    
    async def cleanup(self) -> None:
        """Close libvirt connection"""
        if self.conn:
            self.conn.close()
            self.conn = None
```

### 1.4 Configuration System
```python
# core/settings.py (updated)
import os
from enum import Enum
from typing import Optional
from pydantic import BaseSettings, Field

class HypervisorConfig(BaseSettings):
    """Hypervisor configuration"""
    
    # Hypervisor selection
    HYPERVISOR_TYPE: str = Field(
        default="virtualbox",
        env="TWITCHBOT_HYPERVISOR",
        description="Hypervisor type: virtualbox or kvm"
    )
    
    # VirtualBox settings
    VBOX_SDK_PATH: Optional[str] = Field(
        default=None,
        env="VBOX_SDK_PATH",
        description="Path to VirtualBox SDK (optional)"
    )
    
    VBOX_FALLBACK_TO_CLI: bool = Field(
        default=True,
        env="VBOX_FALLBACK_TO_CLI",
        description="Fallback to VBoxManage CLI if SDK fails"
    )
    
    # KVM settings
    LIBVIRT_URI: str = Field(
        default="qemu:///system",
        env="LIBVIRT_URI",
        description="Libvirt connection URI"
    )
    
    # Common settings
    VM_KEY_DELAY: int = Field(
        default=50,
        env="VM_KEY_DELAY",
        description="Delay between key presses in milliseconds"
    )
    
    # VM selection
    VM_NAME_PREFIX: str = Field(
        default="ctf_",
        env="VM_NAME_PREFIX",
        description="Prefix for CTF challenge VMs"
    )
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

# Backward compatibility
MAX_FREEBIES = 10
PRESS_DELAY = 50
DEFAULT_OBJECTIVE = "Escalate privileges in order to gain full control of the system"
DEFAULT_PROFILE = 3
STATE_MIDDLEWARE = 'core.state.filestore.FileStore'
LOG_FILE = 'twitchbot.log'
LOGGING_LEVEL = logging.DEBUG

# New hypervisor config
hypervisor_config = HypervisorConfig()
```

## Phase 2: Dependencies & Environment (Week 3)

### 2.1 Modern pyproject.toml
```toml
[project]
name = "twitchbot"
version = "2.0.0"
description = "Twitch CTF Bot with VirtualBox and KVM support"
requires-python = ">=3.12"
dependencies = [
    # Core
    "twitchio>=3.1.0",
    "aiohttp>=3.10.0",
    "asyncio>=3.4.3",
    
    # Hypervisor Support
    "pyvbox>=2.0.0",           # VirtualBox SDK (better than vboxapi)
    "libvirt-python>=10.0.0",  # KVM/QEMU support
    
    # Storage & Config
    "pydantic>=2.9.0",
    "pydantic-settings>=2.6.0",
    "python-dotenv>=1.0.0",
    
    # Utilities
    "structlog>=24.0.0",
    "rich>=13.9.0",
    "httpx>=0.28.0",
    "asyncstdlib>=3.13.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.24.0",
    "pytest-mock>=3.14.0",
    "mypy>=1.13.0",
    "ruff>=0.8.0",
    "black>=24.0.0",
]

virtualbox = [
    "pyvbox>=2.0.0",
]

kvm = [
    "libvirt-python>=10.0.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.ruff]
target-version = "py312"
line-length = 100
select = ["E", "F", "W", "I", "N", "UP", "B", "A", "C4", "PT", "SIM", "PD"]

[tool.mypy]
python_version = "3.12"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
```

### 2.2 Docker Support for Both Hypervisors
```dockerfile
# Dockerfile
FROM python:3.12-slim AS base

# Install system dependencies for both hypervisors
RUN apt-get update && apt-get install -y \
    # Common
    curl \
    build-essential \
    # VirtualBox dependencies
    wget \
    ca-certificates \
    # KVM dependencies
    libvirt-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Install uv for fast dependency management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Copy dependency files
COPY pyproject.toml ./
COPY requirements.txt ./

# Install Python dependencies
RUN uv pip install --system -r requirements.txt

# Copy application code
COPY . .

# Runtime stage for VirtualBox
FROM base AS virtualbox-runtime

# Install VirtualBox (headless)
RUN echo "deb [arch=amd64 signed-by=/usr/share/keyrings/oracle-virtualbox-2016.gpg] https://download.virtualbox.org/virtualbox/debian bookworm contrib" > /etc/apt/sources.list.d/virtualbox.list \
    && wget -O- https://www.virtualbox.org/download/oracle_vbox_2016.asc | gpg --dearmor --yes --output /usr/share/keyrings/oracle-virtualbox-2016.gpg \
    && apt-get update \
    && apt-get install -y virtualbox-7.0 \
    && rm -rf /var/lib/apt/lists/*

ENV TWITCHBOT_HYPERVISOR=virtualbox

# Runtime stage for KVM
FROM base AS kvm-runtime

# Install KVM/QEMU runtime
RUN apt-get update && apt-get install -y \
    qemu-kvm \
    libvirt-daemon-system \
    libvirt-clients \
    && rm -rf /var/lib/apt/lists/*

ENV TWITCHBOT_HYPERVISOR=kvm

# Final stage (selectable at build time)
ARG HYPERVISOR=virtualbox
FROM ${HYPERVISOR}-runtime AS final

# Create non-root user
RUN useradd -m -s /bin/bash twitchbot \
    && usermod -aG libvirt,vboxusers twitchbot 2>/dev/null || true

USER twitchbot

ENTRYPOINT ["python", "-m", "twitchbot"]
```

### 2.3 Docker Compose for Development
```yaml
# docker-compose.yml
version: '3.9'

services:
  # VirtualBox variant
  twitchbot-vbox:
    build:
      context: .
      target: final
      args:
        HYPERVISOR: virtualbox
    image: twitchbot:vbox
    container_name: twitchbot-vbox
    environment:
      - TWITCHBOT_HYPERVISOR=virtualbox
      - TWITCH_CLIENT_ID=${TWITCH_CLIENT_ID}
      - TWITCH_CLIENT_SECRET=${TWITCH_CLIENT_SECRET}
    volumes:
      # VirtualBox VMs location
      - ${HOME}/VirtualBox VMs:/home/twitchbot/VirtualBox VMs
      - ./data:/app/data
      - ./logs:/app/logs
    devices:
      - /dev/vboxdrv:/dev/vboxdrv
    privileged: true
    networks:
      - twitchbot-net
    profiles:
      - virtualbox

  # KVM variant  
  twitchbot-kvm:
    build:
      context: .
      target: final
      args:
        HYPERVISOR: kvm
    image: twitchbot:kvm
    container_name: twitchbot-kvm
    environment:
      - TWITCHBOT_HYPERVISOR=kvm
      - LIBVIRT_URI=qemu:///system
      - TWITCH_CLIENT_ID=${TWITCH_CLIENT_ID}
      - TWITCH_CLIENT_SECRET=${TWITCH_CLIENT_SECRET}
    volumes:
      - /var/run/libvirt/libvirt-sock:/var/run/libvirt/libvirt-sock
      - /var/lib/libvirt:/var/lib/libvirt
      - ./data:/app/data
      - ./logs:/app/logs
    devices:
      - /dev/kvm:/dev/kvm
    privileged: true
    networks:
      - twitchbot-net
    profiles:
      - kvm

  # Development with both
  twitchbot-dev:
    build:
      context: .
      target: base
    image: twitchbot:dev
    container_name: twitchbot-dev
    environment:
      - TWITCHBOT_HYPERVISOR=${HYPERVISOR:-virtualbox}
      - TWITCH_CLIENT_ID=${TWITCH_CLIENT_ID}
      - TWITCH_CLIENT_SECRET=${TWITCH_CLIENT_SECRET}
    volumes:
      - .:/app
      - ${HOME}/VirtualBox VMs:/home/twitchbot/VirtualBox VMs
      - /var/run/libvirt/libvirt-sock:/var/run/libvirt/libvirt-sock
    command: ["python", "-m", "twitchbot", "--debug"]
    networks:
      - twitchbot-net
    profiles:
      - dev

networks:
  twitchbot-net:
    driver: bridge
```

## Phase 3: State Management Updates (Week 4)

### 3.1 Updated State Class
```python
# core/state/__init__.py (updated sections)
from core.vm.base import VMControllerFactory, HypervisorType
from core.settings import hypervisor_config

class State:
    def __init__(self):
        # ... existing code ...
        self.vm_controller = None
        self.hypervisor_type = None
        
        # Initialize VM controller based on config
        self.initialize_vm_controller()
    
    def initialize_vm_controller(self):
        """Initialize the appropriate VM controller"""
        hypervisor = HypervisorType(hypervisor_config.HYPERVISOR_TYPE.lower())
        
        controller_kwargs = {
            'delay': hypervisor_config.VM_KEY_DELAY
        }
        
        if hypervisor == HypervisorType.VIRTUALBOX:
            controller_kwargs['vbox_path'] = hypervisor_config.VBOX_SDK_PATH
        elif hypervisor == HypervisorType.KVM:
            controller_kwargs['uri'] = hypervisor_config.LIBVIRT_URI
        
        self.vm_controller = VMControllerFactory.create(
            hypervisor,
            **controller_kwargs
        )
        
        # Initialize asynchronously
        asyncio.create_task(self.vm_controller.initialize())
        self.hypervisor_type = hypervisor
        
        logger.info(f"Initialized {hypervisor.value} VM controller")
    
    # Update existing methods to use new controller
    def initialize_box(self):
        """Initialize VM for current challenge"""
        if not self.challenge:
            raise NoChallengeSelectedError
        
        # VM name format: prefix + challenge_name
        vm_name = f"{hypervisor_config.VM_NAME_PREFIX}{self.challenge.name}"
        
        # Check if VM exists
        async def check_vm():
            vms = await self.vm_controller.list_vms()
            if vm_name not in vms:
                raise BoxNotFoundError(f"VM {vm_name} not found in {self.hypervisor_type.value}")
            
            self.box = vm_name
            logger.info(f"Initialized VM {vm_name} on {self.hypervisor_type.value}")
        
        asyncio.create_task(check_vm())
    
    async def send_keys(self, keys):
        """Send keys to VM"""
        if not self.box:
            raise BoxNotInitializedError
        
        state = await self.vm_controller.get_state(self.box)
        if state != VMState.RUNNING:
            raise BoxNotRunningError
        
        await self.vm_controller.send_keys(self.box, keys)
    
    async def type_text(self, text):
        """Type text in VM"""
        if not self.box:
            raise BoxNotInitializedError
        
        state = await self.vm_controller.get_state(self.box)
        if state != VMState.RUNNING:
            raise BoxNotRunningError
        
        await self.vm_controller.type_text(self.box, text)
```

## Phase 4: Migration & Testing (Week 5-6)

### 4.1 Testing Suite
```python
# tests/test_vm_controllers.py
import pytest
from unittest.mock import AsyncMock, MagicMock
from core.vm.base import VMControllerFactory, HypervisorType, VMState
from core.vm.virtualbox_controller import VirtualBoxController
from core.vm.kvm_controller import KVMController

@pytest.fixture
def mock_vbox_manager():
    """Mock pyvbox VirtualBoxManager"""
    mock = MagicMock()
    mock.vbox.version = "7.0.0"
    mock.vbox.machines = []
    return mock

@pytest.fixture
def mock_libvirt_conn():
    """Mock libvirt connection"""
    mock = MagicMock()
    mock.getType.return_value = "QEMU"
    mock.listAllDomains.return_value = []
    return mock

@pytest.mark.asyncio
async def test_virtualbox_controller_initialization(mock_vbox_manager, monkeypatch):
    """Test VirtualBox controller initialization"""
    monkeypatch.setattr(
        "core.vm.virtualbox_controller.VirtualBoxManager",
        lambda: mock_vbox_manager
    )
    
    controller = VirtualBoxController()
    await controller.initialize()
    
    assert controller.vbox_mgr == mock_vbox_manager
    assert controller.vbox == mock_vbox_manager.vbox

@pytest.mark.asyncio
async def test_kvm_controller_initialization(mock_libvirt_conn, monkeypatch):
    """Test KVM controller initialization"""
    monkeypatch.setattr(
        "libvirt.open",
        lambda uri: mock_libvirt_conn
    )
    
    controller = KVMController()
    await controller.initialize()
    
    assert controller.conn == mock_libvirt_conn

@pytest.mark.asyncio
async def test_factory_creates_correct_controller():
    """Test factory creates correct controller type"""
    vbox_controller = VMControllerFactory.create(HypervisorType.VIRTUALBOX)
    assert isinstance(vbox_controller, VirtualBoxController)
    
    kvm_controller = VMControllerFactory.create(HypervisorType.KVM)
    assert isinstance(kvm_controller, KVMController)

@pytest.mark.asyncio
async def test_controller_interface_compatibility():
    """Test both controllers implement the same interface"""
    for hypervisor in [HypervisorType.VIRTUALBOX, HypervisorType.KVM]:
        controller = VMControllerFactory.create(hypervisor)
        
        # Check all required methods exist
        assert hasattr(controller, 'initialize')
        assert hasattr(controller, 'list_vms')
        assert hasattr(controller, 'start')
        assert hasattr(controller, 'stop')
        assert hasattr(controller, 'send_keys')
        assert hasattr(controller, 'type_text')
        assert hasattr(controller, 'snapshot')
        assert hasattr(controller, 'restore_snapshot')
        assert hasattr(controller, 'get_state')
        assert hasattr(controller, 'cleanup')
```

### 4.2 CLI for Testing
```python
# cli/vm_test.py
#!/usr/bin/env python3
"""
Test CLI for VM controllers
Usage: python -m cli.vm_test --hypervisor [virtualbox|kvm] --vm-name <name>
"""

import asyncio
import argparse
import logging
from rich.console import Console
from rich.table import Table
from core.vm.base import VMControllerFactory, HypervisorType

console = Console()

async def test_vm_controller(hypervisor: str, vm_name: str):
    """Test VM controller operations"""
    
    console.print(f"[bold blue]Testing {hypervisor} controller[/bold blue]")
    
    # Create controller
    hypervisor_type = HypervisorType(hypervisor.lower())
    controller = VMControllerFactory.create(hypervisor_type)
    
    try:
        # Initialize
        console.print("Initializing controller...")
        await controller.initialize()
        console.print("[green]✓[/green] Controller initialized")
        
        # List VMs
        console.print("\nListing VMs...")
        vms = await controller.list_vms()
        
        table = Table(title="Available VMs")
        table.add_column("VM Name", style="cyan")
        for vm in vms:
            table.add_row(vm)
        console.print(table)
        
        if vm_name and vm_name in vms:
            # Get VM state
            state = await controller.get_state(vm_name)
            console.print(f"\nVM '{vm_name}' state: [yellow]{state.value}[/yellow]")
            
            # Test operations
            console.print("\n[bold]Testing VM operations:[/bold]")
            
            # Start VM
            console.print(f"Starting VM '{vm_name}'...")
            await controller.start(vm_name)
            console.print("[green]✓[/green] VM started")
            
            await asyncio.sleep(5)
            
            # Send keys
            console.print("Sending test keys...")
            await controller.send_keys(vm_name, "TAB")
            await controller.send_keys(vm_name, "ENTER")
            console.print("[green]✓[/green] Keys sent")
            
            # Type text
            console.print("Typing test text...")
            await controller.type_text(vm_name, "Hello from TwitchBot!")
            console.print("[green]✓[/green] Text typed")
            
            # Create snapshot
            console.print("Creating test snapshot...")
            await controller.snapshot(vm_name, "test_snapshot")
            console.print("[green]✓[/green] Snapshot created")
            
            # Stop VM
            console.print("Stopping VM...")
            await controller.stop(vm_name, save_state=True)
            console.print("[green]✓[/green] VM stopped")
            
        console.print("\n[bold green]All tests passed![/bold green]")
        
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise
    
    finally:
        await controller.cleanup()

def main():
    parser = argparse.ArgumentParser(description="Test VM controllers")
    parser.add_argument(
        "--hypervisor",
        choices=["virtualbox", "kvm"],
        default="virtualbox",
        help="Hypervisor to test"
    )
    parser.add_argument(
        "--vm-name",
        help="VM name to test operations on"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging"
    )
    
    args = parser.parse_args()
    
    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    
    asyncio.run(test_vm_controller(args.hypervisor, args.vm_name))

if __name__ == "__main__":
    main()
```

## Phase 5: Documentation & Deployment (Week 7)

### 5.1 Environment Configuration (.env)
```bash
# .env.example
# Hypervisor Configuration
TWITCHBOT_HYPERVISOR=virtualbox  # or 'kvm'

# VirtualBox Configuration
VBOX_SDK_PATH=/usr/lib/virtualbox
VBOX_FALLBACK_TO_CLI=true

# KVM Configuration  
LIBVIRT_URI=qemu:///system

# VM Configuration
VM_KEY_DELAY=50
VM_NAME_PREFIX=ctf_

# Twitch Configuration
TWITCH_CLIENT_ID=your_client_id
TWITCH_CLIENT_SECRET=your_client_secret

# Logging
LOG_LEVEL=INFO
LOG_FILE=twitchbot.log
```

### 5.2 Deployment Scripts
```bash
#!/bin/bash
# deploy.sh - Deployment script with hypervisor selection

set -e

HYPERVISOR=${1:-virtualbox}

echo "Deploying TwitchBot with $HYPERVISOR support..."

# Check hypervisor availability
if [ "$HYPERVISOR" = "virtualbox" ]; then
    if ! command -v VBoxManage &> /dev/null; then
        echo "Error: VirtualBox not found"
        exit 1
    fi
    echo "VirtualBox version: $(VBoxManage --version)"
elif [ "$HYPERVISOR" = "kvm" ]; then
    if ! command -v virsh &> /dev/null; then
        echo "Error: libvirt not found"
        exit 1
    fi
    echo "libvirt version: $(virsh --version)"
else
    echo "Error: Unknown hypervisor $HYPERVISOR"
    exit 1
fi

# Install Python dependencies
echo "Installing Python dependencies..."
uv pip install -e ".[${HYPERVISOR}]"

# Run tests
echo "Running tests..."
pytest tests/test_vm_controllers.py -v

# Build Docker image
echo "Building Docker image..."
docker compose --profile $HYPERVISOR build

# Start services
echo "Starting services..."
docker compose --profile $HYPERVISOR up -d

echo "Deployment complete!"
echo "Check logs: docker compose logs -f twitchbot-$HYPERVISOR"
```

## Migration Timeline

### Week 1-2: Hypervisor Abstraction
- [x] Design abstract VM interface
- [x] Implement VirtualBox controller with pyvbox
- [x] Implement KVM controller with libvirt
- [x] Create factory pattern for controller selection

### Week 3: Dependencies & Environment
- [ ] Set up pyproject.toml with both hypervisor deps
- [ ] Create Docker images for both configurations
- [ ] Set up docker-compose with profiles

### Week 4: State Management
- [ ] Update State class to use new controllers
- [ ] Migrate existing VM operations
- [ ] Add async support throughout

### Week 5-6: Testing & Validation
- [ ] Unit tests for both controllers
- [ ] Integration tests with real VMs
- [ ] Performance benchmarking
- [ ] Migration testing

### Week 7: Documentation & Deployment
- [ ] Update documentation
- [ ] Create deployment scripts
- [ ] Production deployment

## Benefits of This Approach

### 1. **Backward Compatibility**
- Existing VirtualBox VMs continue to work
- No forced migration required
- Gradual transition possible

### 2. **Performance Options**
- Use VirtualBox for Windows/complex VMs
- Use KVM for Linux/performance-critical VMs
- Runtime selection based on needs

### 3. **Better SDK Support**
- pyvbox is more reliable than vboxapi
- Fallback to CLI if SDK fails
- libvirt is production-grade for KVM

### 4. **Deployment Flexibility**
- Single codebase for both hypervisors
- Docker images for each configuration
- Easy switching via environment variables

### 5. **Future-Proof**
- Abstract interface allows adding more hypervisors
- Easy to add VMware, Hyper-V, etc.
- Modern Python 3.12+ patterns

## Testing Strategy

### Local Development
```bash
# Test with VirtualBox
export TWITCHBOT_HYPERVISOR=virtualbox
python -m cli.vm_test --vm-name test_vm

# Test with KVM
export TWITCHBOT_HYPERVISOR=kvm
python -m cli.vm_test --vm-name test_vm
```

### CI/CD Pipeline
```yaml
# .github/workflows/test.yml
name: Test VM Controllers

on: [push, pull_request]

jobs:
  test-virtualbox:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Install VirtualBox
        run: |
          sudo apt-get update
          sudo apt-get install -y virtualbox
      - name: Test VirtualBox Controller
        run: |
          uv pip install -e ".[virtualbox,dev]"
          pytest tests/test_vm_controllers.py::test_virtualbox
          
  test-kvm:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Install KVM
        run: |
          sudo apt-get update
          sudo apt-get install -y qemu-kvm libvirt-daemon-system
      - name: Test KVM Controller
        run: |
          uv pip install -e ".[kvm,dev]"
          pytest tests/test_vm_controllers.py::test_kvm
```

## Conclusion

This dual-hypervisor approach provides:
- **Immediate improvement** via better VirtualBox SDK (pyvbox)
- **Future performance** via optional KVM support
- **Zero downtime** migration path
- **Production flexibility** to use the best tool for each VM
- **Modern architecture** with async support and clean abstractions

The abstraction layer ensures that the rest of the codebase doesn't need to know which hypervisor is being used, making it easy to add support for additional hypervisors in the future.