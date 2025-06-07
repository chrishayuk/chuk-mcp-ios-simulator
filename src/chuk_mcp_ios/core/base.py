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
    
    def run_command(self, command: str, timeout: Optional[int] = None, 
                   show_errors: bool = True) -> subprocess.CompletedProcess:
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
            if show_errors:
                print(f"Error executing command: {command}")
                print(f"Error: {e.stderr}")
            raise e
        except subprocess.TimeoutExpired as e:
            if show_errors:
                print(f"Command timed out: {command}")
            raise e
        except FileNotFoundError as e:
            if show_errors:
                print(f"Command not found: {command}")
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
    
    # Check simctl (most important)
    try:
        result = subprocess.run(
            ["xcrun", "simctl", "help"], 
            capture_output=True, 
            text=True, 
            timeout=5,
            check=True
        )
        tools['simctl'] = True
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
        pass
    
    # Check idb (optional)
    try:
        result = subprocess.run(
            ["idb", "list-targets"], 
            capture_output=True, 
            text=True, 
            timeout=5,
            check=True
        )
        tools['idb'] = True
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
        pass
    
    # Check devicectl (Xcode 15+) - Use simpler command that doesn't cause errors
    try:
        result = subprocess.run(
            ["xcrun", "devicectl", "list", "devices"], 
            capture_output=True, 
            text=True, 
            timeout=5,
            check=True
        )
        tools['devicectl'] = True
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
        pass
    
    # Check instruments (legacy)
    try:
        result = subprocess.run(
            ["instruments", "-v"], 
            capture_output=True, 
            text=True, 
            timeout=5,
            check=True
        )
        tools['instruments'] = True
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
        pass
    
    return tools

def check_ios_development_setup() -> Dict[str, any]:
    """Check the overall iOS development setup."""
    setup_info = {
        'xcode_installed': False,
        'command_line_tools': False,
        'simulators_available': False,
        'simulator_app_found': False,
        'available_tools': {},
        'simulator_count': 0,
        'recommendations': []
    }
    
    # Check Xcode Command Line Tools
    try:
        result = subprocess.run(
            ["xcode-select", "-p"], 
            capture_output=True, 
            text=True, 
            timeout=5,
            check=True
        )
        setup_info['command_line_tools'] = True
        
        # Check if full Xcode is installed
        xcode_path = result.stdout.strip()
        if '/Applications/Xcode.app' in xcode_path:
            setup_info['xcode_installed'] = True
    except:
        setup_info['recommendations'].append(
            "Install Xcode Command Line Tools: xcode-select --install"
        )
    
    # Check Simulator app
    import os
    sim_paths = [
        "/Applications/Xcode.app/Contents/Developer/Applications/Simulator.app",
        "/System/Applications/Simulator.app"
    ]
    
    for path in sim_paths:
        if os.path.exists(path):
            setup_info['simulator_app_found'] = True
            break
    
    # Detect available tools
    setup_info['available_tools'] = detect_available_tools()
    
    # Check if simulators are available
    if setup_info['available_tools']['simctl']:
        try:
            result = subprocess.run(
                ["xcrun", "simctl", "list", "devices", "-j"],
                capture_output=True,
                text=True,
                timeout=10,
                check=True
            )
            import json
            data = json.loads(result.stdout)
            
            # Count available iOS simulators
            simulator_count = 0
            for runtime, devices in data['devices'].items():
                if 'iOS' in runtime:
                    for device in devices:
                        if device.get('isAvailable', True):
                            simulator_count += 1
            
            setup_info['simulators_available'] = simulator_count > 0
            setup_info['simulator_count'] = simulator_count
            
        except:
            pass
    
    # Generate recommendations
    if not setup_info['command_line_tools']:
        setup_info['recommendations'].append(
            "Install Xcode Command Line Tools: xcode-select --install"
        )
    
    if not setup_info['xcode_installed']:
        setup_info['recommendations'].append(
            "Install full Xcode from App Store for best simulator support"
        )
    
    if not setup_info['simulators_available']:
        setup_info['recommendations'].append(
            "Download iOS Simulator runtimes in Xcode > Settings > Platforms"
        )
    
    if not setup_info['available_tools']['idb']:
        setup_info['recommendations'].append(
            "Optional: Install idb for real device support: brew install idb-companion"
        )
    
    return setup_info

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