#!/usr/bin/env python3
# chuk_mcp_ios/core/base.py
"""
Core base classes and interfaces for iOS device control.
Device-agnostic abstractions that work for both simulators and real devices.
"""

import subprocess
from typing import List, Dict, Optional, Union, Tuple
from dataclasses import dataclass
from datetime import datetime
from abc import ABC, abstractmethod
from enum import Enum

# Device Types
class DeviceType(Enum):
    SIMULATOR = "simulator"
    REAL_DEVICE = "real_device"

# Device States
class DeviceState(Enum):
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    BOOTED = "booted"
    SHUTDOWN = "shutdown"
    UNKNOWN = "unknown"

# Data Models
@dataclass
class DeviceInfo:
    """Unified device information."""
    udid: str
    name: str
    state: DeviceState
    device_type: DeviceType
    os_version: str
    model: str
    connection_type: str  # usb, wifi, simulator
    architecture: Optional[str] = None
    is_available: bool = True

@dataclass
class AppInfo:
    """Application information."""
    bundle_id: str
    name: str
    version: Optional[str] = None
    installed_path: Optional[str] = None

@dataclass
class SessionInfo:
    """Session information."""
    session_id: str
    device_udid: str
    device_type: DeviceType
    created_at: datetime
    metadata: Dict = None

# Base Executor
class CommandExecutor:
    """Base class for executing shell commands with error handling."""
    
    def __init__(self):
        self.simctl_path = "xcrun simctl"
        self.idb_path = "idb"
        self.devicectl_path = "xcrun devicectl"
    
    def run_command(self, command: str, timeout: Optional[int] = None) -> subprocess.CompletedProcess:
        """Execute a shell command and return the result."""
        try:
            result = subprocess.run(
                command, 
                shell=True, 
                capture_output=True, 
                text=True, 
                check=True,
                timeout=timeout
            )
            return result
        except subprocess.CalledProcessError as e:
            print(f"Error executing command: {command}")
            print(f"Error: {e.stderr}")
            raise e
        except subprocess.TimeoutExpired as e:
            print(f"Command timed out: {command}")
            raise e

# Abstract Interfaces
class DeviceControllerInterface(ABC):
    """Interface for device control operations."""
    
    @abstractmethod
    def boot_device(self, udid: str, timeout: int = 30) -> None:
        """Boot/connect to a device."""
        pass
    
    @abstractmethod
    def shutdown_device(self, udid: str) -> None:
        """Shutdown/disconnect a device."""
        pass
    
    @abstractmethod
    def is_device_available(self, udid: str) -> bool:
        """Check if device is available."""
        pass
    
    @abstractmethod
    def get_device_info(self, udid: str) -> Optional[DeviceInfo]:
        """Get device information."""
        pass

class AppManagerInterface(ABC):
    """Interface for app management operations."""
    
    @abstractmethod
    def install_app(self, udid: str, app_path: str) -> AppInfo:
        """Install an app on the device."""
        pass
    
    @abstractmethod
    def uninstall_app(self, udid: str, bundle_id: str) -> None:
        """Uninstall an app from the device."""
        pass
    
    @abstractmethod
    def launch_app(self, udid: str, bundle_id: str, arguments: Optional[List[str]] = None) -> None:
        """Launch an app on the device."""
        pass
    
    @abstractmethod
    def terminate_app(self, udid: str, bundle_id: str) -> None:
        """Terminate a running app."""
        pass
    
    @abstractmethod
    def list_apps(self, udid: str, user_apps_only: bool = True) -> List[AppInfo]:
        """List installed apps."""
        pass

class UIControllerInterface(ABC):
    """Interface for UI automation operations."""
    
    @abstractmethod
    def tap(self, udid: str, x: int, y: int) -> None:
        """Tap at coordinates."""
        pass
    
    @abstractmethod
    def swipe(self, udid: str, start_x: int, start_y: int, end_x: int, end_y: int, duration: int = 100) -> None:
        """Perform swipe gesture."""
        pass
    
    @abstractmethod
    def input_text(self, udid: str, text: str) -> None:
        """Input text."""
        pass
    
    @abstractmethod
    def press_button(self, udid: str, button: str) -> None:
        """Press hardware button."""
        pass
    
    @abstractmethod
    def take_screenshot(self, udid: str, output_path: Optional[str] = None) -> Union[bytes, str]:
        """Take screenshot."""
        pass

class MediaManagerInterface(ABC):
    """Interface for media and location operations."""
    
    @abstractmethod
    def add_media(self, udid: str, media_paths: List[str]) -> None:
        """Add media files to device."""
        pass
    
    @abstractmethod
    def set_location(self, udid: str, latitude: float, longitude: float) -> None:
        """Set device location."""
        pass

# Exception Classes
class DeviceError(Exception):
    """Base exception for device-related errors."""
    pass

class DeviceNotFoundError(DeviceError):
    """Device not found."""
    pass

class DeviceNotAvailableError(DeviceError):
    """Device not available or not booted/connected."""
    pass

class AppNotFoundError(DeviceError):
    """App not found or not installed."""
    pass

class SessionError(DeviceError):
    """Session-related error."""
    pass

# Utility Functions
def detect_available_tools() -> Dict[str, bool]:
    """Detect which tools are available on the system."""
    tools = {
        'simctl': False,
        'idb': False,
        'devicectl': False,
        'instruments': False
    }
    
    executor = CommandExecutor()
    
    # Check simctl
    try:
        executor.run_command("xcrun simctl help", timeout=5)
        tools['simctl'] = True
    except:
        pass
    
    # Check idb
    try:
        executor.run_command("idb --version", timeout=5)
        tools['idb'] = True
    except:
        pass
    
    # Check devicectl
    try:
        executor.run_command("xcrun devicectl --version", timeout=5)
        tools['devicectl'] = True
    except:
        pass
    
    # Check instruments
    try:
        executor.run_command("instruments -v", timeout=5)
        tools['instruments'] = True
    except:
        pass
    
    return tools

def get_ios_version_from_runtime(runtime_name: str) -> str:
    """Extract iOS version from runtime name."""
    # Convert "com.apple.CoreSimulator.SimRuntime.iOS-16-0" to "iOS 16.0"
    import re
    match = re.search(r'iOS-(\d+)-(\d+)', runtime_name)
    if match:
        return f"iOS {match.group(1)}.{match.group(2)}"
    return runtime_name

def validate_bundle_id(bundle_id: str) -> bool:
    """Validate bundle ID format."""
    import re
    pattern = r'^[a-zA-Z][a-zA-Z0-9]*(\.[a-zA-Z][a-zA-Z0-9]*)+$'
    return bool(re.match(pattern, bundle_id))

def format_device_info(device: DeviceInfo) -> str:
    """Format device info for display."""
    state_emoji = {
        DeviceState.CONNECTED: "🟢",
        DeviceState.BOOTED: "🟢",
        DeviceState.DISCONNECTED: "🔴",
        DeviceState.SHUTDOWN: "⚪",
        DeviceState.UNKNOWN: "❓"
    }
    
    type_emoji = "📱" if device.device_type == DeviceType.REAL_DEVICE else "🖥️"
    
    return f"{type_emoji} {state_emoji.get(device.state, '❓')} {device.name} ({device.os_version})"