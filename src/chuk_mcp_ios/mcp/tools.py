#!/usr/bin/env python3
# src/chuk_mcp_ios/mcp/tools.py
"""
Comprehensive iOS Device Control MCP tools - unified iOS automation.
Enhanced with CHUK Sessions for persistent session management across tool calls.
FIXED: Renamed session_id parameters to ios_session_id to avoid MCP runtime validation.
"""

import os
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path

# chuk runtime
from chuk_mcp_runtime.common.mcp_tool_decorator import mcp_tool

# CHUK Sessions integration
from chuk_sessions import SessionManager

# models
from .models import *

# Import iOS control managers
from chuk_mcp_ios.core.device_manager import UnifiedDeviceManager
from chuk_mcp_ios.core.session_manager import UnifiedSessionManager, SessionConfig
from chuk_mcp_ios.core.app_manager import UnifiedAppManager, AppInstallConfig
from chuk_mcp_ios.core.ui_controller import UnifiedUIController
from chuk_mcp_ios.core.media_manager import UnifiedMediaManager
from chuk_mcp_ios.core.utilities_manager import UnifiedUtilitiesManager
from chuk_mcp_ios.core.logger_manager import UnifiedLoggerManager, LogFilter

# ═══════════════════════════════════════════════════════════════════════════
# CHUK SESSIONS INTEGRATION
# ═══════════════════════════════════════════════════════════════════════════

# Initialize CHUK Sessions manager with proper error handling
os.environ.setdefault('SESSION_PROVIDER', 'memory')

try:
    ios_session_manager = SessionManager(
        sandbox_id="ios-device-control",
        default_ttl_hours=24
    )
    print("🔐 CHUK Sessions manager initialized successfully")
except Exception as e:
    print(f"❌ Failed to initialize CHUK Sessions: {e}")
    ios_session_manager = None

# Store session metadata separately since CHUK Sessions manages its own IDs
_ios_session_registry: Dict[str, Dict[str, Any]] = {}

# ═══════════════════════════════════════════════════════════════════════════
# SINGLETON MANAGER INSTANCES
# ═══════════════════════════════════════════════════════════════════════════

_device_manager: Optional[UnifiedDeviceManager] = None
_unified_session_manager: Optional[UnifiedSessionManager] = None

def get_device_manager() -> UnifiedDeviceManager:
    """Get device manager instance."""
    global _device_manager
    if _device_manager is None:
        _device_manager = UnifiedDeviceManager()
    return _device_manager

def get_unified_session_manager() -> UnifiedSessionManager:
    """Get THE SAME UnifiedSessionManager instance across all calls."""
    global _unified_session_manager
    if _unified_session_manager is None:
        print("🔧 Creating singleton UnifiedSessionManager")
        _unified_session_manager = UnifiedSessionManager()
    return _unified_session_manager

# ═══════════════════════════════════════════════════════════════════════════
# SESSION VALIDATION
# ═══════════════════════════════════════════════════════════════════════════

async def simple_session_validation(session_id: str) -> bool:
    """Simple, fast session validation that just works."""
    try:
        print(f"🔍 Quick validation for session: {session_id}")
        unified_manager = get_unified_session_manager()
        is_valid = session_id in unified_manager.sessions
        print(f"✅ Session {session_id} valid: {is_valid}")
        return is_valid
    except Exception as e:
        print(f"❌ Session validation error: {e}")
        return False

async def register_ios_session(session_id: str, device_info: Dict[str, Any], ios_session_manager_instance) -> bool:
    """Register an iOS session using CHUK Sessions for persistence."""
    global _ios_session_registry
    
    if not ios_session_manager:
        print("❌ CHUK Sessions not available")
        return False
    
    try:
        # Create session in CHUK Sessions using our session_id as user_id
        chuk_session_id = await ios_session_manager.allocate_session(
            user_id=session_id,
            ttl_hours=24,
            custom_metadata={
                'ios_session_id': session_id,
                'device_udid': device_info.get('device_udid', ''),
                'device_name': device_info.get('device_name', ''),
                'device_type': device_info.get('device_type', ''),
                'platform_version': device_info.get('os_version', ''),
                'state': device_info.get('current_state', ''),
                'manager_id': str(id(ios_session_manager_instance)),
                'created_at': datetime.now().isoformat(),
                'session_type': 'ios_device'
            }
        )
        
        # Store session mapping in our registry
        _ios_session_registry[session_id] = {
            'chuk_session_id': chuk_session_id,
            'device_info': device_info,
            'created_at': datetime.now().isoformat(),
            'ios_manager_instance': ios_session_manager_instance
        }
        
        print(f"🔐 iOS session registered with CHUK Sessions:")
        print(f"   iOS Session ID: {session_id}")
        print(f"   CHUK Session ID: {chuk_session_id}")
        return True
        
    except Exception as e:
        print(f"❌ Failed to register session {session_id}: {e}")
        return False

async def unregister_ios_session(session_id: str):
    """Unregister iOS session from CHUK Sessions."""
    global _ios_session_registry
    
    try:
        registry_entry = _ios_session_registry.get(session_id)
        
        # Delete from CHUK Sessions if available
        if ios_session_manager and registry_entry:
            chuk_session_id = registry_entry.get('chuk_session_id')
            if chuk_session_id:
                try:
                    await ios_session_manager.delete_session(chuk_session_id)
                    print(f"🗑️ CHUK session {chuk_session_id} deleted")
                except Exception as e:
                    print(f"⚠️ Failed to delete CHUK session: {e}")
        
        # Remove from our registry
        if registry_entry:
            del _ios_session_registry[session_id]
            print(f"🗑️ iOS session {session_id} removed from registry")
        
    except Exception as e:
        print(f"❌ Failed to unregister session {session_id}: {e}")

async def get_manager_for_session(session_id: str, manager_class):
    """Get a manager instance configured for a specific session."""
    print(f"🔧 Getting {manager_class.__name__} for session: {session_id}")
    
    # Check if session is valid
    if not await simple_session_validation(session_id):
        raise Exception(f"Session {session_id} is invalid or expired")
    
    # Get the singleton UnifiedSessionManager
    unified_session_manager = get_unified_session_manager()
    
    # Create manager instance
    manager = manager_class()
    
    # Configure manager if it supports session management
    if hasattr(manager, 'set_session_manager'):
        manager.set_session_manager(unified_session_manager)
        print(f"🔧 {manager_class.__name__} configured for session {session_id}")
    
    return manager

async def run_sync(func, *args, **kwargs):
    """Run sync function in thread pool."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, func, *args, **kwargs)

# ═══════════════════════════════════════════════════════════════════════════
# SESSION MANAGEMENT TOOLS
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
        
        # Use the singleton UnifiedSessionManager
        unified_session_manager = get_unified_session_manager()
        
        # Create session
        try:
            session_id = await run_sync(unified_session_manager.create_session, config)
            print(f"🎯 Session created in singleton manager: {session_id}")
        except Exception as e:
            return {"error": f"Failed to create session: {e}"}
        
        # Get session info
        try:
            info = await run_sync(unified_session_manager.get_session_info, session_id)
        except Exception as e:
            # Clean up failed session
            try:
                await run_sync(unified_session_manager.terminate_session, session_id)
            except:
                pass
            return {"error": f"Failed to get session info: {e}"}
        
        # Register session with CHUK Sessions for persistence
        chuk_registered = await register_ios_session(session_id, info, unified_session_manager)
        
        # Return success
        return {
            "session_id": session_id,
            "device_name": info['device_name'],
            "udid": info['device_udid'],
            "device_type": info['device_type'],
            "platform_version": info.get('os_version', 'Unknown'),
            "state": info['current_state'],
            "registered_with_chuk": chuk_registered,
            "chuk_available": ios_session_manager is not None
        }
        
    except Exception as e:
        return {"error": f"Session creation failed: {e}"}

@mcp_tool(
    name="ios_list_sessions",
    description="List all active iOS device sessions",
    timeout=10
)
async def ios_list_sessions() -> Dict:
    """List active sessions."""
    try:
        # Get sessions from the singleton UnifiedSessionManager
        unified_manager = get_unified_session_manager()
        session_ids = await run_sync(unified_manager.list_sessions)
        print(f"📋 Found {len(session_ids)} sessions in singleton manager")
        
        sessions = []
        for session_id in session_ids:
            try:
                info = await run_sync(unified_manager.get_session_info, session_id)
                
                sessions.append(SessionInfoResult(
                    session_id=session_id,
                    device_name=info.get('device_name', 'Unknown'),
                    udid=info.get('device_udid', 'Unknown'),
                    device_type=info.get('device_type', 'Unknown'),
                    state=info.get('current_state', 'unknown'),
                    platform_version=info.get('os_version', 'Unknown'),
                    created_at=info.get('created_at', ''),
                    is_available=info.get('is_available', False)
                ))
            except Exception as e:
                print(f"Warning: Could not get info for session {session_id}: {e}")
        
        return ListSessionsResult(
            sessions=sessions,
            total_count=len(sessions),
            chuk_sessions_available=ios_session_manager is not None
        ).model_dump()
        
    except Exception as e:
        return ErrorResult(error=str(e)).model_dump()

@mcp_tool(
    name="ios_terminate_session",
    description="Terminate an iOS device session",
    timeout=15
)
async def ios_terminate_session(ios_session_id: str) -> Dict:
    """Terminate session with cleanup."""
    try:
        # Terminate in the singleton UnifiedSessionManager
        unified_session_manager = get_unified_session_manager()
        try:
            await run_sync(unified_session_manager.terminate_session, ios_session_id)
            print(f"✅ Session terminated in singleton manager: {ios_session_id}")
        except Exception as e:
            print(f"Warning: Failed to terminate in UnifiedSessionManager: {e}")
        
        # Remove from CHUK Sessions and registry
        await unregister_ios_session(ios_session_id)
        
        return OperationResult(
            success=True,
            message=f"Session {ios_session_id} terminated successfully"
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
        # Use the singleton UnifiedSessionManager
        unified_session_manager = get_unified_session_manager()
        config = {'device_name': device_name} if device_name else {}
        if device_type:
            config['device_type'] = device_type
            
        session_id = await run_sync(unified_session_manager.create_automation_session, config)
        print(f"🎯 Automation session created in singleton manager: {session_id}")
        
        # Get session info
        info = await run_sync(unified_session_manager.get_session_info, session_id)
        
        # Register with CHUK Sessions
        chuk_registered = await register_ios_session(session_id, info, unified_session_manager)
        
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
    name="ios_session_status",
    description="Get detailed status of an iOS session",
    timeout=10
)
async def ios_session_status(ios_session_id: str) -> Dict:
    """Get session status."""
    try:
        # Check if session exists in singleton manager
        unified_manager = get_unified_session_manager()
        in_unified = ios_session_id in unified_manager.sessions
        
        unified_info = None
        if in_unified:
            try:
                unified_info = await run_sync(unified_manager.get_session_info, ios_session_id)
            except Exception as e:
                print(f"Warning: Could not get unified info: {e}")
        
        return {
            "session_id": ios_session_id,
            "in_unified_manager": in_unified,
            "chuk_sessions_available": ios_session_manager is not None,
            "unified_info": unified_info,
            "overall_valid": in_unified
        }
        
    except Exception as e:
        return ErrorResult(error=str(e)).model_dump()

# ═══════════════════════════════════════════════════════════════════════════
# DEVICE MANAGEMENT (no session required)
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
# APP MANAGEMENT - FIXED WITH ios_session_id PARAMETER
# ═══════════════════════════════════════════════════════════════════════════

@mcp_tool(
    name="ios_install_app",
    description="Install an app on iOS device (.app bundle or .ipa file)",
    timeout=120
)
async def ios_install_app(
    ios_session_id: str,
    app_path: str,
    force_reinstall: bool = False,
    launch_after_install: bool = False
) -> Dict:
    """Install app."""
    try:
        if not await simple_session_validation(ios_session_id):
            return ErrorResult(error=f"Session {ios_session_id} is invalid").model_dump()
        
        config = AppInstallConfig(
            force_reinstall=force_reinstall,
            launch_after_install=launch_after_install
        )
        
        app_manager = await get_manager_for_session(ios_session_id, UnifiedAppManager)
        app_info = await run_sync(app_manager.install_app, ios_session_id, app_path, config)
        
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
    ios_session_id: str,
    bundle_id: str,
    arguments: Optional[List[str]] = None
) -> Dict:
    """Launch app."""
    try:
        if not await simple_session_validation(ios_session_id):
            return ErrorResult(error=f"Session {ios_session_id} is invalid").model_dump()
        
        app_manager = await get_manager_for_session(ios_session_id, UnifiedAppManager)
        await run_sync(app_manager.launch_app, ios_session_id, bundle_id, arguments)
        
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
async def ios_terminate_app(ios_session_id: str, bundle_id: str) -> Dict:
    """Terminate app."""
    try:
        if not await simple_session_validation(ios_session_id):
            return ErrorResult(error=f"Session {ios_session_id} is invalid").model_dump()
        
        app_manager = await get_manager_for_session(ios_session_id, UnifiedAppManager)
        await run_sync(app_manager.terminate_app, ios_session_id, bundle_id)
        
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
async def ios_uninstall_app(ios_session_id: str, bundle_id: str) -> Dict:
    """Uninstall app."""
    try:
        if not await simple_session_validation(ios_session_id):
            return ErrorResult(error=f"Session {ios_session_id} is invalid").model_dump()
        
        app_manager = await get_manager_for_session(ios_session_id, UnifiedAppManager)
        await run_sync(app_manager.uninstall_app, ios_session_id, bundle_id)
        
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
async def ios_list_apps(ios_session_id: str, user_apps_only: bool = True) -> Dict:
    """List apps."""
    try:
        if not await simple_session_validation(ios_session_id):
            return ErrorResult(error=f"Session {ios_session_id} is invalid").model_dump()
        
        app_manager = await get_manager_for_session(ios_session_id, UnifiedAppManager)
        apps = await run_sync(app_manager.list_apps, ios_session_id, user_apps_only)
        
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
# UI INTERACTIONS - FIXED WITH ios_session_id PARAMETER
# ═══════════════════════════════════════════════════════════════════════════

@mcp_tool(
    name="ios_tap",
    description="Tap at coordinates on iOS device screen",
    timeout=10
)
async def ios_tap(ios_session_id: str, x: int, y: int) -> Dict:
    """Tap gesture."""
    try:
        if not await simple_session_validation(ios_session_id):
            return ErrorResult(error=f"Session {ios_session_id} is invalid").model_dump()
        
        ui_controller = await get_manager_for_session(ios_session_id, UnifiedUIController)
        await run_sync(ui_controller.tap, ios_session_id, x, y)
        
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
async def ios_double_tap(ios_session_id: str, x: int, y: int) -> Dict:
    """Double tap."""
    try:
        if not await simple_session_validation(ios_session_id):
            return ErrorResult(error=f"Session {ios_session_id} is invalid").model_dump()
        
        ui_controller = await get_manager_for_session(ios_session_id, UnifiedUIController)
        await run_sync(ui_controller.double_tap, ios_session_id, x, y)
        
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
    ios_session_id: str,
    x: int,
    y: int,
    duration: float = 1.0
) -> Dict:
    """Long press."""
    try:
        if not await simple_session_validation(ios_session_id):
            return ErrorResult(error=f"Session {ios_session_id} is invalid").model_dump()
        
        ui_controller = await get_manager_for_session(ios_session_id, UnifiedUIController)
        await run_sync(ui_controller.long_press, ios_session_id, x, y, duration)
        
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
    ios_session_id: str,
    start_x: int,
    start_y: int,
    end_x: int,
    end_y: int,
    duration: int = 300
) -> Dict:
    """Swipe gesture."""
    try:
        if not await simple_session_validation(ios_session_id):
            return ErrorResult(error=f"Session {ios_session_id} is invalid").model_dump()
        
        ui_controller = await get_manager_for_session(ios_session_id, UnifiedUIController)
        await run_sync(ui_controller.swipe, ios_session_id, start_x, start_y, end_x, end_y, duration)
        
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
    ios_session_id: str,
    direction: str,
    distance: Optional[int] = None,
    duration: int = 300
) -> Dict:
    """Swipe by direction."""
    try:
        if not await simple_session_validation(ios_session_id):
            return ErrorResult(error=f"Session {ios_session_id} is invalid").model_dump()
        
        ui_controller = await get_manager_for_session(ios_session_id, UnifiedUIController)
        
        if direction == "up":
            await run_sync(ui_controller.swipe_up, ios_session_id, distance, duration)
        elif direction == "down":
            await run_sync(ui_controller.swipe_down, ios_session_id, distance, duration)
        elif direction == "left":
            await run_sync(ui_controller.swipe_left, ios_session_id, distance, duration)
        elif direction == "right":
            await run_sync(ui_controller.swipe_right, ios_session_id, distance, duration)
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
async def ios_input_text(ios_session_id: str, text: str) -> Dict:
    """Input text."""
    try:
        if not await simple_session_validation(ios_session_id):
            return ErrorResult(error=f"Session {ios_session_id} is invalid").model_dump()
        
        ui_controller = await get_manager_for_session(ios_session_id, UnifiedUIController)
        await run_sync(ui_controller.input_text, ios_session_id, text)
        
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
async def ios_press_button(ios_session_id: str, button: str) -> Dict:
    """Press button."""
    try:
        if not await simple_session_validation(ios_session_id):
            return ErrorResult(error=f"Session {ios_session_id} is invalid").model_dump()
        
        ui_controller = await get_manager_for_session(ios_session_id, UnifiedUIController)
        await run_sync(ui_controller.press_button, ios_session_id, button)
        
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
    ios_session_id: str,
    output_path: Optional[str] = None
) -> Dict:
    """Take screenshot."""
    try:
        if not await simple_session_validation(ios_session_id):
            return ErrorResult(error=f"Session {ios_session_id} is invalid").model_dump()
        
        ui_controller = await get_manager_for_session(ios_session_id, UnifiedUIController)
        
        # Generate path if not provided
        if not output_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"screenshot_{timestamp}.png"
        
        result = await run_sync(ui_controller.take_screenshot, ios_session_id, output_path)
        
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
    ios_session_id: str,
    output_path: str,
    duration: int = 10,
    quality: Optional[str] = None
) -> Dict:
    """Record video."""
    try:
        if not await simple_session_validation(ios_session_id):
            return ErrorResult(error=f"Session {ios_session_id} is invalid").model_dump()
        
        ui_controller = await get_manager_for_session(ios_session_id, UnifiedUIController)
        
        options = {}
        if quality:
            options['quality'] = quality
        
        result = await run_sync(
            ui_controller.record_video,
            ios_session_id,
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
async def ios_get_screen_info(ios_session_id: str) -> Dict:
    """Get screen info."""
    try:
        if not await simple_session_validation(ios_session_id):
            return ErrorResult(error=f"Session {ios_session_id} is invalid").model_dump()
        
        ui_controller = await get_manager_for_session(ios_session_id, UnifiedUIController)
        screen_info = await run_sync(ui_controller.get_screen_info, ios_session_id)
        
        return ScreenInfo(
            width=screen_info.width,
            height=screen_info.height,
            scale=screen_info.scale,
            orientation=screen_info.orientation
        ).model_dump()
    except Exception as e:
        return ErrorResult(error=str(e)).model_dump()

# ═══════════════════════════════════════════════════════════════════════════
# LOCATION & MEDIA - FIXED WITH ios_session_id PARAMETER
# ═══════════════════════════════════════════════════════════════════════════

@mcp_tool(
    name="ios_set_location",
    description="Set GPS location on iOS device",
    timeout=15
)
async def ios_set_location(
    ios_session_id: str,
    latitude: float,
    longitude: float,
    altitude: Optional[float] = None
) -> Dict:
    """Set location."""
    try:
        if not await simple_session_validation(ios_session_id):
            return ErrorResult(error=f"Session {ios_session_id} is invalid").model_dump()
        
        media_manager = await get_manager_for_session(ios_session_id, UnifiedMediaManager)
        await run_sync(media_manager.set_location, ios_session_id, latitude, longitude, altitude)
        
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
async def ios_set_location_by_name(ios_session_id: str, location_name: str) -> Dict:
    """Set location by name."""
    try:
        if not await simple_session_validation(ios_session_id):
            return ErrorResult(error=f"Session {ios_session_id} is invalid").model_dump()
        
        media_manager = await get_manager_for_session(ios_session_id, UnifiedMediaManager)
        await run_sync(media_manager.set_location_by_name, ios_session_id, location_name)
        
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
async def ios_add_media(ios_session_id: str, media_paths: List[str]) -> Dict:
    """Add media."""
    try:
        if not await simple_session_validation(ios_session_id):
            return ErrorResult(error=f"Session {ios_session_id} is invalid").model_dump()
        
        media_manager = await get_manager_for_session(ios_session_id, UnifiedMediaManager)
        added_files = await run_sync(media_manager.add_media, ios_session_id, media_paths)
        
        return MediaOperationResult(
            success=True,
            files_processed=len(added_files),
            files_failed=len(media_paths) - len(added_files),
            message=f"Added {len(added_files)} media files"
        ).model_dump()
    except Exception as e:
        return ErrorResult(error=str(e)).model_dump()

# ═══════════════════════════════════════════════════════════════════════════
# UTILITIES - FIXED WITH ios_session_id PARAMETER
# ═══════════════════════════════════════════════════════════════════════════

@mcp_tool(
    name="ios_open_url",
    description="Open URL in Safari on iOS device",
    timeout=20
)
async def ios_open_url(ios_session_id: str, url: str) -> Dict:
    """Open URL with renamed session parameter to avoid MCP validation."""
    try:
        print(f"🌐 Opening URL: {url} on session: {ios_session_id}")
        
        # Simple validation using singleton manager
        if not await simple_session_validation(ios_session_id):
            return ErrorResult(error=f"Session {ios_session_id} is invalid").model_dump()
        
        print(f"✅ Session {ios_session_id} validated in singleton manager")
        
        # Get utilities manager using singleton
        unified_manager = get_unified_session_manager()
        utilities = UnifiedUtilitiesManager()
        utilities.set_session_manager(unified_manager)
        
        print(f"🔧 Utilities manager configured with singleton")
        
        # Open URL
        await run_sync(utilities.open_url, ios_session_id, url)
        
        print(f"✅ Successfully opened URL: {url}")
        
        return OperationResult(
            success=True,
            message=f"Opened {url}"
        ).model_dump()
        
    except Exception as e:
        print(f"❌ ios_open_url failed: {e}")
        return ErrorResult(error=str(e)).model_dump()

@mcp_tool(
    name="ios_get_logs",
    description="Get system or app logs from iOS device",
    timeout=30
)
async def ios_get_logs(
    ios_session_id: str,
    bundle_id: Optional[str] = None,
    since: Optional[str] = None,
    limit: int = 100
) -> Dict:
    """Get logs."""
    try:
        if not await simple_session_validation(ios_session_id):
            return ErrorResult(error=f"Session {ios_session_id} is invalid").model_dump()
        
        logger = await get_manager_for_session(ios_session_id, UnifiedLoggerManager)
        
        # Parse since timestamp if provided
        since_dt = None
        if since:
            since_dt = datetime.fromisoformat(since)
        
        # Create filter
        filter = LogFilter(bundle_id=bundle_id, since=since_dt)
        
        # Get logs
        logs = await run_sync(logger.get_logs, ios_session_id, filter, limit)
        
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
    ios_session_id: str,
    bundle_id: str,
    service: str,
    status: str
) -> Dict:
    """Set permission."""
    try:
        if not await simple_session_validation(ios_session_id):
            return ErrorResult(error=f"Session {ios_session_id} is invalid").model_dump()
        
        utilities = await get_manager_for_session(ios_session_id, UnifiedUtilitiesManager)
        await run_sync(utilities.set_permission, ios_session_id, bundle_id, service, status)
        
        return OperationResult(
            success=True,
            message=f"Set {service} permission to {status} for {bundle_id}"
        ).model_dump()
    except Exception as e:
        return ErrorResult(error=str(e)).model_dump()

@mcp_tool(
    name="ios_focus_simulator",
    description="Focus simulator window (simulators only)",
    timeout=10
)
async def ios_focus_simulator(ios_session_id: str) -> Dict:
    """Focus simulator."""
    try:
        if not await simple_session_validation(ios_session_id):
            return ErrorResult(error=f"Session {ios_session_id} is invalid").model_dump()
        
        utilities = await get_manager_for_session(ios_session_id, UnifiedUtilitiesManager)
        await run_sync(utilities.focus_simulator, ios_session_id)
        
        return OperationResult(
            success=True,
            message="Simulator window focused"
        ).model_dump()
    except Exception as e:
        return ErrorResult(error=str(e)).model_dump()