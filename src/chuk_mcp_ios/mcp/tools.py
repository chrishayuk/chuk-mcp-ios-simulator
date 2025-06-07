#!/usr/bin/env python3
# src/chuk_mcp_ios/mcp/tools.py
"""
Comprehensive iOS Device Control MCP tools - unified iOS automation.
"""

import os
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path
from pydantic import ValidationError

# chuk runtime
from chuk_mcp_runtime.common.mcp_tool_decorator import mcp_tool

# models
from .models import *

# Import iOS control managers - Updated imports
from chuk_mcp_ios.core.device_manager import UnifiedDeviceManager
from chuk_mcp_ios.core.session_manager import UnifiedSessionManager, SessionConfig
from chuk_mcp_ios.core.app_manager import UnifiedAppManager, AppInstallConfig
from chuk_mcp_ios.core.ui_controller import UnifiedUIController
from chuk_mcp_ios.core.media_manager import UnifiedMediaManager
from chuk_mcp_ios.core.utilities_manager import UnifiedUtilitiesManager
from chuk_mcp_ios.core.logger_manager import UnifiedLoggerManager, LogFilter

# Global manager instances
_session_manager: Optional[UnifiedSessionManager] = None
_device_manager: Optional[UnifiedDeviceManager] = None
_app_manager: Optional[UnifiedAppManager] = None
_ui_controller: Optional[UnifiedUIController] = None
_media_manager: Optional[UnifiedMediaManager] = None
_utilities_manager: Optional[UnifiedUtilitiesManager] = None
_logger_manager: Optional[UnifiedLoggerManager] = None

def get_session_manager() -> UnifiedSessionManager:
    """Get session manager instance."""
    global _session_manager
    if _session_manager is None:
        _session_manager = UnifiedSessionManager()
    return _session_manager

def get_device_manager() -> UnifiedDeviceManager:
    """Get device manager instance."""
    global _device_manager
    if _device_manager is None:
        _device_manager = UnifiedDeviceManager()
    return _device_manager

def get_app_manager() -> UnifiedAppManager:
    """Get app manager instance."""
    global _app_manager
    if _app_manager is None:
        _app_manager = UnifiedAppManager()
        _app_manager.set_session_manager(get_session_manager())
    return _app_manager

def get_ui_controller() -> UnifiedUIController:
    """Get UI controller instance."""
    global _ui_controller
    if _ui_controller is None:
        _ui_controller = UnifiedUIController()
        _ui_controller.set_session_manager(get_session_manager())
    return _ui_controller

def get_media_manager() -> UnifiedMediaManager:
    """Get media manager instance."""
    global _media_manager
    if _media_manager is None:
        _media_manager = UnifiedMediaManager()
        _media_manager.set_session_manager(get_session_manager())
    return _media_manager

def get_utilities_manager() -> UnifiedUtilitiesManager:
    """Get utilities manager instance."""
    global _utilities_manager
    if _utilities_manager is None:
        _utilities_manager = UnifiedUtilitiesManager()
        _utilities_manager.set_session_manager(get_session_manager())
    return _utilities_manager

def get_logger_manager() -> UnifiedLoggerManager:
    """Get logger manager instance."""
    global _logger_manager
    if _logger_manager is None:
        _logger_manager = UnifiedLoggerManager()
        _logger_manager.set_session_manager(get_session_manager())
    return _logger_manager

async def run_sync(func, *args, **kwargs):
    """Run sync function in thread pool."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, func, *args, **kwargs)

# ═══════════════════════════════════════════════════════════════════════════
# SESSION MANAGEMENT
# ═══════════════════════════════════════════════════════════════════════════

@mcp_tool(
    name="ios_create_session",
    description="Create new iOS device session with automatic device selection",
    timeout=60
)
async def ios_create_session(
    device_name: Optional[str] = None,
    device_udid: Optional[str] = None,
    device_type: Optional[str] = None,
    platform_version: Optional[str] = None,
    autoboot: bool = True,
    session_name: Optional[str] = None
) -> Dict:
    """Create iOS device session."""
    try:
        from ..core.base import DeviceType as CoreDeviceType
        
        config = SessionConfig(
            device_name=device_name,
            device_udid=device_udid,
            platform_version=platform_version,
            autoboot=autoboot,
            session_name=session_name
        )
        
        # Set device type if specified
        if device_type:
            if device_type == "simulator":
                config.device_type = CoreDeviceType.SIMULATOR
            elif device_type == "real_device":
                config.device_type = CoreDeviceType.REAL_DEVICE
        
        session_manager = get_session_manager()
        session_id = await run_sync(session_manager.create_session, config)
        
        # Get session info
        info = await run_sync(session_manager.get_session_info, session_id)
        
        return CreateSessionResult(
            session_id=session_id,
            device_name=info['device_name'],
            udid=info['device_udid'],
            device_type=info['device_type'],
            platform_version=info.get('os_version', 'Unknown'),
            state=info['current_state']
        ).model_dump()
    except Exception as e:
        return ErrorResult(error=str(e)).model_dump()

@mcp_tool(
    name="ios_list_sessions",
    description="List all active iOS device sessions",
    timeout=10
)
async def ios_list_sessions() -> Dict:
    """List active sessions."""
    try:
        session_manager = get_session_manager()
        session_ids = await run_sync(session_manager.list_sessions)
        
        sessions = []
        for session_id in session_ids:
            try:
                info = await run_sync(session_manager.get_session_info, session_id)
                sessions.append(SessionInfoResult(
                    session_id=session_id,
                    device_name=info['device_name'],
                    udid=info['device_udid'],
                    device_type=info['device_type'],
                    state=info['current_state'],
                    platform_version=info.get('os_version', 'Unknown'),
                    created_at=info['created_at'],
                    is_available=info['is_available']
                ))
            except:
                pass
        
        return ListSessionsResult(
            sessions=sessions,
            total_count=len(sessions)
        ).model_dump()
    except Exception as e:
        return ErrorResult(error=str(e)).model_dump()

@mcp_tool(
    name="ios_terminate_session",
    description="Terminate an iOS device session",
    timeout=15
)
async def ios_terminate_session(session_id: str) -> Dict:
    """Terminate session."""
    try:
        session_manager = get_session_manager()
        await run_sync(session_manager.terminate_session, session_id)
        return OperationResult(
            success=True,
            message=f"Session {session_id} terminated"
        ).model_dump()
    except Exception as e:
        return ErrorResult(error=str(e)).model_dump()

@mcp_tool(
    name="ios_create_automation_session", 
    description="Create optimized session for automation with best available device",
    timeout=60
)
async def ios_create_automation_session(
    device_name: Optional[str] = None,
    device_type: Optional[str] = None
) -> Dict:
    """Create automation session."""
    try:
        session_manager = get_session_manager()
        config = {'device_name': device_name} if device_name else {}
        if device_type:
            config['device_type'] = device_type
            
        session_id = await run_sync(session_manager.create_automation_session, config)
        
        # Get session info
        info = await run_sync(session_manager.get_session_info, session_id)
        
        return CreateSessionResult(
            session_id=session_id,
            device_name=info['device_name'],
            udid=info['device_udid'],
            device_type=info['device_type'],
            platform_version=info.get('os_version', 'Unknown'),
            state=info['current_state']
        ).model_dump()
    except Exception as e:
        return ErrorResult(error=str(e)).model_dump()

# ═══════════════════════════════════════════════════════════════════════════
# DEVICE MANAGEMENT
# ═══════════════════════════════════════════════════════════════════════════

@mcp_tool(
    name="ios_list_devices",
    description="List all available iOS devices (simulators and real devices)",
    timeout=15
)
async def ios_list_devices() -> Dict:
    """List available devices."""
    try:
        device_manager = get_device_manager()
        devices = await run_sync(device_manager.discover_all_devices)
        
        device_list = []
        simulators = 0
        real_devices = 0
        available_count = 0
        
        for device in devices:
            device_info = DeviceInfo(
                udid=device.udid,
                name=device.name,
                state=device.state.value,
                device_type=device.device_type.value,
                os_version=device.os_version,
                model=device.model,
                connection_type=device.connection_type,
                is_available=device.is_available
            )
            device_list.append(device_info)
            
            if device.device_type.value == 'simulator':
                simulators += 1
            else:
                real_devices += 1
                
            if device.is_available:
                available_count += 1
        
        return ListDevicesResult(
            devices=device_list,
            total_count=len(device_list),
            simulators=simulators,
            real_devices=real_devices,
            available_count=available_count
        ).model_dump()
    except Exception as e:
        return ErrorResult(error=str(e)).model_dump()

@mcp_tool(
    name="ios_boot_device",
    description="Boot an iOS simulator or connect to real device by UDID",
    timeout=60
)
async def ios_boot_device(udid: str, timeout: int = 60) -> Dict:
    """Boot device."""
    try:
        device_manager = get_device_manager()
        await run_sync(device_manager.boot_device, udid, timeout)
        
        # Get updated device info
        device = await run_sync(device_manager.get_device, udid)
        if device:
            device_info = DeviceInfo(
                udid=device.udid,
                name=device.name,
                state=device.state.value,
                device_type=device.device_type.value,
                os_version=device.os_version,
                model=device.model,
                connection_type=device.connection_type,
                is_available=device.is_available
            )
        else:
            device_info = None
        
        return DeviceOperationResult(
            success=True,
            message=f"Device {udid} booted/connected successfully",
            device_info=device_info
        ).model_dump()
    except Exception as e:
        return ErrorResult(error=str(e)).model_dump()

@mcp_tool(
    name="ios_shutdown_device",
    description="Shutdown an iOS simulator (real devices cannot be shutdown programmatically)",
    timeout=30
)
async def ios_shutdown_device(udid: str) -> Dict:
    """Shutdown device."""
    try:
        device_manager = get_device_manager()
        await run_sync(device_manager.shutdown_device, udid)
        
        return DeviceOperationResult(
            success=True,
            message=f"Device {udid} shutdown successfully"
        ).model_dump()
    except Exception as e:
        return ErrorResult(error=str(e)).model_dump()

# ═══════════════════════════════════════════════════════════════════════════
# APP MANAGEMENT
# ═══════════════════════════════════════════════════════════════════════════

@mcp_tool(
    name="ios_install_app",
    description="Install an app on iOS device (.app bundle or .ipa file)",
    timeout=120
)
async def ios_install_app(
    session_id: str,
    app_path: str,
    force_reinstall: bool = False,
    launch_after_install: bool = False
) -> Dict:
    """Install app."""
    try:
        config = AppInstallConfig(
            force_reinstall=force_reinstall,
            launch_after_install=launch_after_install
        )
        
        app_manager = get_app_manager()
        app_info = await run_sync(app_manager.install_app, session_id, app_path, config)
        
        return AppOperationResult(
            success=True,
            message=f"App {app_info.name} installed successfully",
            app_info=AppInfo(
                bundle_id=app_info.bundle_id,
                name=app_info.name,
                version=app_info.version,
                installed_path=app_info.installed_path
            )
        ).model_dump()
    except Exception as e:
        return ErrorResult(error=str(e)).model_dump()

@mcp_tool(
    name="ios_launch_app",
    description="Launch an app on iOS device by bundle ID",
    timeout=30
)
async def ios_launch_app(
    session_id: str,
    bundle_id: str,
    arguments: Optional[List[str]] = None
) -> Dict:
    """Launch app."""
    try:
        app_manager = get_app_manager()
        await run_sync(app_manager.launch_app, session_id, bundle_id, arguments)
        
        return OperationResult(
            success=True,
            message=f"App {bundle_id} launched"
        ).model_dump()
    except Exception as e:
        return ErrorResult(error=str(e)).model_dump()

@mcp_tool(
    name="ios_terminate_app",
    description="Terminate a running app",
    timeout=15
)
async def ios_terminate_app(session_id: str, bundle_id: str) -> Dict:
    """Terminate app."""
    try:
        app_manager = get_app_manager()
        await run_sync(app_manager.terminate_app, session_id, bundle_id)
        
        return OperationResult(
            success=True,
            message=f"App {bundle_id} terminated"
        ).model_dump()
    except Exception as e:
        return ErrorResult(error=str(e)).model_dump()

@mcp_tool(
    name="ios_uninstall_app",
    description="Uninstall an app from iOS device",
    timeout=30
)
async def ios_uninstall_app(session_id: str, bundle_id: str) -> Dict:
    """Uninstall app."""
    try:
        app_manager = get_app_manager()
        await run_sync(app_manager.uninstall_app, session_id, bundle_id)
        
        return OperationResult(
            success=True,
            message=f"App {bundle_id} uninstalled"
        ).model_dump()
    except Exception as e:
        return ErrorResult(error=str(e)).model_dump()

@mcp_tool(
    name="ios_list_apps",
    description="List installed apps on iOS device",
    timeout=20
)
async def ios_list_apps(session_id: str, user_apps_only: bool = True) -> Dict:
    """List apps."""
    try:
        app_manager = get_app_manager()
        apps = await run_sync(app_manager.list_apps, session_id, user_apps_only)
        
        app_list = []
        user_count = 0
        
        for app in apps:
            app_info = AppInfo(
                bundle_id=app.bundle_id,
                name=app.name,
                version=app.version,
                installed_path=app.installed_path
            )
            app_list.append(app_info)
            
            if not app.bundle_id.startswith('com.apple.'):
                user_count += 1
        
        return ListAppsResult(
            apps=app_list,
            total_count=len(app_list),
            user_app_count=user_count
        ).model_dump()
    except Exception as e:
        return ErrorResult(error=str(e)).model_dump()

# ═══════════════════════════════════════════════════════════════════════════
# UI INTERACTIONS
# ═══════════════════════════════════════════════════════════════════════════

@mcp_tool(
    name="ios_tap",
    description="Tap at coordinates on iOS device screen",
    timeout=10
)
async def ios_tap(session_id: str, x: int, y: int) -> Dict:
    """Tap gesture."""
    try:
        ui_controller = get_ui_controller()
        await run_sync(ui_controller.tap, session_id, x, y)
        
        return OperationResult(
            success=True,
            message=f"Tapped at ({x}, {y})"
        ).model_dump()
    except Exception as e:
        return ErrorResult(error=str(e)).model_dump()

@mcp_tool(
    name="ios_double_tap",
    description="Double tap at coordinates",
    timeout=10
)
async def ios_double_tap(session_id: str, x: int, y: int) -> Dict:
    """Double tap."""
    try:
        ui_controller = get_ui_controller()
        await run_sync(ui_controller.double_tap, session_id, x, y)
        
        return OperationResult(
            success=True,
            message=f"Double tapped at ({x}, {y})"
        ).model_dump()
    except Exception as e:
        return ErrorResult(error=str(e)).model_dump()

@mcp_tool(
    name="ios_long_press",
    description="Long press at coordinates",
    timeout=10
)
async def ios_long_press(
    session_id: str,
    x: int,
    y: int,
    duration: float = 1.0
) -> Dict:
    """Long press."""
    try:
        ui_controller = get_ui_controller()
        await run_sync(ui_controller.long_press, session_id, x, y, duration)
        
        return OperationResult(
            success=True,
            message=f"Long pressed at ({x}, {y}) for {duration}s"
        ).model_dump()
    except Exception as e:
        return ErrorResult(error=str(e)).model_dump()

@mcp_tool(
    name="ios_swipe",
    description="Swipe gesture on iOS device",
    timeout=10
)
async def ios_swipe(
    session_id: str,
    start_x: int,
    start_y: int,
    end_x: int,
    end_y: int,
    duration: int = 300
) -> Dict:
    """Swipe gesture."""
    try:
        ui_controller = get_ui_controller()
        await run_sync(ui_controller.swipe, session_id, start_x, start_y, end_x, end_y, duration)
        
        return OperationResult(
            success=True,
            message=f"Swiped from ({start_x}, {start_y}) to ({end_x}, {end_y})"
        ).model_dump()
    except Exception as e:
        return ErrorResult(error=str(e)).model_dump()

@mcp_tool(
    name="ios_swipe_direction",
    description="Swipe in a direction (up, down, left, right)",
    timeout=10
)
async def ios_swipe_direction(
    session_id: str,
    direction: str,
    distance: Optional[int] = None,
    duration: int = 300
) -> Dict:
    """Swipe by direction."""
    try:
        ui_controller = get_ui_controller()
        
        if direction == "up":
            await run_sync(ui_controller.swipe_up, session_id, distance, duration)
        elif direction == "down":
            await run_sync(ui_controller.swipe_down, session_id, distance, duration)
        elif direction == "left":
            await run_sync(ui_controller.swipe_left, session_id, distance, duration)
        elif direction == "right":
            await run_sync(ui_controller.swipe_right, session_id, distance, duration)
        else:
            return ErrorResult(error=f"Invalid direction: {direction}").model_dump()
        
        return OperationResult(
            success=True,
            message=f"Swiped {direction}"
        ).model_dump()
    except Exception as e:
        return ErrorResult(error=str(e)).model_dump()

@mcp_tool(
    name="ios_input_text",
    description="Input text into focused field on iOS device",
    timeout=15
)
async def ios_input_text(session_id: str, text: str) -> Dict:
    """Input text."""
    try:
        ui_controller = get_ui_controller()
        await run_sync(ui_controller.input_text, session_id, text)
        
        return OperationResult(
            success=True,
            message=f"Input text: {text[:50]}{'...' if len(text) > 50 else ''}"
        ).model_dump()
    except Exception as e:
        return ErrorResult(error=str(e)).model_dump()

@mcp_tool(
    name="ios_press_button",
    description="Press hardware button (home, lock, volume_up, volume_down)",
    timeout=10
)
async def ios_press_button(session_id: str, button: str) -> Dict:
    """Press button."""
    try:
        ui_controller = get_ui_controller()
        await run_sync(ui_controller.press_button, session_id, button)
        
        return OperationResult(
            success=True,
            message=f"Pressed {button} button"
        ).model_dump()
    except Exception as e:
        return ErrorResult(error=str(e)).model_dump()

@mcp_tool(
    name="ios_screenshot",
    description="Take screenshot of iOS device",
    timeout=20
)
async def ios_screenshot(
    session_id: str,
    output_path: Optional[str] = None
) -> Dict:
    """Take screenshot."""
    try:
        ui_controller = get_ui_controller()
        
        # Generate path if not provided
        if not output_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"screenshot_{timestamp}.png"
        
        result = await run_sync(ui_controller.take_screenshot, session_id, output_path)
        
        # Get file info
        file_path = result if isinstance(result, str) else output_path
        file_size = os.path.getsize(file_path) if os.path.exists(file_path) else 0
        
        return ScreenshotResult(
            success=True,
            file_path=file_path,
            file_size=file_size,
            timestamp=datetime.now().isoformat()
        ).model_dump()
    except Exception as e:
        return ErrorResult(error=str(e)).model_dump()

@mcp_tool(
    name="ios_record_video",
    description="Record video from iOS device",
    timeout=120
)
async def ios_record_video(
    session_id: str,
    output_path: str,
    duration: int = 10,
    quality: Optional[str] = None
) -> Dict:
    """Record video."""
    try:
        ui_controller = get_ui_controller()
        
        options = {}
        if quality:
            options['quality'] = quality
        
        result = await run_sync(
            ui_controller.record_video,
            session_id,
            output_path,
            duration,
            options
        )
        
        return OperationResult(
            success=True,
            message=f"Video recorded: {output_path}",
            data={"file_path": result}
        ).model_dump()
    except Exception as e:
        return ErrorResult(error=str(e)).model_dump()

@mcp_tool(
    name="ios_get_screen_info",
    description="Get screen dimensions and orientation",
    timeout=10
)
async def ios_get_screen_info(session_id: str) -> Dict:
    """Get screen info."""
    try:
        ui_controller = get_ui_controller()
        screen_info = await run_sync(ui_controller.get_screen_info, session_id)
        
        return ScreenInfo(
            width=screen_info.width,
            height=screen_info.height,
            scale=screen_info.scale,
            orientation=screen_info.orientation
        ).model_dump()
    except Exception as e:
        return ErrorResult(error=str(e)).model_dump()

# ═══════════════════════════════════════════════════════════════════════════
# LOCATION & MEDIA
# ═══════════════════════════════════════════════════════════════════════════

@mcp_tool(
    name="ios_set_location",
    description="Set GPS location on iOS device",
    timeout=15
)
async def ios_set_location(
    session_id: str,
    latitude: float,
    longitude: float,
    altitude: Optional[float] = None
) -> Dict:
    """Set location."""
    try:
        media_manager = get_media_manager()
        await run_sync(media_manager.set_location, session_id, latitude, longitude, altitude)
        
        return OperationResult(
            success=True,
            message=f"Location set to {latitude}, {longitude}"
        ).model_dump()
    except Exception as e:
        return ErrorResult(error=str(e)).model_dump()

@mcp_tool(
    name="ios_set_location_by_name",
    description="Set location by city/landmark name (e.g., 'San Francisco', 'Tokyo')",
    timeout=15
)
async def ios_set_location_by_name(session_id: str, location_name: str) -> Dict:
    """Set location by name."""
    try:
        media_manager = get_media_manager()
        await run_sync(media_manager.set_location_by_name, session_id, location_name)
        
        return OperationResult(
            success=True,
            message=f"Location set to {location_name}"
        ).model_dump()
    except Exception as e:
        return ErrorResult(error=str(e)).model_dump()

@mcp_tool(
    name="ios_add_media",
    description="Add photos/videos to iOS device Photos library",
    timeout=30
)
async def ios_add_media(session_id: str, media_paths: List[str]) -> Dict:
    """Add media."""
    try:
        media_manager = get_media_manager()
        added_files = await run_sync(media_manager.add_media, session_id, media_paths)
        
        return MediaOperationResult(
            success=True,
            files_processed=len(added_files),
            files_failed=len(media_paths) - len(added_files),
            message=f"Added {len(added_files)} media files"
        ).model_dump()
    except Exception as e:
        return ErrorResult(error=str(e)).model_dump()

# ═══════════════════════════════════════════════════════════════════════════
# UTILITIES
# ═══════════════════════════════════════════════════════════════════════════

@mcp_tool(
    name="ios_open_url",
    description="Open URL in Safari on iOS device",
    timeout=20
)
async def ios_open_url(session_id: str, url: str) -> Dict:
    """Open URL."""
    try:
        utilities = get_utilities_manager()
        await run_sync(utilities.open_url, session_id, url)
        
        return OperationResult(
            success=True,
            message=f"Opened {url}"
        ).model_dump()
    except Exception as e:
        return ErrorResult(error=str(e)).model_dump()

@mcp_tool(
    name="ios_get_logs",
    description="Get system or app logs from iOS device",
    timeout=30
)
async def ios_get_logs(
    session_id: str,
    bundle_id: Optional[str] = None,
    since: Optional[str] = None,
    limit: int = 100
) -> Dict:
    """Get logs."""
    try:
        logger = get_logger_manager()
        
        # Parse since timestamp if provided
        since_dt = None
        if since:
            since_dt = datetime.fromisoformat(since)
        
        # Create filter
        filter = LogFilter(bundle_id=bundle_id, since=since_dt)
        
        # Get logs
        logs = await run_sync(logger.get_logs, session_id, filter, limit)
        
        # Convert to result format
        entries = []
        for log in logs:
            entries.append(LogEntry(
                timestamp=log.timestamp.isoformat(),
                level=log.level,
                process=log.process,
                message=log.message
            ))
        
        return LogsResult(
            entries=entries,
            total_count=len(entries),
            filtered_count=len(entries)
        ).model_dump()
    except Exception as e:
        return ErrorResult(error=str(e)).model_dump()

@mcp_tool(
    name="ios_set_permission",
    description="Set app permission (photos, camera, microphone, location, etc.)",
    timeout=15
)
async def ios_set_permission(
    session_id: str,
    bundle_id: str,
    service: str,
    status: str
) -> Dict:
    """Set permission."""
    try:
        utilities = get_utilities_manager()
        await run_sync(utilities.set_permission, session_id, bundle_id, service, status)
        
        return OperationResult(
            success=True,
            message=f"Set {service} permission to {status} for {bundle_id}"
        ).model_dump()
    except Exception as e:
        return ErrorResult(error=str(e)).model_dump()

@mcp_tool(
    name="ios_set_status_bar",
    description="Customize status bar appearance (simulators only)",
    timeout=10
)
async def ios_set_status_bar(
    session_id: str,
    time: Optional[str] = None,
    battery_level: Optional[int] = None,
    cellular_bars: Optional[int] = None,
    wifi_bars: Optional[int] = None
) -> Dict:
    """Set status bar."""
    try:
        # Get device UDID from session
        session_manager = get_session_manager()
        udid = await run_sync(session_manager.get_device_udid, session_id)
        
        # Build command
        from ..core.base import CommandExecutor
        executor = CommandExecutor()
        
        cmd = f"xcrun simctl status_bar {udid} override"
        if time:
            cmd += f" --time '{time}'"
        if battery_level is not None:
            cmd += f" --batteryLevel {battery_level}"
        if cellular_bars is not None:
            cmd += f" --cellularBars {cellular_bars}"
        if wifi_bars is not None:
            cmd += f" --wifiBars {wifi_bars}"
        
        await run_sync(executor.run_command, cmd)
        
        return OperationResult(
            success=True,
            message="Status bar updated"
        ).model_dump()
    except Exception as e:
        return ErrorResult(error=str(e)).model_dump()

@mcp_tool(
    name="ios_set_appearance",
    description="Set light or dark mode (simulators only)",
    timeout=10
)
async def ios_set_appearance(session_id: str, mode: str) -> Dict:
    """Set appearance mode."""
    try:
        # Get device UDID from session
        session_manager = get_session_manager()
        udid = await run_sync(session_manager.get_device_udid, session_id)
        
        # Set appearance
        from ..core.base import CommandExecutor
        executor = CommandExecutor()
        
        await run_sync(executor.run_command, f"xcrun simctl ui {udid} appearance {mode}")
        
        return OperationResult(
            success=True,
            message=f"Appearance set to {mode} mode"
        ).model_dump()
    except Exception as e:
        return ErrorResult(error=str(e)).model_dump()

@mcp_tool(
    name="ios_clear_keychain",
    description="Clear device keychain (simulators only)",
    timeout=15
)
async def ios_clear_keychain(session_id: str) -> Dict:
    """Clear keychain."""
    try:
        utilities = get_utilities_manager()
        await run_sync(utilities.clear_keychain, session_id)
        
        return OperationResult(
            success=True,
            message="Keychain cleared"
        ).model_dump()
    except Exception as e:
        return ErrorResult(error=str(e)).model_dump()

@mcp_tool(
    name="ios_focus_simulator",
    description="Focus simulator window (simulators only)",
    timeout=10
)
async def ios_focus_simulator(session_id: str) -> Dict:
    """Focus simulator."""
    try:
        utilities = get_utilities_manager()
        await run_sync(utilities.focus_simulator, session_id)
        
        return OperationResult(
            success=True,
            message="Simulator window focused"
        ).model_dump()
    except Exception as e:
        return ErrorResult(error=str(e)).model_dump()