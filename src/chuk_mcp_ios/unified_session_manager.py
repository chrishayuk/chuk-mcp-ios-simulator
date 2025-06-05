#!/usr/bin/env python3
# chuk_mcp/unified_session_manager.py
#!/usr/bin/env python3
"""
Unified Session Manager Module
Enhanced session management supporting both simulators and real iOS devices.
"""

import time
from typing import Dict, List, Optional, Union
from dataclasses import dataclass
from device_detector import DeviceDetector, DeviceType, UnifiedDeviceInfo
from ios_simulator_base import (
    SessionManagerInterface, 
    CommandExecutor, 
    SessionNotFoundError
)

@dataclass
class UnifiedSessionConfig:
    """Enhanced session configuration for both simulators and real devices."""
    device_name: Optional[str] = None
    device_udid: Optional[str] = None
    platform_version: Optional[str] = None
    device_type: Optional[DeviceType] = None
    autoboot: bool = True  # Only applies to simulators
    wait_for_connection: bool = True  # For real devices
    developer_team_id: Optional[str] = None  # For real device development
    require_unlocked: bool = True  # For real devices

class UnifiedSessionManager(CommandExecutor, SessionManagerInterface):
    """
    Enhanced session manager supporting both iOS simulators and real devices.
    Provides unified interface for device session management.
    """
    
    def __init__(self):
        super().__init__()
        self.device_detector = DeviceDetector()
        self.sessions: Dict[str, str] = {}  # sessionId -> udid
        self.session_counter = 0
        self.session_metadata: Dict[str, Dict] = {}
    
    def create_session(self, config: Optional[UnifiedSessionConfig] = None) -> str:
        """
        Create a new device session (simulator or real device).
        
        Args:
            config: Optional session configuration
            
        Returns:
            str: The created session ID
            
        Raises:
            Exception: If no suitable device is found or session creation fails
        """
        if config is None:
            config = UnifiedSessionConfig()
        
        # Find target device
        target_device = self._find_target_device(config)
        if not target_device:
            raise Exception("No suitable device found for session creation")
        
        # Prepare device based on type
        if target_device.device_type == DeviceType.SIMULATOR:
            self._prepare_simulator(target_device, config)
        else:
            self._prepare_real_device(target_device, config)
        
        # Create session
        session_id = self._generate_session_id()
        self.sessions[session_id] = target_device.udid
        
        # Store enhanced metadata
        self.session_metadata[session_id] = {
            "created_at": time.time(),
            "config": config,
            "udid": target_device.udid,
            "device_type": target_device.device_type.value,
            "device_name": target_device.name,
            "os_version": target_device.os_version,
            "connection_type": target_device.connection_type,
            "capabilities": self.device_detector.get_device_capabilities(target_device.udid)
        }
        
        return session_id
    
    def _find_target_device(self, config: UnifiedSessionConfig) -> Optional[UnifiedDeviceInfo]:
        """Find the target device based on configuration."""
        all_devices = self.device_detector.discover_all_devices(refresh_cache=True)
        
        # Filter by UDID if specified
        if config.device_udid:
            device = self.device_detector.find_device_by_udid(config.device_udid)
            if device and (not config.device_type or device.device_type == config.device_type):
                return device
            return None
        
        # Filter by name and other criteria
        candidates = []
        for device in all_devices:
            # Filter by device type
            if config.device_type and device.device_type != config.device_type:
                continue
            
            # Filter by name
            if config.device_name and device.name != config.device_name:
                continue
            
            # Filter by OS version
            if config.platform_version and config.platform_version not in device.os_version:
                continue
            
            # Filter by availability
            if not device.is_available:
                continue
            
            candidates.append(device)
        
        if not candidates:
            return None
        
        # Prioritize connected/booted devices
        connected = [d for d in candidates if d.state in ['Booted', 'Connected']]
        if connected:
            return connected[0]
        
        # Return first available candidate
        return candidates[0]
    
    def _prepare_simulator(self, device: UnifiedDeviceInfo, config: UnifiedSessionConfig):
        """Prepare a simulator for the session."""
        if config.autoboot and device.state != 'Booted':
            print(f"Booting simulator: {device.name}")
            try:
                self.run_command(f"{self.simctl_path} boot {device.udid}")
                
                # Wait for boot completion
                timeout = 30
                attempts = 0
                while attempts < timeout:
                    # Refresh device state
                    updated_device = self.device_detector.find_device_by_udid(device.udid)
                    if updated_device and updated_device.state == 'Booted':
                        print(f"✅ Simulator {device.name} booted successfully")
                        time.sleep(2)  # Allow full initialization
                        return
                    time.sleep(1)
                    attempts += 1
                
                raise Exception(f"Timeout waiting for simulator {device.udid} to boot")
            except Exception as e:
                raise Exception(f"Failed to boot simulator {device.name}: {str(e)}")
    
    def _prepare_real_device(self, device: UnifiedDeviceInfo, config: UnifiedSessionConfig):
        """Prepare a real device for the session."""
        if config.wait_for_connection and device.state != 'Connected':
            print(f"Waiting for device connection: {device.name}")
            if not self.device_detector.wait_for_device_connection(device.udid, timeout=30):
                raise Exception(f"Device {device.name} did not connect within timeout")
        
        # Verify device is accessible
        try:
            # Try to get device info via idb
            result = self.run_command(f"{self.idb_path} describe --udid {device.udid} --json", timeout=10)
            device_info = result.stdout
            print(f"✅ Real device {device.name} is accessible")
        except Exception as e:
            print(f"⚠️  Warning: Could not verify device accessibility: {e}")
            print("   Make sure the device is unlocked and trusted")
    
    def terminate_session(self, session_id: str) -> None:
        """Terminate a device session."""
        if session_id not in self.sessions:
            raise SessionNotFoundError(f"Session not found: {session_id}")
        
        # Get session metadata
        metadata = self.session_metadata.get(session_id, {})
        device_type = metadata.get("device_type")
        
        # Perform device-specific cleanup
        if device_type == DeviceType.SIMULATOR.value:
            # Simulator-specific cleanup could go here
            pass
        elif device_type == DeviceType.REAL_DEVICE.value:
            # Real device-specific cleanup could go here
            pass
        
        # Clean up session data
        del self.sessions[session_id]
        if session_id in self.session_metadata:
            del self.session_metadata[session_id]
    
    def list_sessions(self) -> List[str]:
        """List all active device sessions."""
        return list(self.sessions.keys())
    
    def get_udid_from_session(self, session_id: str) -> str:
        """Get UDID from session ID."""
        if session_id not in self.sessions:
            raise SessionNotFoundError(f"Session not found: {session_id}")
        return self.sessions[session_id]
    
    def get_session_info(self, session_id: str) -> Dict:
        """Get detailed session information."""
        if session_id not in self.sessions:
            raise SessionNotFoundError(f"Session not found: {session_id}")
        
        metadata = self.session_metadata.get(session_id, {})
        udid = self.sessions[session_id]
        
        # Get current device state
        current_device = self.device_detector.find_device_by_udid(udid)
        
        return {
            "session_id": session_id,
            "udid": udid,
            "device_name": metadata.get("device_name", "Unknown"),
            "device_type": metadata.get("device_type", "unknown"),
            "os_version": metadata.get("os_version", "Unknown"),
            "connection_type": metadata.get("connection_type", "unknown"),
            "created_at": metadata.get("created_at"),
            "current_state": current_device.state if current_device else "Unknown",
            "capabilities": metadata.get("capabilities", {}),
            "is_available": current_device.is_available if current_device else False
        }
    
    def get_device_type(self, session_id: str) -> DeviceType:
        """Get the device type for a session."""
        metadata = self.session_metadata.get(session_id, {})
        device_type_str = metadata.get("device_type", "")
        return DeviceType(device_type_str) if device_type_str else DeviceType.SIMULATOR
    
    def is_real_device_session(self, session_id: str) -> bool:
        """Check if session is for a real device."""
        return self.get_device_type(session_id) == DeviceType.REAL_DEVICE
    
    def is_simulator_session(self, session_id: str) -> bool:
        """Check if session is for a simulator."""
        return self.get_device_type(session_id) == DeviceType.SIMULATOR
    
    def get_session_capabilities(self, session_id: str) -> Dict[str, bool]:
        """Get capabilities for a session."""
        metadata = self.session_metadata.get(session_id, {})
        return metadata.get("capabilities", {})
    
    def validate_session(self, session_id: str) -> bool:
        """Validate that a session exists and device is accessible."""
        if session_id not in self.sessions:
            return False
        
        udid = self.sessions[session_id]
        device = self.device_detector.find_device_by_udid(udid)
        
        if not device:
            return False
        
        # Check if device is accessible
        if device.device_type == DeviceType.SIMULATOR:
            return device.state == 'Booted'
        else:  # Real device
            return device.state == 'Connected'
    
    def create_simulator_session(self, device_name: Optional[str] = None, 
                                platform_version: Optional[str] = None, 
                                autoboot: bool = True) -> str:
        """Create a simulator-specific session (backward compatibility)."""
        config = UnifiedSessionConfig(
            device_name=device_name,
            platform_version=platform_version,
            device_type=DeviceType.SIMULATOR,
            autoboot=autoboot
        )
        return self.create_session(config)
    
    def create_real_device_session(self, device_name: Optional[str] = None,
                                  device_udid: Optional[str] = None,
                                  wait_for_connection: bool = True) -> str:
        """Create a real device-specific session."""
        config = UnifiedSessionConfig(
            device_name=device_name,
            device_udid=device_udid,
            device_type=DeviceType.REAL_DEVICE,
            wait_for_connection=wait_for_connection
        )
        return self.create_session(config)
    
    def create_any_available_session(self, prefer_real_device: bool = False) -> str:
        """Create a session with any available device."""
        # Get all connected/booted devices
        devices = self.device_detector.get_connected_devices()
        
        if not devices:
            raise Exception("No connected devices available")
        
        # Choose device based on preference
        if prefer_real_device:
            real_devices = [d for d in devices if d.device_type == DeviceType.REAL_DEVICE]
            if real_devices:
                target_device = real_devices[0]
            else:
                target_device = devices[0]
        else:
            # Prefer simulators
            simulators = [d for d in devices if d.device_type == DeviceType.SIMULATOR]
            if simulators:
                target_device = simulators[0]
            else:
                target_device = devices[0]
        
        config = UnifiedSessionConfig(
            device_udid=target_device.udid,
            device_type=target_device.device_type
        )
        return self.create_session(config)
    
    def _generate_session_id(self) -> str:
        """Generate a unique session ID."""
        session_id = f"session_{int(time.time())}_{self.session_counter}"
        self.session_counter += 1
        return session_id
    
    def print_sessions_status(self):
        """Print detailed status of all sessions."""
        sessions = self.list_sessions()
        
        print(f"\n📱 Session Status ({len(sessions)} active):")
        print("=" * 60)
        
        if not sessions:
            print("No active sessions")
            return
        
        for session_id in sessions:
            try:
                info = self.get_session_info(session_id)
                device_type_emoji = "📱" if info['device_type'] == 'real_device' else "🖥️"
                state_emoji = "🟢" if info['current_state'] in ['Booted', 'Connected'] else "🔴"
                
                print(f"\n{device_type_emoji} {session_id}")
                print(f"   {state_emoji} {info['device_name']} ({info['device_type']})")
                print(f"   UDID: {info['udid']}")
                print(f"   OS: {info['os_version']}")
                print(f"   Connection: {info['connection_type']}")
                print(f"   State: {info['current_state']}")
                
                # Show capabilities
                capabilities = info.get('capabilities', {})
                enabled_caps = [k.replace('can_', '').replace('_', ' ') for k, v in capabilities.items() if v]
                if enabled_caps:
                    print(f"   Capabilities: {', '.join(enabled_caps[:3])}{'...' if len(enabled_caps) > 3 else ''}")
                
            except Exception as e:
                print(f"❌ {session_id} (Error: {e})")
    
    def cleanup_inactive_sessions(self, max_age_hours: int = 24) -> List[str]:
        """
        Clean up sessions that have been inactive for too long.
        
        Args:
            max_age_hours: Maximum age in hours before cleanup
            
        Returns:
            List[str]: List of cleaned up session IDs
        """
        current_time = time.time()
        max_age_seconds = max_age_hours * 3600
        cleaned_sessions = []
        
        for session_id, metadata in list(self.session_metadata.items()):
            created_at = metadata.get("created_at", 0)
            if current_time - created_at > max_age_seconds:
                try:
                    self.terminate_session(session_id)
                    cleaned_sessions.append(session_id)
                except Exception:
                    pass  # Session already cleaned up
        
        return cleaned_sessions
    
    def get_sessions_by_device_type(self, device_type: DeviceType) -> List[str]:
        """Get all session IDs for a specific device type."""
        matching_sessions = []
        for session_id, metadata in self.session_metadata.items():
            if metadata.get("device_type") == device_type.value:
                matching_sessions.append(session_id)
        return matching_sessions
    
    def get_real_device_sessions(self) -> List[str]:
        """Get all real device session IDs."""
        return self.get_sessions_by_device_type(DeviceType.REAL_DEVICE)
    
    def get_simulator_sessions(self) -> List[str]:
        """Get all simulator session IDs."""
        return self.get_sessions_by_device_type(DeviceType.SIMULATOR)
    
    def terminate_sessions_by_device_type(self, device_type: DeviceType) -> List[str]:
        """Terminate all sessions for a specific device type."""
        session_ids = self.get_sessions_by_device_type(device_type)
        terminated = []
        
        for session_id in session_ids:
            try:
                self.terminate_session(session_id)
                terminated.append(session_id)
            except Exception as e:
                print(f"Failed to terminate session {session_id}: {e}")
        
        return terminated
    
    def get_session_device_info(self, session_id: str) -> Optional[Dict]:
        """Get current device information for a session."""
        if session_id not in self.sessions:
            return None
        
        udid = self.sessions[session_id]
        device = self.device_detector.find_device_by_udid(udid)
        
        if not device:
            return None
        
        return {
            "udid": device.udid,
            "name": device.name,
            "state": device.state,
            "device_type": device.device_type.value,
            "os_version": device.os_version,
            "model": device.model,
            "connection_type": device.connection_type,
            "architecture": device.architecture,
            "is_available": device.is_available
        }
    
    def refresh_session_status(self, session_id: str) -> bool:
        """
        Refresh and validate session status.
        
        Args:
            session_id: Session ID to refresh
            
        Returns:
            bool: True if session is still valid
        """
        if session_id not in self.sessions:
            return False
        
        # Force refresh device detection cache
        self.device_detector.discover_all_devices(refresh_cache=True)
        
        # Validate session is still accessible
        return self.validate_session(session_id)
    
    def export_session_info(self, output_file: str) -> None:
        """Export all session information to a JSON file."""
        import json
        
        session_data = {
            "export_timestamp": time.time(),
            "total_sessions": len(self.sessions),
            "sessions": {}
        }
        
        for session_id in self.sessions:
            try:
                session_data["sessions"][session_id] = self.get_session_info(session_id)
            except Exception as e:
                session_data["sessions"][session_id] = {"error": str(e)}
        
        with open(output_file, 'w') as f:
            json.dump(session_data, f, indent=2)
        
        print(f"📄 Session info exported to: {output_file}")
    
    def create_automation_session(self, prefer_device_type: Optional[DeviceType] = None) -> str:
        """
        Create a session optimized for automation.
        
        Args:
            prefer_device_type: Preferred device type (simulator or real device)
            
        Returns:
            str: Created session ID
        """
        # Get connected devices
        connected_devices = self.device_detector.get_connected_devices()
        
        if not connected_devices:
            # Try to boot a simulator if no devices are connected
            simulators = self.device_detector.get_simulators_only()
            if simulators:
                # Find an iPhone simulator
                iphone_sims = [s for s in simulators if 'iPhone' in s.name and s.is_available]
                if iphone_sims:
                    config = UnifiedSessionConfig(
                        device_udid=iphone_sims[0].udid,
                        device_type=DeviceType.SIMULATOR,
                        autoboot=True
                    )
                    return self.create_session(config)
            
            raise Exception("No devices available for automation session")
        
        # Filter by preference
        if prefer_device_type:
            filtered_devices = [d for d in connected_devices if d.device_type == prefer_device_type]
            if filtered_devices:
                target_device = filtered_devices[0]
            else:
                target_device = connected_devices[0]  # Fallback to any device
        else:
            # Default preference: simulators for easier automation
            simulators = [d for d in connected_devices if d.device_type == DeviceType.SIMULATOR]
            target_device = simulators[0] if simulators else connected_devices[0]
        
        config = UnifiedSessionConfig(
            device_udid=target_device.udid,
            device_type=target_device.device_type
        )
        
        session_id = self.create_session(config)
        
        print(f"🤖 Automation session created:")
        print(f"   Session ID: {session_id}")
        print(f"   Device: {target_device.name} ({target_device.device_type.value})")
        print(f"   OS: {target_device.os_version}")
        
        return session_id