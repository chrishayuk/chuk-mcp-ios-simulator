"""chuk_mcp_ios_simulator.tools

Comprehensive iOS Simulator MCP tools - pure iOS automation focus.
"""

import os
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime

from pydantic import ValidationError
from chuk_mcp_runtime.common.mcp_tool_decorator import mcp_tool

from .models import *

# Import iOS simulator modules
from simple_demo import SimpleiOSController

# Global controller instances
_controller: Optional[SimpleiOSController] = None
_simple_controller: Optional[SimpleiOSController] = None

def get_controller() -> SimpleiOSController:
    # """Get main iOS simulator controller."""
    # global _controller
    # if _controller is None:
    #     _controller = iOSSimulatorController()
    # return _controller
    """Get simple iOS simulator controller (simctl only)."""
    global _simple_controller
    if _simple_controller is None:
        _simple_controller = SimpleiOSController()
    return _simple_controller

def get_simple_controller() -> SimpleiOSController:
    """Get simple iOS simulator controller (simctl only)."""
    global _simple_controller
    if _simple_controller is None:
        _simple_controller = SimpleiOSController()
    return _simple_controller

async def run_sync(func, *args, **kwargs):
    """Run sync function in thread pool."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, func, *args, **kwargs)

# ═══════════════════════════════════════════════════════════════════════════
# SESSION MANAGEMENT
# ═══════════════════════════════════════════════════════════════════════════

@mcp_tool(
    name="ios_create_session",
    description="Create new iOS simulator session",
    timeout=30
)
async def ios_create_session(device_name: Optional[str] = None, autoboot: bool = True) -> Dict:
    """Create iOS simulator session with device selection."""
    try:
        controller = get_controller()
        session_id = await run_sync(controller.create_session, device_name, None, autoboot)
        session_info = await run_sync(controller.get_session_info, session_id)
        
        return CreateSessionResult(
            session_id=session_id,
            device_name=session_info.get('device_name', 'Unknown'),
            udid=session_info.get('udid', '')
        ).model_dump()
    except Exception as e:
        return {"error": str(e)}

@mcp_tool(
    name="ios_list_sessions", 
    description="List active iOS simulator sessions",
    timeout=10
)
async def ios_list_sessions() -> Dict:
    """List all active simulator sessions."""
    try:
        controller = get_controller()
        sessions = await run_sync(controller.list_sessions)
        
        session_details = []
        for session_id in sessions:
            info = await run_sync(controller.get_session_info, session_id)
            session_details.append(SessionInfoResult(
                session_id=session_id,
                device_name=info.get('device_name', 'Unknown'),
                udid=info.get('udid', ''),
                state=info.get('current_state', 'Unknown')
            ))
        
        return {"sessions": [s.model_dump() for s in session_details]}
    except Exception as e:
        return {"error": str(e)}

@mcp_tool(
    name="ios_terminate_session",
    description="Terminate iOS simulator session", 
    timeout=15
)
async def ios_terminate_session(session_id: str) -> Dict:
    """Terminate simulator session."""
    try:
        controller = get_controller()
        await run_sync(controller.terminate_session, session_id)
        return OperationResult(success=True, message=f"Session {session_id} terminated").model_dump()
    except Exception as e:
        return {"error": str(e)}

# ═══════════════════════════════════════════════════════════════════════════
# DEVICE MANAGEMENT
# ═══════════════════════════════════════════════════════════════════════════

@mcp_tool(
    name="ios_list_devices",
    description="List available iOS simulators",
    timeout=15
)
async def ios_list_devices() -> Dict:
    """List all available iOS simulators."""
    try:
        simple_controller = get_simple_controller()
        devices = await run_sync(simple_controller.list_simulators)
        booted = await run_sync(simple_controller.get_booted_simulators)
        
        return ListDevicesResult(
            devices=devices,
            total_count=len(devices),
            booted_count=len(booted)
        ).model_dump()
    except Exception as e:
        return {"error": str(e)}

@mcp_tool(
    name="ios_boot_device",
    description="Boot iOS simulator by UDID",
    timeout=60
)
async def ios_boot_device(udid: str) -> Dict:
    """Boot iOS simulator."""
    try:
        simple_controller = get_simple_controller()
        success = await run_sync(simple_controller.boot_simulator, udid)
        
        return DeviceOperationResult(
            success=success,
            message=f"Device {udid[:8]}... {'booted' if success else 'failed to boot'}"
        ).model_dump()
    except Exception as e:
        return {"error": str(e)}

@mcp_tool(
    name="ios_shutdown_device", 
    description="Shutdown iOS simulator by UDID",
    timeout=30
)
async def ios_shutdown_device(udid: str) -> Dict:
    """Shutdown iOS simulator."""
    try:
        simple_controller = get_simple_controller()
        success = await run_sync(simple_controller.shutdown_simulator, udid)
        
        return DeviceOperationResult(
            success=success,
            message=f"Device {udid[:8]}... {'shutdown' if success else 'failed to shutdown'}"
        ).model_dump()
    except Exception as e:
        return {"error": str(e)}

# ═══════════════════════════════════════════════════════════════════════════
# APP MANAGEMENT  
# ═══════════════════════════════════════════════════════════════════════════

@mcp_tool(
    name="ios_install_app",
    description="Install app on iOS simulator",
    timeout=120
)
async def ios_install_app(session_id: str, app_path: str) -> Dict:
    """Install app on simulator."""
    try:
        controller = get_controller()
        app_info = await run_sync(controller.install_app, session_id, app_path)
        
        return {
            "success": True,
            "app_info": app_info.model_dump() if hasattr(app_info, 'model_dump') else app_info
        }
    except Exception as e:
        return {"error": str(e)}

@mcp_tool(
    name="ios_launch_app",
    description="Launch app on iOS simulator",
    timeout=30
)
async def ios_launch_app(session_id: str, bundle_id: str) -> Dict:
    """Launch app by bundle ID."""
    try:
        # Try with full controller first
        try:
            controller = get_controller()
            await run_sync(controller.launch_app, session_id, bundle_id)
        except:
            # Fallback to simple controller with session UDID
            controller = get_controller()
            udid = controller.session_manager.get_udid_from_session(session_id)
            simple_controller = get_simple_controller()
            await run_sync(simple_controller.launch_app, udid, bundle_id)
        
        return OperationResult(success=True, message=f"Launched {bundle_id}").model_dump()
    except Exception as e:
        return {"error": str(e)}

@mcp_tool(
    name="ios_list_apps",
    description="List installed apps on iOS simulator",
    timeout=20
)
async def ios_list_apps(session_id: str, user_apps_only: bool = True) -> Dict:
    """List installed apps."""
    try:
        controller = get_controller()
        apps = await run_sync(controller.list_apps, session_id, user_apps_only)
        
        app_list = []
        for app in apps:
            if hasattr(app, 'model_dump'):
                app_list.append(app.model_dump())
            else:
                app_list.append(app)
        
        return ListAppsResult(apps=app_list, total_count=len(app_list)).model_dump()
    except Exception as e:
        return {"error": str(e)}

@mcp_tool(
    name="ios_terminate_app",
    description="Terminate app on iOS simulator", 
    timeout=15
)
async def ios_terminate_app(session_id: str, bundle_id: str) -> Dict:
    """Terminate running app."""
    try:
        controller = get_controller()
        await run_sync(controller.terminate_app, session_id, bundle_id)
        return OperationResult(success=True, message=f"Terminated {bundle_id}").model_dump()
    except Exception as e:
        return {"error": str(e)}

# ═══════════════════════════════════════════════════════════════════════════
# UI INTERACTIONS
# ═══════════════════════════════════════════════════════════════════════════

@mcp_tool(
    name="ios_tap",
    description="Tap at coordinates on iOS simulator",
    timeout=10
)
async def ios_tap(session_id: str, x: int, y: int) -> Dict:
    """Simulate tap gesture."""
    try:
        controller = get_controller()
        await run_sync(controller.tap, session_id, x, y)
        return OperationResult(success=True, message=f"Tapped at ({x}, {y})").model_dump()
    except Exception as e:
        return {"error": str(e)}

@mcp_tool(
    name="ios_swipe",
    description="Swipe gesture on iOS simulator",
    timeout=10
)
async def ios_swipe(session_id: str, start_x: int, start_y: int, end_x: int, end_y: int, duration: int = 100) -> Dict:
    """Simulate swipe gesture."""
    try:
        controller = get_controller()
        await run_sync(controller.swipe, session_id, start_x, start_y, end_x, end_y, duration)
        return OperationResult(success=True, message=f"Swiped from ({start_x}, {start_y}) to ({end_x}, {end_y})").model_dump()
    except Exception as e:
        return {"error": str(e)}

@mcp_tool(
    name="ios_input_text",
    description="Input text on iOS simulator",
    timeout=15
)
async def ios_input_text(session_id: str, text: str) -> Dict:
    """Input text into focused field."""
    try:
        controller = get_controller()
        await run_sync(controller.input_text, session_id, text)
        return OperationResult(success=True, message=f"Input text: {text}").model_dump()
    except Exception as e:
        return {"error": str(e)}

@mcp_tool(
    name="ios_press_button",
    description="Press hardware button on iOS simulator",
    timeout=10
)
async def ios_press_button(session_id: str, button: str) -> Dict:
    """Press hardware button (home, lock, volume_up, volume_down)."""
    try:
        controller = get_controller()
        await run_sync(controller.press_button, session_id, button)
        return OperationResult(success=True, message=f"Pressed {button} button").model_dump()
    except Exception as e:
        return {"error": str(e)}

# ═══════════════════════════════════════════════════════════════════════════
# SCREENSHOTS
# ═══════════════════════════════════════════════════════════════════════════

@mcp_tool(
    name="ios_screenshot",
    description="Take screenshot of iOS simulator",
    timeout=20
)
async def ios_screenshot(session_id: str, output_path: Optional[str] = None) -> Dict:
    """Take simulator screenshot."""
    try:
        # Try full controller first
        try:
            controller = get_controller()
            result = await run_sync(controller.take_screenshot, session_id, output_path)
        except:
            # Fallback to simple controller
            controller = get_controller()
            udid = controller.session_manager.get_udid_from_session(session_id)
            simple_controller = get_simple_controller()
            
            if not output_path:
                output_path = f"screenshot_{int(datetime.now().timestamp())}.png"
            
            success = await run_sync(simple_controller.take_screenshot, udid, output_path)
            result = output_path if success else None
        
        if result:
            file_size = os.path.getsize(result) if isinstance(result, str) and os.path.exists(result) else None
            return ScreenshotResult(
                success=True,
                file_path=result if isinstance(result, str) else output_path,
                timestamp=datetime.now().isoformat()
            ).model_dump()
        else:
            return {"error": "Screenshot failed"}
            
    except Exception as e:
        return {"error": str(e)}

# ═══════════════════════════════════════════════════════════════════════════
# LOCATION & MEDIA
# ═══════════════════════════════════════════════════════════════════════════

@mcp_tool(
    name="ios_set_location",
    description="Set GPS location on iOS simulator",
    timeout=15
)
async def ios_set_location(session_id: str, latitude: float, longitude: float) -> Dict:
    """Set simulator GPS location."""
    try:
        # Try full controller first
        try:
            controller = get_controller()
            await run_sync(controller.set_location, session_id, latitude, longitude)
        except:
            # Fallback to simple controller
            controller = get_controller()
            udid = controller.session_manager.get_udid_from_session(session_id)
            simple_controller = get_simple_controller()
            await run_sync(simple_controller.set_location, udid, latitude, longitude)
        
        return OperationResult(success=True, message=f"Location set to {latitude}, {longitude}").model_dump()
    except Exception as e:
        return {"error": str(e)}

@mcp_tool(
    name="ios_add_media", 
    description="Add media files to iOS simulator",
    timeout=30
)
async def ios_add_media(session_id: str, media_paths: List[str]) -> Dict:
    """Add media files to photo library."""
    try:
        # Validate files exist
        valid_paths = [path for path in media_paths if os.path.exists(path)]
        if not valid_paths:
            return {"error": "No valid media files found"}
        
        controller = get_controller()
        await run_sync(controller.add_media, session_id, valid_paths)
        
        return MediaOperationResult(
            success=True,
            files_processed=len(valid_paths),
            message=f"Added {len(valid_paths)} media files"
        ).model_dump()
    except Exception as e:
        return {"error": str(e)}

# ═══════════════════════════════════════════════════════════════════════════
# UTILITIES
# ═══════════════════════════════════════════════════════════════════════════

@mcp_tool(
    name="ios_open_url",
    description="Open URL in iOS Safari",
    timeout=20
)
async def ios_open_url(session_id: str, url: str) -> Dict:
    """Open URL in Safari."""
    try:
        # Try full controller first
        try:
            controller = get_controller()
            await run_sync(controller.open_url, session_id, url)
        except:
            # Fallback to simple controller
            controller = get_controller()
            udid = controller.session_manager.get_udid_from_session(session_id)
            simple_controller = get_simple_controller()
            await run_sync(simple_controller.open_url, udid, url)
        
        return OperationResult(success=True, message=f"Opened {url}").model_dump()
    except Exception as e:
        return {"error": str(e)}

@mcp_tool(
    name="ios_get_logs",
    description="Get system logs from iOS simulator",
    timeout=30
)
async def ios_get_logs(session_id: str, bundle_id: Optional[str] = None, limit: int = 100) -> Dict:
    """Get system or app logs."""
    try:
        controller = get_controller()
        logs = await run_sync(controller.get_system_logs, session_id, bundle_id, limit)
        
        entry_count = len(logs.split('\n')) if logs else 0
        return LogsResult(
            logs=logs,
            entry_count=entry_count
        ).model_dump()
    except Exception as e:
        return {"error": str(e)}

@mcp_tool(
    name="ios_approve_permissions",
    description="Approve app permissions on iOS simulator",
    timeout=20
)
async def ios_approve_permissions(session_id: str, bundle_id: str, permissions: List[str]) -> Dict:
    """Approve app permissions."""
    try:
        controller = get_controller()
        await run_sync(controller.approve_permissions, session_id, bundle_id, permissions)
        return OperationResult(success=True, message=f"Approved permissions for {bundle_id}").model_dump()
    except Exception as e:
        return {"error": str(e)}

@mcp_tool(
    name="ios_clear_keychain",
    description="Clear iOS simulator keychain",
    timeout=15
)
async def ios_clear_keychain(session_id: str) -> Dict:
    """Clear simulator keychain."""
    try:
        controller = get_controller()
        await run_sync(controller.clear_keychain, session_id)
        return OperationResult(success=True, message="Keychain cleared").model_dump()
    except Exception as e:
        return {"error": str(e)}

@mcp_tool(
    name="ios_focus_simulator",
    description="Focus iOS simulator window",
    timeout=10
)
async def ios_focus_simulator(session_id: str) -> Dict:
    """Focus simulator window."""
    try:
        controller = get_controller()
        await run_sync(controller.focus_simulator, session_id)
        return OperationResult(success=True, message="Simulator focused").model_dump()
    except Exception as e:
        return {"error": str(e)}