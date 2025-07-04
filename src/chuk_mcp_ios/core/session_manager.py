#!/usr/bin/env python3
# chuk_mcp_ios/core/session_manager.py
"""
Unified Session Manager for iOS Device Control

Manages device sessions for both simulators and real devices.
Provides session lifecycle management, tracking, and cleanup.

FIXED VERSION: Implements automatic cleanup, session limits, and better lifecycle management.
"""

import time
import secrets
import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path

from .base import (
    DeviceType,
    DeviceState,
    DeviceInfo,
    SessionInfo,
    SessionError,
    DeviceNotFoundError,
    DeviceNotAvailableError
)
from .device_manager import UnifiedDeviceManager

def generate_uuid4() -> str:
    """Generate a UUID4 string using secrets module to avoid uuid import issues."""
    # Generate 16 random bytes
    random_bytes = secrets.randbits(128)
    
    # Format as UUID4
    # Set version (4) in bits 12-15 of time_hi_and_version
    random_bytes &= ~(0xf000 << 48)  # Clear version bits
    random_bytes |= (0x4000 << 48)   # Set version to 4
    
    # Set variant bits (10) in bits 6-7 of clock_seq_hi_and_reserved
    random_bytes &= ~(0xc0 << 56)    # Clear variant bits
    random_bytes |= (0x80 << 56)     # Set variant to 10
    
    # Format as standard UUID string
    hex_string = f"{random_bytes:032x}"
    return f"{hex_string[:8]}-{hex_string[8:12]}-{hex_string[12:16]}-{hex_string[16:20]}-{hex_string[20:]}"

@dataclass
class SessionConfig:
    """Configuration for creating a new session."""
    device_name: Optional[str] = None
    device_udid: Optional[str] = None
    platform_version: Optional[str] = None
    device_type: Optional[DeviceType] = None
    autoboot: bool = True  # Auto-boot simulators
    wait_for_connection: bool = True  # Wait for real device connection
    prefer_available: bool = True  # Prefer already booted/connected devices
    session_name: Optional[str] = None  # Optional custom session name
    metadata: Optional[Dict[str, Any]] = None  # Custom metadata

class UnifiedSessionManager:
    """
    Manages device sessions with automatic lifecycle management.
    Supports both iOS simulators and real devices.
    Fixed version with automatic cleanup and session limits.
    """
    
    def __init__(self, session_dir: Optional[Path] = None, max_sessions: int = 10, auto_cleanup_hours: int = 6):
        """
        Initialize with automatic cleanup and session limits.
        
        Args:
            session_dir: Directory for session files
            max_sessions: Maximum number of concurrent sessions (default: 10)
            auto_cleanup_hours: Auto cleanup sessions older than this (default: 6 hours)
        """
        self.device_manager = UnifiedDeviceManager()
        self.sessions: Dict[str, SessionInfo] = {}
        self.session_dir = session_dir or Path.home() / ".ios-device-control" / "sessions"
        self.session_dir.mkdir(parents=True, exist_ok=True)
        self.max_sessions = max_sessions
        self.auto_cleanup_hours = auto_cleanup_hours
        
        # Clean up old sessions on startup
        self._cleanup_old_sessions_on_startup()
        
        # Load existing sessions with improved error handling
        self._load_sessions()
        
        # Enforce session limit
        self._enforce_session_limit()
    
    def create_session(self, config: Optional[SessionConfig] = None) -> str:
        """
        Create a new device session with automatic cleanup.
        
        Args:
            config: Session configuration
            
        Returns:
            str: Session ID
            
        Raises:
            SessionError: If maximum sessions reached
            DeviceNotFoundError: If no suitable device is found
            DeviceNotAvailableError: If device cannot be made available
        """
        # Check session limit
        if len(self.sessions) >= self.max_sessions:
            # Try to clean up old sessions first
            self.cleanup_inactive_sessions(max_age_hours=1)
            
            # Check again
            if len(self.sessions) >= self.max_sessions:
                raise SessionError(
                    f"Maximum sessions ({self.max_sessions}) reached. "
                    "Please terminate existing sessions first."
                )
        
        if config is None:
            config = SessionConfig()
        
        # Find or prepare device
        device = self._find_or_prepare_device(config)
        
        # Generate session ID
        session_id = self._generate_session_id(config.session_name)
        
        # Create session info
        session_info = SessionInfo(
            session_id=session_id,
            device_udid=device.udid,
            device_type=device.device_type,
            created_at=datetime.now(),
            metadata={
                'device_name': device.name,
                'os_version': device.os_version,
                'model': device.model,
                'connection_type': device.connection_type,
                'config': asdict(config),
                'custom_metadata': config.metadata or {}
            }
        )
        
        # Store session
        self.sessions[session_id] = session_info
        self._save_session(session_info)
        
        print(f"✅ Session created: {session_id}")
        print(f"   Device: {device.name} ({device.device_type.value})")
        print(f"   Active sessions: {len(self.sessions)}/{self.max_sessions}")
        
        return session_id
    
    def terminate_session(self, session_id: str) -> None:
        """
        Terminate a session with proper cleanup.
        
        Args:
            session_id: Session ID to terminate
            
        Raises:
            SessionError: If session not found
        """
        if session_id not in self.sessions:
            # Check if it's an old session file
            session_file = self.session_dir / f"{session_id}.json"
            if session_file.exists():
                session_file.unlink()
                print(f"✅ Cleaned up orphaned session file: {session_id}")
            else:
                raise SessionError(f"Session not found: {session_id}")
            return
        
        session_info = self.sessions[session_id]
        
        # Perform cleanup based on device type
        try:
            device = self.device_manager.get_device(session_info.device_udid)
            if device and device.device_type == DeviceType.SIMULATOR:
                # Optionally shutdown simulator if it was auto-booted
                config = session_info.metadata.get('config', {})
                if config.get('autoboot', False):
                    print(f"Shutting down auto-booted simulator...")
                    self.device_manager.shutdown_device(session_info.device_udid)
        except Exception as e:
            print(f"Warning: Cleanup failed: {e}")
        
        # Remove session
        del self.sessions[session_id]
        self._delete_session_file(session_id)
        
        print(f"✅ Session terminated: {session_id}")
        print(f"   Active sessions: {len(self.sessions)}/{self.max_sessions}")
    
    def get_session_info(self, session_id: str) -> Dict[str, Any]:
        """
        Get detailed session information.
        
        Args:
            session_id: Session ID
            
        Returns:
            Dict containing session details
            
        Raises:
            SessionError: If session not found
        """
        if session_id not in self.sessions:
            raise SessionError(f"Session not found: {session_id}")
        
        session_info = self.sessions[session_id]
        
        # Get current device state
        device = self.device_manager.get_device(session_info.device_udid)
        current_state = device.state.value if device else "unknown"
        
        # Calculate session age
        age = datetime.now() - session_info.created_at
        
        return {
            'session_id': session_id,
            'device_udid': session_info.device_udid,
            'device_type': session_info.device_type.value,
            'device_name': session_info.metadata.get('device_name', 'Unknown'),
            'os_version': session_info.metadata.get('os_version', 'Unknown'),
            'created_at': session_info.created_at.isoformat(),
            'age_seconds': age.total_seconds(),
            'current_state': current_state,
            'is_available': self.is_session_available(session_id),
            'metadata': session_info.metadata,
            'capabilities': self.device_manager.get_device_capabilities(session_info.device_udid)
        }
    
    def list_sessions(self) -> List[str]:
        """Get list of all session IDs."""
        return list(self.sessions.keys())
    
    def get_device_udid(self, session_id: str) -> str:
        """
        Get device UDID for a session.
        
        Args:
            session_id: Session ID
            
        Returns:
            str: Device UDID
            
        Raises:
            SessionError: If session not found
        """
        if session_id not in self.sessions:
            raise SessionError(f"Session not found: {session_id}")
        
        return self.sessions[session_id].device_udid
    
    def is_session_available(self, session_id: str) -> bool:
        """
        Check if session's device is available.
        
        Args:
            session_id: Session ID
            
        Returns:
            bool: True if device is available
        """
        try:
            udid = self.get_device_udid(session_id)
            return self.device_manager.is_device_available(udid)
        except:
            return False
    
    def wait_for_session(self, session_id: str, timeout: int = 30) -> bool:
        """
        Wait for session's device to become available.
        
        Args:
            session_id: Session ID
            timeout: Timeout in seconds
            
        Returns:
            bool: True if device became available
        """
        try:
            udid = self.get_device_udid(session_id)
            return self.device_manager.wait_for_device(udid, timeout)
        except:
            return False
    
    def create_automation_session(self, config: Optional[Dict[str, Any]] = None) -> str:
        """
        Create a session optimized for automation.
        
        Args:
            config: Optional configuration overrides
            
        Returns:
            str: Session ID
        """
        session_config = SessionConfig(
            prefer_available=True,
            autoboot=True,
            wait_for_connection=True,
            session_name="automation",
            metadata={'purpose': 'automation'}
        )
        
        # Apply config overrides
        if config:
            for key, value in config.items():
                if hasattr(session_config, key):
                    setattr(session_config, key, value)
        
        return self.create_session(session_config)
    
    def create_quick_session(self, device_name: Optional[str] = None) -> str:
        """
        Create a quick session with minimal configuration.
        
        Args:
            device_name: Optional device name
            
        Returns:
            str: Session ID
        """
        config = SessionConfig(
            device_name=device_name,
            prefer_available=True,
            autoboot=True
        )
        
        return self.create_session(config)
    
    def cleanup_inactive_sessions(self, max_age_hours: int = 24) -> List[str]:
        """
        Clean up inactive sessions older than specified age.
        
        Args:
            max_age_hours: Maximum age in hours
            
        Returns:
            List[str]: Cleaned up session IDs
        """
        current_time = datetime.now()
        max_age_seconds = max_age_hours * 3600
        cleaned = []
        
        for session_id, session_info in list(self.sessions.items()):
            age = (current_time - session_info.created_at).total_seconds()
            
            if age > max_age_seconds:
                try:
                    self.terminate_session(session_id)
                    cleaned.append(session_id)
                except Exception as e:
                    print(f"Failed to cleanup session {session_id}: {e}")
        
        if cleaned:
            print(f"Cleaned up {len(cleaned)} inactive sessions")
        
        return cleaned
    
    def periodic_cleanup(self, max_age_hours: Optional[int] = None) -> None:
        """
        Periodically clean up inactive sessions.
        Should be called regularly (e.g., every hour).
        
        Args:
            max_age_hours: Maximum age for inactive sessions (uses auto_cleanup_hours if not specified)
        """
        if max_age_hours is None:
            max_age_hours = self.auto_cleanup_hours
            
        cleaned = self.cleanup_inactive_sessions(max_age_hours)
        if cleaned:
            print(f"🧹 Periodic cleanup: removed {len(cleaned)} inactive sessions")
    
    def get_sessions_by_device_type(self, device_type: DeviceType) -> List[str]:
        """Get all sessions for a specific device type."""
        return [
            session_id for session_id, info in self.sessions.items()
            if info.device_type == device_type
        ]
    
    def get_sessions_by_device(self, device_udid: str) -> List[str]:
        """Get all sessions for a specific device."""
        return [
            session_id for session_id, info in self.sessions.items()
            if info.device_udid == device_udid
        ]
    
    def refresh_session(self, session_id: str) -> bool:
        """
        Refresh session by checking device availability.
        
        Args:
            session_id: Session ID
            
        Returns:
            bool: True if session is still valid
        """
        if session_id not in self.sessions:
            return False
        
        # Force device cache refresh
        self.device_manager.discover_all_devices(refresh_cache=True)
        
        return self.is_session_available(session_id)
    
    def print_sessions_status(self):
        """Print formatted status of all sessions."""
        sessions = self.list_sessions()
        
        print(f"\n📊 Active Sessions ({len(sessions)}/{self.max_sessions}):")
        print("=" * 60)
        
        if not sessions:
            print("No active sessions")
            return
        
        for session_id in sessions:
            try:
                info = self.get_session_info(session_id)
                
                # Format status
                device_icon = "📱" if info['device_type'] == 'real_device' else "🖥️"
                state_icon = "🟢" if info['is_available'] else "🔴"
                
                print(f"\n{device_icon} {session_id}")
                print(f"   {state_icon} {info['device_name']} ({info['device_type']})")
                print(f"   UDID: {info['device_udid']}")
                print(f"   OS: {info['os_version']}")
                print(f"   State: {info['current_state']}")
                print(f"   Created: {info['created_at']}")
                
                # Show age
                age_seconds = info['age_seconds']
                if age_seconds < 3600:
                    age_str = f"{int(age_seconds / 60)} minutes"
                else:
                    age_str = f"{int(age_seconds / 3600)} hours"
                print(f"   Age: {age_str}")
                
            except Exception as e:
                print(f"\n❌ {session_id} (Error: {e})")
    
    def _cleanup_old_sessions_on_startup(self):
        """Clean up old sessions on startup."""
        print("🧹 Cleaning up old sessions...")
        
        cutoff_time = datetime.now() - timedelta(hours=self.auto_cleanup_hours)
        removed = 0
        corrupted = 0
        
        for session_file in self.session_dir.glob("*.json"):
            try:
                with open(session_file, 'r') as f:
                    data = json.load(f)
                
                # Check if session is old
                created_at = datetime.fromisoformat(data['created_at'])
                if created_at < cutoff_time:
                    session_file.unlink()
                    removed += 1
            except Exception as e:
                # Remove corrupted files
                print(f"Removing corrupted session file: {session_file.name}")
                session_file.unlink()
                corrupted += 1
        
        if removed > 0 or corrupted > 0:
            print(f"✅ Cleaned up {removed} old and {corrupted} corrupted session files")
    
    def _enforce_session_limit(self):
        """Ensure we don't exceed maximum session limit."""
        if len(self.sessions) > self.max_sessions:
            # Sort sessions by creation time
            sorted_sessions = sorted(
                self.sessions.items(),
                key=lambda x: x[1].created_at
            )
            
            # Remove oldest sessions
            to_remove = len(self.sessions) - self.max_sessions
            for session_id, _ in sorted_sessions[:to_remove]:
                try:
                    self.terminate_session(session_id)
                except Exception as e:
                    print(f"Failed to terminate old session {session_id}: {e}")
                    # Force remove
                    if session_id in self.sessions:
                        del self.sessions[session_id]
                    self._delete_session_file(session_id)
            
            print(f"✅ Enforced session limit: {len(self.sessions)}/{self.max_sessions}")
    
    def _find_or_prepare_device(self, config: SessionConfig) -> DeviceInfo:
        """Find or prepare a device based on configuration."""
        # Try to find specific device by UDID
        if config.device_udid:
            device = self.device_manager.get_device(config.device_udid)
            if not device:
                raise DeviceNotFoundError(f"Device not found: {config.device_udid}")
            
            # Prepare device if needed
            if not self.device_manager.is_device_available(device.udid):
                if device.device_type == DeviceType.SIMULATOR and config.autoboot:
                    print(f"Booting simulator: {device.name}")
                    self.device_manager.boot_device(device.udid)
                elif device.device_type == DeviceType.REAL_DEVICE and config.wait_for_connection:
                    print(f"Waiting for device connection: {device.name}")
                    if not self.device_manager.wait_for_device(device.udid, timeout=30):
                        raise DeviceNotAvailableError(f"Device not available: {device.name}")
                else:
                    raise DeviceNotAvailableError(f"Device not available: {device.name}")
            
            return device
        
        # Find by criteria
        all_devices = self.device_manager.discover_all_devices()
        
        # Filter by criteria
        candidates = all_devices
        
        if config.device_name:
            candidates = [d for d in candidates if d.name == config.device_name]
        
        if config.device_type:
            candidates = [d for d in candidates if d.device_type == config.device_type]
        
        if config.platform_version:
            candidates = [d for d in candidates if config.platform_version in d.os_version]
        
        if not candidates:
            raise DeviceNotFoundError("No devices match the specified criteria")
        
        # Prefer available devices
        if config.prefer_available:
            available = [d for d in candidates if d.state in [DeviceState.BOOTED, DeviceState.CONNECTED]]
            if available:
                return available[0]
        
        # Use first candidate and prepare it
        device = candidates[0]
        
        if not self.device_manager.is_device_available(device.udid):
            if device.device_type == DeviceType.SIMULATOR and config.autoboot:
                print(f"Booting simulator: {device.name}")
                self.device_manager.boot_device(device.udid)
            elif device.device_type == DeviceType.REAL_DEVICE:
                raise DeviceNotAvailableError(f"Real device not connected: {device.name}")
            else:
                raise DeviceNotAvailableError(f"Device not available: {device.name}")
        
        return device
    
    def _generate_session_id(self, custom_name: Optional[str] = None) -> str:
        """Generate unique session ID using alternative UUID generation."""
        timestamp = int(time.time())
        # Use first 8 characters of our custom UUID
        unique_id = generate_uuid4()[:8]
        
        if custom_name:
            return f"{custom_name}_{timestamp}_{unique_id}"
        else:
            return f"session_{timestamp}_{unique_id}"
    
    def _save_session(self, session_info: SessionInfo):
        """Save session to disk with proper enum serialization."""
        session_file = self.session_dir / f"{session_info.session_id}.json"
        
        # Convert enum to string before JSON serialization
        data = {
            'session_id': session_info.session_id,
            'device_udid': session_info.device_udid,
            'device_type': session_info.device_type.value,  # Convert enum to string
            'created_at': session_info.created_at.isoformat(),
            'metadata': self._serialize_metadata(session_info.metadata)  # Handle nested objects
        }
        
        try:
            with open(session_file, 'w') as f:
                json.dump(data, f, indent=2, default=self._json_serializer)
            # Only log in debug mode to reduce noise
            # print(f"💾 Session saved: {session_info.session_id}")
        except Exception as e:
            print(f"❌ Failed to save session {session_info.session_id}: {e}")
            # Don't raise - allow session creation to continue even if save fails
    
    def _serialize_metadata(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively serialize metadata to JSON-compatible format."""
        if not isinstance(metadata, dict):
            return metadata
        
        serialized = {}
        for key, value in metadata.items():
            if hasattr(value, 'value'):  # Handle enums
                serialized[key] = value.value
            elif isinstance(value, dict):
                serialized[key] = self._serialize_metadata(value)
            elif isinstance(value, (list, tuple)):
                serialized[key] = [
                    item.value if hasattr(item, 'value') else item 
                    for item in value
                ]
            elif isinstance(value, datetime):
                serialized[key] = value.isoformat()
            elif isinstance(value, Path):
                serialized[key] = str(value)
            else:
                serialized[key] = value
        return serialized
    
    def _json_serializer(self, obj):
        """Custom JSON serializer for non-standard types."""
        if hasattr(obj, 'value'):  # Handle enums
            return obj.value
        elif isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, Path):
            return str(obj)
        else:
            return str(obj)
    
    def _load_sessions(self):
        """Load sessions from disk with better error handling."""
        loaded_count = 0
        failed_count = 0
        
        # Only load sessions newer than auto_cleanup_hours
        cutoff_time = datetime.now() - timedelta(hours=self.auto_cleanup_hours)
        
        for session_file in self.session_dir.glob("*.json"):
            try:
                with open(session_file, 'r') as f:
                    data = json.load(f)
                
                # Validate required fields
                required_fields = ['session_id', 'device_udid', 'device_type', 'created_at']
                if not all(field in data for field in required_fields):
                    print(f"Warning: Invalid session file {session_file} - missing required fields")
                    failed_count += 1
                    session_file.unlink()  # Remove invalid file
                    continue
                
                # Parse datetime and check age
                try:
                    created_at = datetime.fromisoformat(data['created_at'])
                    if created_at < cutoff_time:
                        # Skip old sessions
                        session_file.unlink()
                        continue
                except ValueError:
                    print(f"Warning: Invalid created_at in {session_file}: {data['created_at']}")
                    failed_count += 1
                    session_file.unlink()  # Remove invalid file
                    continue
                
                # Proper enum conversion with validation
                try:
                    device_type = DeviceType(data['device_type']) if isinstance(data['device_type'], str) else data['device_type']
                except ValueError:
                    print(f"Warning: Invalid device_type in {session_file}: {data['device_type']}")
                    failed_count += 1
                    session_file.unlink()  # Remove invalid file
                    continue
                
                session_info = SessionInfo(
                    session_id=data['session_id'],
                    device_udid=data['device_udid'],
                    device_type=device_type,
                    created_at=created_at,
                    metadata=data.get('metadata', {})
                )
                
                self.sessions[session_info.session_id] = session_info
                loaded_count += 1
                
                # Stop loading if we hit the max limit
                if loaded_count >= self.max_sessions:
                    print(f"⚠️ Reached max sessions limit ({self.max_sessions}), skipping remaining files")
                    break
                
            except json.JSONDecodeError as e:
                print(f"Warning: Invalid JSON in session file {session_file}: {e}")
                failed_count += 1
                # Move corrupted files to backup directory
                self._backup_corrupted_session(session_file)
            except Exception as e:
                print(f"Warning: Failed to load session {session_file}: {e}")
                failed_count += 1
        
        if loaded_count > 0:
            print(f"📁 Loaded {loaded_count} sessions from disk")
        if failed_count > 0:
            print(f"⚠️ Failed to load {failed_count} session files")
    
    def _backup_corrupted_session(self, session_file: Path):
        """Move corrupted session file to backup directory."""
        try:
            backup_dir = self.session_dir / "corrupted"
            backup_dir.mkdir(exist_ok=True)
            
            backup_file = backup_dir / f"{session_file.name}.{int(time.time())}.bak"
            session_file.rename(backup_file)
            print(f"📁 Moved corrupted session to: {backup_file}")
        except Exception as e:
            print(f"⚠️ Failed to backup corrupted session: {e}")
    
    def _delete_session_file(self, session_id: str):
        """Delete session file from disk."""
        session_file = self.session_dir / f"{session_id}.json"
        if session_file.exists():
            session_file.unlink()
    
    def export_sessions(self, output_file: Path):
        """Export all sessions to a file."""
        data = {
            'export_time': datetime.now().isoformat(),
            'total_sessions': len(self.sessions),
            'sessions': []
        }
        
        for session_id in self.sessions:
            try:
                info = self.get_session_info(session_id)
                data['sessions'].append(info)
            except Exception as e:
                data['sessions'].append({
                    'session_id': session_id,
                    'error': str(e)
                })
        
        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"📄 Exported {len(self.sessions)} sessions to {output_file}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get session statistics."""
        total = len(self.sessions)
        simulators = len(self.get_sessions_by_device_type(DeviceType.SIMULATOR))
        real_devices = len(self.get_sessions_by_device_type(DeviceType.REAL_DEVICE))
        available = sum(1 for s in self.sessions if self.is_session_available(s))
        
        # Calculate age statistics
        ages = []
        for session_info in self.sessions.values():
            age = (datetime.now() - session_info.created_at).total_seconds()
            ages.append(age)
        
        avg_age = sum(ages) / len(ages) if ages else 0
        
        return {
            'total_sessions': total,
            'simulator_sessions': simulators,
            'real_device_sessions': real_devices,
            'available_sessions': available,
            'average_age_hours': avg_age / 3600,
            'oldest_session_hours': max(ages) / 3600 if ages else 0,
            'newest_session_hours': min(ages) / 3600 if ages else 0,
            'max_sessions_limit': self.max_sessions,
            'auto_cleanup_hours': self.auto_cleanup_hours
        }