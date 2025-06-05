"""chuk_mcp_ios_simulator.models

Pydantic models for iOS Simulator MCP server - comprehensive iOS automation.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

# ───────────────────────── Session Management ──────────────────────────
class CreateSessionInput(BaseModel):
    """Create iOS simulator session."""
    device_name: Optional[str] = Field(None, description="Device name (e.g., 'iPhone 15')")
    autoboot: bool = Field(True, description="Auto-boot simulator")

class CreateSessionResult(BaseModel):
    """Session creation result."""
    session_id: str = Field(..., description="Created session ID")
    device_name: str = Field(..., description="Device name")
    udid: str = Field(..., description="Device UDID")

class SessionInfoResult(BaseModel):
    """Session information."""
    session_id: str = Field(..., description="Session ID")
    device_name: str = Field(..., description="Device name")
    udid: str = Field(..., description="Device UDID") 
    state: str = Field(..., description="Device state")

# ───────────────────────── Device Management ──────────────────────────
class ListDevicesResult(BaseModel):
    """Available devices result."""
    devices: List[Dict[str, Any]] = Field(..., description="Available simulators")
    total_count: int = Field(..., description="Total device count")
    booted_count: int = Field(..., description="Booted device count")

class BootDeviceInput(BaseModel):
    """Boot device input."""
    udid: str = Field(..., description="Device UDID")

class DeviceOperationResult(BaseModel):
    """Device operation result."""
    success: bool = Field(..., description="Operation success")
    message: str = Field(..., description="Result message")

# ───────────────────────── App Management ──────────────────────────
class InstallAppInput(BaseModel):
    """Install app input."""
    session_id: str = Field(..., description="Session ID")
    app_path: str = Field(..., description="Path to .app bundle")

class LaunchAppInput(BaseModel):
    """Launch app input."""
    session_id: str = Field(..., description="Session ID")
    bundle_id: str = Field(..., description="App bundle ID")

class AppInfo(BaseModel):
    """App information."""
    bundle_id: str = Field(..., description="Bundle ID")
    name: str = Field(..., description="App name")
    installed_path: str = Field(..., description="Install path")

class ListAppsResult(BaseModel):
    """List apps result."""
    apps: List[AppInfo] = Field(..., description="Installed apps")
    total_count: int = Field(..., description="App count")

# ───────────────────────── UI Interactions ──────────────────────────
class TapInput(BaseModel):
    """Tap gesture input."""
    session_id: str = Field(..., description="Session ID")
    x: int = Field(..., description="X coordinate")
    y: int = Field(..., description="Y coordinate")

class SwipeInput(BaseModel):
    """Swipe gesture input."""
    session_id: str = Field(..., description="Session ID")
    start_x: int = Field(..., description="Start X")
    start_y: int = Field(..., description="Start Y")
    end_x: int = Field(..., description="End X")
    end_y: int = Field(..., description="End Y")
    duration: int = Field(100, description="Duration (ms)")

class InputTextInput(BaseModel):
    """Text input."""
    session_id: str = Field(..., description="Session ID")
    text: str = Field(..., description="Text to input")

class PressButtonInput(BaseModel):
    """Button press input."""
    session_id: str = Field(..., description="Session ID")
    button: str = Field(..., description="Button (home, lock, volume_up, etc.)")

class ScreenshotInput(BaseModel):
    """Screenshot input."""
    session_id: str = Field(..., description="Session ID")
    output_path: Optional[str] = Field(None, description="Output path")

class ScreenshotResult(BaseModel):
    """Screenshot result."""
    success: bool = Field(..., description="Success status")
    file_path: str = Field(..., description="Screenshot path")
    timestamp: str = Field(..., description="Timestamp")

# ───────────────────────── Location and Media ──────────────────────────
class SetLocationInput(BaseModel):
    """Set location input."""
    session_id: str = Field(..., description="Session ID")
    latitude: float = Field(..., description="Latitude")
    longitude: float = Field(..., description="Longitude")

class AddMediaInput(BaseModel):
    """Add media input."""
    session_id: str = Field(..., description="Session ID")
    media_paths: List[str] = Field(..., description="Media file paths")

class MediaOperationResult(BaseModel):
    """Media operation result."""
    success: bool = Field(..., description="Success status")
    files_processed: int = Field(..., description="Files processed")
    message: str = Field(..., description="Result message")

# ───────────────────────── Utilities ──────────────────────────
class OpenUrlInput(BaseModel):
    """Open URL input."""
    session_id: str = Field(..., description="Session ID")
    url: str = Field(..., description="URL to open")

class GetLogsInput(BaseModel):
    """Get logs input."""
    session_id: str = Field(..., description="Session ID")
    bundle_id: Optional[str] = Field(None, description="Bundle ID filter")
    limit: Optional[int] = Field(100, description="Log limit")

class LogsResult(BaseModel):
    """Logs result."""
    logs: str = Field(..., description="Log content")
    entry_count: int = Field(..., description="Entry count")

class ApprovePermissionsInput(BaseModel):
    """Approve permissions input."""
    session_id: str = Field(..., description="Session ID")
    bundle_id: str = Field(..., description="App bundle ID")
    permissions: List[str] = Field(..., description="Permissions to approve")

# ───────────────────────── Generic Results ──────────────────────────
class OperationResult(BaseModel):
    """Generic operation result."""
    success: bool = Field(..., description="Success status")
    message: str = Field(..., description="Result message")
    data: Optional[Dict[str, Any]] = Field(None, description="Additional data")