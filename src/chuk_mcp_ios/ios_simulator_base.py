#!/usr/bin/env python3
# chuk_mcp_ios/ios_simulator_base.py
"""
iOS Simulator Base Classes and Data Models
Contains core data structures and base functionality for iOS simulator control.
"""

import subprocess
import json
from typing import List, Dict, Optional, Union
from dataclasses import dataclass
from datetime import datetime
from abc import ABC, abstractmethod

# Data Models
@dataclass
class SimulatorInfo:
    udid: str
    name: str
    state: str
    os: str
    device_type: str

@dataclass
class AppInfo:
    bundle_id: str
    name: str
    installed_path: str

@dataclass
class CrashLogInfo:
    name: str
    bundle_id: Optional[str]
    date: datetime
    path: str

@dataclass
class SessionConfig:
    device_name: Optional[str] = None
    platform_version: Optional[str] = None
    autoboot: bool = True

@dataclass
class DebugServerStatus:
    running: bool
    port: Optional[int] = None
    bundle_id: Optional[str] = None

# Base Command Executor
class CommandExecutor:
    """Base class for executing shell commands with error handling."""
    
    def __init__(self):
        self.simctl_path = "xcrun simctl"
        self.idb_path = "idb"
    
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
    
    def verify_idb_availability(self) -> None:
        """Verify that idb is available."""
        try:
            self.run_command(f"{self.idb_path} --version")
        except subprocess.CalledProcessError:
            raise Exception("idb is not installed or not available in PATH. Make sure idb-companion and fb-idb are properly installed.")

# Session Manager Interface
class SessionManagerInterface(ABC):
    """Interface for session management operations."""
    
    @abstractmethod
    def create_session(self, config: Optional[SessionConfig] = None) -> str:
        pass
    
    @abstractmethod
    def terminate_session(self, session_id: str) -> None:
        pass
    
    @abstractmethod
    def list_sessions(self) -> List[str]:
        pass
    
    @abstractmethod
    def get_udid_from_session(self, session_id: str) -> str:
        pass

# Simulator Manager Interface
class SimulatorManagerInterface(ABC):
    """Interface for simulator management operations."""
    
    @abstractmethod
    def list_available_simulators(self) -> List[SimulatorInfo]:
        pass
    
    @abstractmethod
    def list_booted_simulators(self) -> List[SimulatorInfo]:
        pass
    
    @abstractmethod
    def boot_simulator_by_udid(self, udid: str, timeout: int = 30) -> None:
        pass
    
    @abstractmethod
    def shutdown_simulator_by_udid(self, udid: str) -> None:
        pass
    
    @abstractmethod
    def is_simulator_booted(self, udid: str) -> bool:
        pass

# App Manager Interface
class AppManagerInterface(ABC):
    """Interface for app management operations."""
    
    @abstractmethod
    def install_app(self, udid: str, app_path: str) -> AppInfo:
        pass
    
    @abstractmethod
    def uninstall_app(self, udid: str, bundle_id: str) -> None:
        pass
    
    @abstractmethod
    def launch_app(self, udid: str, bundle_id: str) -> None:
        pass
    
    @abstractmethod
    def terminate_app(self, udid: str, bundle_id: str) -> None:
        pass
    
    @abstractmethod
    def list_apps(self, udid: str) -> List[AppInfo]:
        pass
    
    @abstractmethod
    def is_app_installed(self, udid: str, bundle_id: str) -> bool:
        pass

# UI Controller Interface
class UIControllerInterface(ABC):
    """Interface for UI interaction operations."""
    
    @abstractmethod
    def tap(self, udid: str, x: int, y: int) -> None:
        pass
    
    @abstractmethod
    def swipe(self, udid: str, start_x: int, start_y: int, end_x: int, end_y: int, duration: int = 100) -> None:
        pass
    
    @abstractmethod
    def input_text(self, udid: str, text: str) -> None:
        pass
    
    @abstractmethod
    def press_button(self, udid: str, button: str, duration: Optional[int] = None) -> None:
        pass
    
    @abstractmethod
    def press_key(self, udid: str, key_code: int, duration: Optional[int] = None) -> None:
        pass
    
    @abstractmethod
    def take_screenshot(self, udid: str, output_path: Optional[str] = None) -> Union[bytes, str]:
        pass

# Media Manager Interface
class MediaManagerInterface(ABC):
    """Interface for media and location operations."""
    
    @abstractmethod
    def add_media(self, udid: str, media_paths: List[str]) -> None:
        pass
    
    @abstractmethod
    def set_location(self, udid: str, latitude: float, longitude: float) -> None:
        pass

# Logger Interface
class LoggerInterface(ABC):
    """Interface for logging and crash report operations."""
    
    @abstractmethod
    def get_system_logs(self, udid: str, bundle: Optional[str] = None, 
                       since: Optional[datetime] = None, limit: Optional[int] = None) -> str:
        pass
    
    @abstractmethod
    def list_crash_logs(self, udid: str, bundle_id: Optional[str] = None,
                       before: Optional[datetime] = None, since: Optional[datetime] = None) -> List[CrashLogInfo]:
        pass
    
    @abstractmethod
    def get_crash_log(self, udid: str, crash_name: str) -> str:
        pass
    
    @abstractmethod
    def delete_crash_logs(self, udid: str, crash_names: Optional[List[str]] = None,
                         bundle_id: Optional[str] = None, before: Optional[datetime] = None,
                         since: Optional[datetime] = None, all_crashes: bool = False) -> None:
        pass

# Utilities Interface
class UtilitiesInterface(ABC):
    """Interface for utility operations."""
    
    @abstractmethod
    def open_url(self, udid: str, url: str) -> None:
        pass
    
    @abstractmethod
    def clear_keychain(self, udid: str) -> None:
        pass
    
    @abstractmethod
    def install_dylib(self, udid: str, dylib_path: str) -> None:
        pass
    
    @abstractmethod
    def approve_permissions(self, udid: str, bundle_id: str, permissions: List[str]) -> None:
        pass
    
    @abstractmethod
    def update_contacts(self, udid: str, db_path: str) -> None:
        pass
    
    @abstractmethod
    def get_debug_server_status(self, udid: str) -> DebugServerStatus:
        pass
    
    @abstractmethod
    def focus_simulator(self, udid: str) -> None:
        pass

# Exception Classes
class SimulatorError(Exception):
    """Base exception for simulator-related errors."""
    pass

class SessionNotFoundError(SimulatorError):
    """Raised when a session ID is not found."""
    pass

class SimulatorNotBootedError(SimulatorError):
    """Raised when trying to perform operations on a non-booted simulator."""
    pass

class AppNotFoundError(SimulatorError):
    """Raised when an app is not found or not installed."""
    pass

class IDBNotAvailableError(SimulatorError):
    """Raised when idb tools are not available."""
    pass