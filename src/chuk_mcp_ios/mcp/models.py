#!/usr/bin/env python3
# src/chuk_mcp_ios/mcp/models.py
"""
Pydantic models for iOS Device Control MCP server - comprehensive iOS automation.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

# ═══════════════════════════════════════════════════════════════════════════
# SESSION MANAGEMENT
# ═══════════════════════════════════════════════════════════════════════════

class CreateSessionInput(BaseModel):
    """Create iOS device session."""
    device_name: Optional[str] = Field(None, description="Device name (e.g., 'iPhone 15')")
    device_udid: Optional[str] = Field(None, description="Specific device UDID")
    device_type: Optional[str] = Field(None, description="Device type: 'simulator' or 'real_device'")
    platform_version: Optional[str] = Field(None, description="iOS version (e.g., '17.2')")
    autoboot: bool = Field(True, description="Auto-boot simulator/connect device")
    session_name: Optional[str] = Field(None, description="Custom session name")

class CreateSessionResult(BaseModel):
    """Session creation result."""
    session_id: str = Field(..., description="Created session ID")
    device_name: str = Field(..., description="Device name")
    udid: str = Field(..., description="Device UDID")
    device_type: str = Field(..., description="Device type")
    platform_version: str = Field(..., description="iOS version")
    state: str = Field(..., description="Device state")

class SessionInfoResult(BaseModel):
    """Session information."""
    session_id: str = Field(..., description="Session ID")
    device_name: str = Field(..., description="Device name")
    udid: str = Field(..., description="Device UDID") 
    device_type: str = Field(..., description="Device type")
    state: str = Field(..., description="Device state")
    platform_version: str = Field(..., description="iOS version")
    created_at: str = Field(..., description="Creation timestamp")
    is_available: bool = Field(..., description="Device availability")

class ListSessionsResult(BaseModel):
    """List sessions result."""
    sessions: List[SessionInfoResult] = Field(..., description="Active sessions")
    total_count: int = Field(..., description="Total session count")

# ═══════════════════════════════════════════════════════════════════════════
# DEVICE MANAGEMENT
# ═══════════════════════════════════════════════════════════════════════════

class DeviceInfo(BaseModel):
    """Device information."""
    udid: str = Field(..., description="Device UDID")
    name: str = Field(..., description="Device name")
    state: str = Field(..., description="Device state (booted/shutdown/connected/disconnected)")
    device_type: str = Field(..., description="Device type (simulator/real_device)")
    os_version: str = Field(..., description="iOS version")
    model: str = Field(..., description="Device model")
    connection_type: str = Field(..., description="Connection type (simulator/usb/wifi)")
    is_available: bool = Field(..., description="Availability status")

class ListDevicesResult(BaseModel):
    """Available devices result."""
    devices: List[DeviceInfo] = Field(..., description="Available devices")
    total_count: int = Field(..., description="Total device count")
    simulators: int = Field(..., description="Simulator count")
    real_devices: int = Field(..., description="Real device count")
    available_count: int = Field(..., description="Available device count")

class BootDeviceInput(BaseModel):
    """Boot device input."""
    udid: str = Field(..., description="Device UDID")
    timeout: int = Field(60, description="Boot timeout in seconds")

class DeviceOperationResult(BaseModel):
    """Device operation result."""
    success: bool = Field(..., description="Operation success")
    message: str = Field(..., description="Result message")
    device_info: Optional[DeviceInfo] = Field(None, description="Updated device info")

# ═══════════════════════════════════════════════════════════════════════════
# APP MANAGEMENT
# ═══════════════════════════════════════════════════════════════════════════

class InstallAppInput(BaseModel):
    """Install app input."""
    session_id: str = Field(..., description="Session ID")
    app_path: str = Field(..., description="Path to .app bundle or .ipa file")
    force_reinstall: bool = Field(False, description="Uninstall before installing")
    launch_after_install: bool = Field(False, description="Launch app after installation")

class LaunchAppInput(BaseModel):
    """Launch app input."""
    session_id: str = Field(..., description="Session ID")
    bundle_id: str = Field(..., description="App bundle ID")
    arguments: Optional[List[str]] = Field(None, description="Launch arguments")

class TerminateAppInput(BaseModel):
    """Terminate app input."""
    session_id: str = Field(..., description="Session ID")
    bundle_id: str = Field(..., description="App bundle ID")

class UninstallAppInput(BaseModel):
    """Uninstall app input."""
    session_id: str = Field(..., description="Session ID")
    bundle_id: str = Field(..., description="App bundle ID")

class AppInfo(BaseModel):
    """App information."""
    bundle_id: str = Field(..., description="Bundle ID")
    name: str = Field(..., description="App name")
    version: Optional[str] = Field(None, description="App version")
    installed_path: Optional[str] = Field(None, description="Install path")

class ListAppsInput(BaseModel):
    """List apps input."""
    session_id: str = Field(..., description="Session ID")
    user_apps_only: bool = Field(True, description="Exclude system apps")

class ListAppsResult(BaseModel):
    """List apps result."""
    apps: List[AppInfo] = Field(..., description="Installed apps")
    total_count: int = Field(..., description="Total app count")
    user_app_count: int = Field(..., description="User app count")

class AppOperationResult(BaseModel):
    """App operation result."""
    success: bool = Field(..., description="Operation success")
    message: str = Field(..., description="Result message")
    app_info: Optional[AppInfo] = Field(None, description="App information")

# ═══════════════════════════════════════════════════════════════════════════
# UI INTERACTIONS
# ═══════════════════════════════════════════════════════════════════════════

class TapInput(BaseModel):
    """Tap gesture input."""
    session_id: str = Field(..., description="Session ID")
    x: int = Field(..., description="X coordinate")
    y: int = Field(..., description="Y coordinate")

class DoubleTapInput(BaseModel):
    """Double tap input."""
    session_id: str = Field(..., description="Session ID")
    x: int = Field(..., description="X coordinate")
    y: int = Field(..., description="Y coordinate")

class LongPressInput(BaseModel):
    """Long press input."""
    session_id: str = Field(..., description="Session ID")
    x: int = Field(..., description="X coordinate")
    y: int = Field(..., description="Y coordinate")
    duration: float = Field(1.0, description="Press duration in seconds")

class SwipeInput(BaseModel):
    """Swipe gesture input."""
    session_id: str = Field(..., description="Session ID")
    start_x: int = Field(..., description="Start X")
    start_y: int = Field(..., description="Start Y")
    end_x: int = Field(..., description="End X")
    end_y: int = Field(..., description="End Y")
    duration: int = Field(300, description="Duration in milliseconds")

class SwipeDirectionInput(BaseModel):
    """Swipe by direction input."""
    session_id: str = Field(..., description="Session ID")
    direction: str = Field(..., description="Direction: up, down, left, right")
    distance: Optional[int] = Field(None, description="Swipe distance (pixels)")
    duration: int = Field(300, description="Duration in milliseconds")

class InputTextInput(BaseModel):
    """Text input."""
    session_id: str = Field(..., description="Session ID")
    text: str = Field(..., description="Text to input")

class PressButtonInput(BaseModel):
    """Button press input."""
    session_id: str = Field(..., description="Session ID")
    button: str = Field(..., description="Button: home, lock, volume_up, volume_down, siri")

class ScreenshotInput(BaseModel):
    """Screenshot input."""
    session_id: str = Field(..., description="Session ID")
    output_path: Optional[str] = Field(None, description="Output path (auto-generated if not provided)")

class ScreenshotResult(BaseModel):
    """Screenshot result."""
    success: bool = Field(..., description="Success status")
    file_path: str = Field(..., description="Screenshot file path")
    file_size: int = Field(..., description="File size in bytes")
    timestamp: str = Field(..., description="Capture timestamp")

class RecordVideoInput(BaseModel):
    """Record video input."""
    session_id: str = Field(..., description="Session ID")
    output_path: str = Field(..., description="Output video path")
    duration: int = Field(10, description="Recording duration in seconds")
    quality: Optional[str] = Field(None, description="Video quality: low, medium, high")

class ScreenInfo(BaseModel):
    """Screen information."""
    width: int = Field(..., description="Screen width")
    height: int = Field(..., description="Screen height")
    scale: float = Field(..., description="Screen scale factor")
    orientation: str = Field(..., description="Current orientation")

# ═══════════════════════════════════════════════════════════════════════════
# LOCATION AND MEDIA
# ═══════════════════════════════════════════════════════════════════════════

class SetLocationInput(BaseModel):
    """Set location input."""
    session_id: str = Field(..., description="Session ID")
    latitude: float = Field(..., description="Latitude (-90 to 90)")
    longitude: float = Field(..., description="Longitude (-180 to 180)")
    altitude: Optional[float] = Field(None, description="Altitude in meters")

class SetLocationByNameInput(BaseModel):
    """Set location by name input."""
    session_id: str = Field(..., description="Session ID")
    location_name: str = Field(..., description="Location name (e.g., 'San Francisco', 'Tokyo')")

class AddMediaInput(BaseModel):
    """Add media input."""
    session_id: str = Field(..., description="Session ID")
    media_paths: List[str] = Field(..., description="Paths to media files")

class MediaOperationResult(BaseModel):
    """Media operation result."""
    success: bool = Field(..., description="Success status")
    files_processed: int = Field(..., description="Number of files processed")
    files_failed: int = Field(..., description="Number of files failed")
    message: str = Field(..., description="Result message")

# ═══════════════════════════════════════════════════════════════════════════
# UTILITIES
# ═══════════════════════════════════════════════════════════════════════════

class OpenUrlInput(BaseModel):
    """Open URL input."""
    session_id: str = Field(..., description="Session ID")
    url: str = Field(..., description="URL to open")

class GetLogsInput(BaseModel):
    """Get logs input."""
    session_id: str = Field(..., description="Session ID")
    bundle_id: Optional[str] = Field(None, description="App bundle ID filter")
    since: Optional[str] = Field(None, description="ISO timestamp for log start time")
    limit: int = Field(100, description="Maximum log entries")

class LogEntry(BaseModel):
    """Log entry."""
    timestamp: str = Field(..., description="Log timestamp")
    level: str = Field(..., description="Log level")
    process: str = Field(..., description="Process name")
    message: str = Field(..., description="Log message")

class LogsResult(BaseModel):
    """Logs result."""
    entries: List[LogEntry] = Field(..., description="Log entries")
    total_count: int = Field(..., description="Total entry count")
    filtered_count: int = Field(..., description="Filtered entry count")

class SetPermissionInput(BaseModel):
    """Set permission input."""
    session_id: str = Field(..., description="Session ID")
    bundle_id: str = Field(..., description="App bundle ID")
    service: str = Field(..., description="Permission service: photos, camera, microphone, location, etc.")
    status: str = Field(..., description="Permission status: grant, deny, unset")

class SetStatusBarInput(BaseModel):
    """Set status bar input."""
    session_id: str = Field(..., description="Session ID")
    time: Optional[str] = Field(None, description="Time to display (e.g., '9:41')")
    battery_level: Optional[int] = Field(None, description="Battery level (0-100)")
    cellular_bars: Optional[int] = Field(None, description="Cellular signal bars (0-4)")
    wifi_bars: Optional[int] = Field(None, description="WiFi signal bars (0-3)")

class SetAppearanceInput(BaseModel):
    """Set appearance mode input."""
    session_id: str = Field(..., description="Session ID")
    mode: str = Field(..., description="Appearance mode: light, dark")

# ═══════════════════════════════════════════════════════════════════════════
# GENERIC RESULTS
# ═══════════════════════════════════════════════════════════════════════════

class OperationResult(BaseModel):
    """Generic operation result."""
    success: bool = Field(..., description="Success status")
    message: str = Field(..., description="Result message")
    data: Optional[Dict[str, Any]] = Field(None, description="Additional data")

class ErrorResult(BaseModel):
    """Error result."""
    error: str = Field(..., description="Error message")
    details: Optional[str] = Field(None, description="Error details")
    code: Optional[str] = Field(None, description="Error code")