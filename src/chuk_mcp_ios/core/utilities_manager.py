#!/usr/bin/env python3
# src/chuk_mcp_ios/core/utilities_manager.py
"""
Unified Utilities Manager for iOS Device Control

Provides utility operations including URL handling, permissions, keychain, 
debugging, and other device management utilities for both simulators and real devices.

ENHANCED VERSION: Improved session ID to Device UDID resolution.
"""

import os
import re
import json
import time
import sqlite3
import plistlib
import subprocess
from typing import List, Optional, Union, Dict, Any, Tuple
from dataclasses import dataclass
from pathlib import Path
from datetime import datetime
import urllib.parse

from .base import (
    CommandExecutor,
    DeviceType,
    DeviceNotAvailableError,
    DeviceError,
    SessionError,
    detect_available_tools
)
from .device_manager import UnifiedDeviceManager

@dataclass
class Permission:
    """Represents a device permission."""
    name: str
    service: str  # photos, camera, microphone, location, etc.
    status: str  # granted, denied, unset, restricted
    bundle_id: Optional[str] = None
    
    @property
    def is_granted(self) -> bool:
        return self.status == 'granted'

@dataclass
class URLScheme:
    """Represents a URL scheme."""
    scheme: str
    bundle_id: str
    description: Optional[str] = None

@dataclass
class NetworkProfile:
    """Network conditioning profile."""
    name: str
    bandwidth_down: int  # kbps
    bandwidth_up: int  # kbps
    latency: int  # ms
    packet_loss: float  # percentage

@dataclass
class DeviceSettings:
    """Device settings configuration."""
    locale: Optional[str] = None
    language: Optional[str] = None
    region: Optional[str] = None
    timezone: Optional[str] = None
    keyboard_layout: Optional[str] = None
    accessibility: Optional[Dict[str, bool]] = None

class UnifiedUtilitiesManager(CommandExecutor):
    """
    Unified utilities manager supporting both iOS simulators and real devices.
    Provides various utility operations for device management and testing.
    
    ENHANCED VERSION: Improved session resolution and error handling.
    """
    
    def __init__(self):
        super().__init__()
        self.device_manager = UnifiedDeviceManager()
        self.session_manager = None  # Optional session manager
        self.available_tools = detect_available_tools()
        
        # Add logging if available
        try:
            import logging
            self.logger = logging.getLogger(__name__)
        except:
            # Fallback logger
            class FakeLogger:
                def debug(self, msg): pass
                def info(self, msg): pass
                def warning(self, msg): pass
                def error(self, msg): pass
            self.logger = FakeLogger()
        
        # Predefined network profiles
        self.network_profiles = {
            '3g': NetworkProfile('3G', 384, 384, 300, 0.0),
            '3g_good': NetworkProfile('3G Good', 1500, 750, 100, 0.0),
            'edge': NetworkProfile('Edge', 200, 200, 500, 0.0),
            'lte': NetworkProfile('LTE', 10000, 5000, 50, 0.0),
            'wifi': NetworkProfile('WiFi', 40000, 30000, 2, 0.0),
            'wifi_poor': NetworkProfile('WiFi Poor', 1000, 1000, 200, 2.0),
            'offline': NetworkProfile('Offline', 0, 0, 0, 100.0),
            'lossy': NetworkProfile('Lossy Network', 5000, 2000, 100, 10.0)
        }
        
        # Common URL schemes
        self.url_schemes = {
            # System apps
            'settings': URLScheme('prefs', 'com.apple.Preferences', 'Settings app'),
            'app-store': URLScheme('itms-apps', 'com.apple.AppStore', 'App Store'),
            'maps': URLScheme('maps', 'com.apple.Maps', 'Maps app'),
            'mail': URLScheme('mailto', 'com.apple.mobilemail', 'Mail app'),
            'messages': URLScheme('sms', 'com.apple.MobileSMS', 'Messages app'),
            'facetime': URLScheme('facetime', 'com.apple.facetime', 'FaceTime'),
            'calendar': URLScheme('calshow', 'com.apple.mobilecal', 'Calendar'),
            'photos': URLScheme('photos-redirect', 'com.apple.mobileslideshow', 'Photos'),
            'music': URLScheme('music', 'com.apple.Music', 'Music app'),
            'safari': URLScheme('http', 'com.apple.mobilesafari', 'Safari'),
            
            # Deep links
            'wifi-settings': URLScheme('prefs:root=WIFI', 'com.apple.Preferences', 'WiFi settings'),
            'bluetooth-settings': URLScheme('prefs:root=Bluetooth', 'com.apple.Preferences', 'Bluetooth settings'),
            'privacy-settings': URLScheme('prefs:root=Privacy', 'com.apple.Preferences', 'Privacy settings'),
            'notifications-settings': URLScheme('prefs:root=NOTIFICATIONS_ID', 'com.apple.Preferences', 'Notifications'),
        }
    
    def set_session_manager(self, session_manager):
        """Set session manager for session-based operations."""
        self.session_manager = session_manager
        self.logger.debug(f"Session manager set: {id(session_manager)}")
        print(f"🔧 Utilities manager configured with session manager: {id(session_manager)}")
    

    def _get_device_udid_from_session(self, session_id: str) -> str:
        """
        Get device UDID from session ID using enhanced resolution strategy.
        
        Args:
            session_id: Session identifier
            
        Returns:
            str: Device UDID
            
        Raises:
            SessionError: If session cannot be resolved
        """
        # Strategy 1: Try the configured session manager first
        if self.session_manager:
            try:
                device_udid = self.session_manager.get_device_udid(session_id)
                self.logger.debug(f"Session {session_id} resolved via configured manager to {device_udid}")
                return device_udid
            except Exception as e:
                self.logger.debug(f"Configured session manager failed for {session_id}: {e}")
        
        # Strategy 2: Try to get session manager from global registry
        try:
            from ..mcp.tools import get_session_manager_for_session
            session_manager = get_session_manager_for_session(session_id)
            if session_manager:
                self.logger.debug(f"Retrieved session manager from global registry for {session_id}")
                device_udid = session_manager.get_device_udid(session_id)
                self.logger.debug(f"Session {session_id} resolved via global registry to {device_udid}")
                
                # Update our session manager reference for future calls
                self.session_manager = session_manager
                return device_udid
        except ImportError:
            self.logger.debug("Global registry not available")
        except Exception as e:
            self.logger.debug(f"Global registry lookup failed for {session_id}: {e}")
        
        # Strategy 3: Try creating a new session manager and see if it can find the session
        try:
            self.logger.debug(f"Attempting fallback session discovery for {session_id}")
            from .session_manager import UnifiedSessionManager
            fallback_manager = UnifiedSessionManager()
            
            if session_id in fallback_manager.sessions:
                device_udid = fallback_manager.get_device_udid(session_id)
                self.logger.debug(f"Session {session_id} found via fallback manager: {device_udid}")
                
                # Update our session manager reference
                self.session_manager = fallback_manager
                return device_udid
        except Exception as e:
            self.logger.debug(f"Fallback session discovery failed: {e}")
        
        # All strategies failed
        raise SessionError(f"Session {session_id} not found in any session manager - session may have expired or been terminated")
    
    def _looks_like_session_id(self, target: str) -> bool:
        """Check if target looks like a session ID."""
        # Session IDs typically have patterns like:
        # - session_timestamp_hash
        # - automation_timestamp_hash  
        # - custom_name_timestamp_hash
        return ('_' in target and 
                len(target) > 10 and 
                (target.startswith(('session_', 'automation_', 'mcp_')) or 
                 target.count('_') >= 2))
    
    def _resolve_target(self, target: Union[str, Dict]) -> str:
        """
        Resolve target to device UDID with enhanced session handling.
        
        Args:
            target: Device UDID, session ID, or dict containing device info
            
        Returns:
            str: Device UDID
            
        Raises:
            ValueError: If target format is invalid
            SessionError: If session resolution fails
        """
        if isinstance(target, str):
            self.logger.debug(f"🔍 Resolving target: {target}")
            
            # Check if it looks like a session ID
            if self._looks_like_session_id(target):
                self.logger.debug(f"🎯 Target appears to be session ID: {target}")
                
                try:
                    device_udid = self._get_device_udid_from_session(target)
                    self.logger.debug(f"✅ Resolved session {target} to device {device_udid}")
                    return device_udid
                except SessionError as e:
                    self.logger.error(f"❌ Failed to resolve session {target}: {e}")
                    raise
                except Exception as e:
                    self.logger.error(f"❌ Unexpected error resolving session {target}: {e}")
                    raise SessionError(f"Failed to resolve session {target}: {e}")
            
            # Treat as direct device UDID
            self.logger.debug(f"🎯 Treating {target} as direct device UDID")
            return target
            
        elif isinstance(target, dict):
            # Extract UDID from dict
            udid = target.get('udid', target.get('device_udid', ''))
            if not udid:
                raise ValueError(f"No UDID found in target dict: {target}")
            return udid
        else:
            raise ValueError(f"Invalid target type: {type(target)} - {target}")
    
    # ═══════════════════════════════════════════════════════════════════════════
    # URL Operations
    # ═══════════════════════════════════════════════════════════════════════════
    
    def open_url(self, target: Union[str, Dict], url: str) -> None:
        """
        Open URL on device.
        
        Args:
            target: Device UDID or session ID
            url: URL to open
            
        Raises:
            DeviceNotAvailableError: If device is not available
        """
        self.logger.info(f"📱 Opening URL: {url}")
        
        # Enhanced target resolution
        udid = self._resolve_target(target)
        self.logger.debug(f"🎯 Target resolved to device UDID: {udid}")
        
        # Verify device is available using the resolved UDID
        self._verify_device_available(udid)
        
        # Validate URL
        if not self._is_valid_url(url):
            raise ValueError(f"Invalid URL: {url}")
        
        device = self.device_manager.get_device(udid)
        if not device:
            raise DeviceNotAvailableError(f"Device not found: {udid}")
        
        # Open URL based on device type
        if device.device_type == DeviceType.SIMULATOR:
            self._open_url_simulator(udid, url)
        else:
            self._open_url_real_device(udid, url)
        
        self.logger.info(f"✅ Successfully opened URL: {url}")
        print(f"✅ Opened URL: {url}")
    
    def open_scheme(self, target: Union[str, Dict], scheme_name: str) -> None:
        """Open predefined URL scheme."""
        if scheme_name not in self.url_schemes:
            available = list(self.url_schemes.keys())
            raise ValueError(f"Unknown scheme: {scheme_name}. Available: {available}")
        
        scheme = self.url_schemes[scheme_name]
        url = f"{scheme.scheme}://"
        
        self.open_url(target, url)
        print(f"✅ Opened {scheme.description or scheme_name}")
    
    def open_settings(self, target: Union[str, Dict], page: Optional[str] = None) -> None:
        """
        Open Settings app.
        
        Args:
            target: Device UDID or session ID
            page: Optional settings page (wifi, bluetooth, privacy, etc.)
        """
        if page:
            scheme_name = f"{page}-settings"
            if scheme_name in self.url_schemes:
                self.open_scheme(target, scheme_name)
            else:
                self.open_url(target, f"prefs:root={page.upper()}")
        else:
            self.open_scheme(target, 'settings')
    
    def open_app_settings(self, target: Union[str, Dict], bundle_id: str) -> None:
        """Open settings page for specific app."""
        # This URL scheme opens the app's settings page
        url = f"app-settings:{bundle_id}"
        self.open_url(target, url)
    
    # ═══════════════════════════════════════════════════════════════════════════
    # Permission Management
    # ═══════════════════════════════════════════════════════════════════════════
    
    def get_permissions(self, target: Union[str, Dict], 
                       bundle_id: str) -> List[Permission]:
        """
        Get app permissions.
        
        Args:
            target: Device UDID or session ID
            bundle_id: App bundle identifier
            
        Returns:
            List[Permission]: App permissions
        """
        udid = self._resolve_target(target)
        self._verify_device_available(udid)
        
        device = self.device_manager.get_device(udid)
        if not device:
            raise DeviceNotAvailableError(f"Device not found: {udid}")
        
        if device.device_type == DeviceType.SIMULATOR:
            return self._get_permissions_simulator(udid, bundle_id)
        else:
            return self._get_permissions_real_device(udid, bundle_id)
    
    def set_permission(self, target: Union[str, Dict], bundle_id: str, 
                      service: str, status: str) -> None:
        """
        Set app permission.
        
        Args:
            target: Device UDID or session ID
            bundle_id: App bundle identifier
            service: Permission service (photos, camera, location, etc.)
            status: Permission status (grant, deny, unset)
        """
        # Enhanced target resolution
        udid = self._resolve_target(target)
        self._verify_device_available(udid)
        
        valid_services = ['photos', 'camera', 'microphone', 'location', 'contacts', 
                         'calendar', 'reminders', 'notifications', 'health']
        valid_statuses = ['grant', 'deny', 'unset']
        
        if service not in valid_services:
            raise ValueError(f"Invalid service: {service}. Valid: {valid_services}")
        if status not in valid_statuses:
            raise ValueError(f"Invalid status: {status}. Valid: {valid_statuses}")
        
        device = self.device_manager.get_device(udid)
        if not device:
            raise DeviceNotAvailableError(f"Device not found: {udid}")
        
        if device.device_type == DeviceType.SIMULATOR:
            self._set_permission_simulator(udid, bundle_id, service, status)
        else:
            self._set_permission_real_device(udid, bundle_id, service, status)
        
        print(f"✅ Set {service} permission to {status} for {bundle_id}")
    
    def grant_all_permissions(self, target: Union[str, Dict], bundle_id: str) -> None:
        """Grant all permissions to an app."""
        services = ['photos', 'camera', 'microphone', 'location', 'contacts', 
                   'calendar', 'reminders', 'notifications']
        
        for service in services:
            try:
                self.set_permission(target, bundle_id, service, 'grant')
            except Exception as e:
                print(f"⚠️  Failed to grant {service}: {e}")
    
    def reset_permissions(self, target: Union[str, Dict], 
                         bundle_id: Optional[str] = None) -> None:
        """Reset permissions for app or all apps."""
        udid = self._resolve_target(target)
        device = self.device_manager.get_device(udid)
        
        if device and device.device_type == DeviceType.SIMULATOR:
            try:
                if bundle_id:
                    self.run_command(f"{self.simctl_path} privacy {udid} reset all {bundle_id}")
                    print(f"✅ Reset permissions for {bundle_id}")
                else:
                    self.run_command(f"{self.simctl_path} privacy {udid} reset all")
                    print("✅ Reset all permissions")
            except Exception as e:
                raise DeviceError(f"Failed to reset permissions: {e}")
        else:
            print("⚠️  Permission reset only supported on simulators")
    
    # ═══════════════════════════════════════════════════════════════════════════
    # Keychain Operations
    # ═══════════════════════════════════════════════════════════════════════════
    
    def clear_keychain(self, target: Union[str, Dict]) -> None:
        """Clear device keychain."""
        # Enhanced target resolution
        udid = self._resolve_target(target)
        self._verify_device_available(udid)
        
        device = self.device_manager.get_device(udid)
        if not device:
            raise DeviceNotAvailableError(f"Device not found: {udid}")
        
        if device.device_type == DeviceType.SIMULATOR:
            self._clear_keychain_simulator(udid)
        else:
            self._clear_keychain_real_device(udid)
        
        print("✅ Keychain cleared")
    
    # ═══════════════════════════════════════════════════════════════════════════
    # Network Operations
    # ═══════════════════════════════════════════════════════════════════════════
    
    def set_network_condition(self, target: Union[str, Dict], 
                             profile: Union[str, NetworkProfile]) -> None:
        """
        Set network conditioning.
        
        Args:
            target: Device UDID or session ID
            profile: Network profile name or NetworkProfile object
        """
        udid = self._resolve_target(target)
        device = self.device_manager.get_device(udid)
        
        if not device:
            raise DeviceNotAvailableError(f"Device not found: {udid}")
        
        if isinstance(profile, str):
            if profile not in self.network_profiles:
                available = list(self.network_profiles.keys())
                raise ValueError(f"Unknown profile: {profile}. Available: {available}")
            profile = self.network_profiles[profile]
        
        if device.device_type == DeviceType.SIMULATOR:
            # Note: Network conditioning for simulators requires additional setup
            print(f"⚠️  Network conditioning on simulators requires Network Link Conditioner")
            print(f"   Profile: {profile.name}")
            print(f"   Bandwidth: ↓{profile.bandwidth_down} ↑{profile.bandwidth_up} kbps")
            print(f"   Latency: {profile.latency}ms, Loss: {profile.packet_loss}%")
        else:
            print("⚠️  Network conditioning on real devices requires device configuration")
    
    def clear_network_condition(self, target: Union[str, Dict]) -> None:
        """Clear network conditioning."""
        print("✅ Network conditioning cleared (requires manual configuration)")
    
    # ═══════════════════════════════════════════════════════════════════════════
    # Device Settings
    # ═══════════════════════════════════════════════════════════════════════════
    
    def get_device_info(self, target: Union[str, Dict]) -> Dict[str, Any]:
        """Get detailed device information."""
        udid = self._resolve_target(target)
        device = self.device_manager.get_device(udid)
        
        if not device:
            raise DeviceNotAvailableError(f"Device not found: {udid}")
        
        info = {
            'udid': device.udid,
            'name': device.name,
            'type': device.device_type.value,
            'os_version': device.os_version,
            'model': device.model,
            'state': device.state.value,
            'connection_type': device.connection_type,
            'capabilities': self.device_manager.get_device_capabilities(udid)
        }
        
        # Add additional info based on device type
        if device.device_type == DeviceType.SIMULATOR:
            info.update(self._get_simulator_info(udid))
        else:
            info.update(self._get_real_device_info(udid))
        
        return info
    
    def set_device_settings(self, target: Union[str, Dict], 
                           settings: DeviceSettings) -> None:
        """
        Set device settings.
        
        Args:
            target: Device UDID or session ID
            settings: Device settings configuration
        """
        udid = self._resolve_target(target)
        device = self.device_manager.get_device(udid)
        
        if not device:
            raise DeviceNotAvailableError(f"Device not found: {udid}")
        
        if device.device_type == DeviceType.SIMULATOR:
            # Set simulator settings
            if settings.locale:
                self._set_simulator_locale(udid, settings.locale)
            if settings.language:
                self._set_simulator_language(udid, settings.language)
            if settings.timezone:
                self._set_simulator_timezone(udid, settings.timezone)
            
            print("✅ Device settings updated (restart may be required)")
        else:
            print("⚠️  Device settings modification limited on real devices")
    
    # ═══════════════════════════════════════════════════════════════════════════
    # Clipboard Operations
    # ═══════════════════════════════════════════════════════════════════════════
    
    def set_clipboard(self, target: Union[str, Dict], text: str) -> None:
        """Set clipboard content."""
        udid = self._resolve_target(target)
        device = self.device_manager.get_device(udid)
        
        if not device:
            raise DeviceNotAvailableError(f"Device not found: {udid}")
        
        if device.device_type == DeviceType.SIMULATOR:
            # Use pbcopy through simulator
            try:
                escaped_text = text.replace("'", "'\"'\"'")
                self.run_command(f"echo '{escaped_text}' | pbcopy")
                print(f"✅ Clipboard set: {text[:50]}{'...' if len(text) > 50 else ''}")
            except Exception as e:
                raise DeviceError(f"Failed to set clipboard: {e}")
        else:
            print("⚠️  Clipboard operations not supported on real devices via this tool")
    
    def get_clipboard(self, target: Union[str, Dict]) -> Optional[str]:
        """Get clipboard content."""
        udid = self._resolve_target(target)
        device = self.device_manager.get_device(udid)
        
        if not device:
            return None
        
        if device.device_type == DeviceType.SIMULATOR:
            try:
                result = self.run_command("pbpaste")
                return result.stdout.strip()
            except:
                return None
        else:
            print("⚠️  Clipboard operations not supported on real devices via this tool")
            return None
    
    # ═══════════════════════════════════════════════════════════════════════════
    # App Store Operations
    # ═══════════════════════════════════════════════════════════════════════════
    
    def open_app_store_page(self, target: Union[str, Dict], app_id: str) -> None:
        """Open App Store page for an app."""
        url = f"itms-apps://apps.apple.com/app/id{app_id}"
        self.open_url(target, url)
    
    def search_app_store(self, target: Union[str, Dict], query: str) -> None:
        """Search App Store."""
        encoded_query = urllib.parse.quote(query)
        url = f"itms-apps://search.itunes.apple.com/WebObjects/MZSearch.woa/wa/search?media=software&term={encoded_query}"
        self.open_url(target, url)
    
    # ═══════════════════════════════════════════════════════════════════════════
    # Debugging Operations
    # ═══════════════════════════════════════════════════════════════════════════
    
    def enable_developer_mode(self, target: Union[str, Dict]) -> None:
        """Enable developer mode (simulators only)."""
        udid = self._resolve_target(target)
        device = self.device_manager.get_device(udid)
        
        if device and device.device_type == DeviceType.SIMULATOR:
            print("✅ Developer mode enabled for simulator")
        else:
            print("⚠️  Developer mode must be enabled manually on real devices:")
            print("   1. Go to Settings > Privacy & Security")
            print("   2. Tap Developer Mode")
            print("   3. Toggle Developer Mode on")
            print("   4. Restart device")
    
    def simulate_memory_warning(self, target: Union[str, Dict]) -> None:
        """Simulate memory warning."""
        udid = self._resolve_target(target)
        device = self.device_manager.get_device(udid)
        
        if device and device.device_type == DeviceType.SIMULATOR:
            try:
                self.run_command(f"{self.simctl_path} spawn {udid} memory_pressure -S critical")
                print("✅ Memory warning simulated")
            except Exception as e:
                print(f"⚠️  Failed to simulate memory warning: {e}")
        else:
            print("⚠️  Memory warning simulation only available on simulators")
    
    def trigger_icloud_sync(self, target: Union[str, Dict]) -> None:
        """Trigger iCloud sync."""
        udid = self._resolve_target(target)
        device = self.device_manager.get_device(udid)
        
        if device and device.device_type == DeviceType.SIMULATOR:
            try:
                self.run_command(f"{self.simctl_path} spawn {udid} notifyutil -p com.apple.icloud.sync")
                print("✅ iCloud sync triggered")
            except:
                print("⚠️  Could not trigger iCloud sync")
        else:
            print("⚠️  iCloud sync trigger only available on simulators")
    
    # ═══════════════════════════════════════════════════════════════════════════
    # Focus and Window Management
    # ═══════════════════════════════════════════════════════════════════════════
    
    def focus_simulator(self, target: Union[str, Dict]) -> None:
        """Focus simulator window."""
        udid = self._resolve_target(target)
        device = self.device_manager.get_device(udid)
        
        if device and device.device_type == DeviceType.SIMULATOR:
            try:
                # Use AppleScript to focus Simulator app
                script = '''
                tell application "Simulator"
                    activate
                end tell
                '''
                self.run_command(f"osascript -e '{script}'")
                print("✅ Simulator window focused")
            except Exception as e:
                print(f"⚠️  Failed to focus simulator: {e}")
        else:
            print("⚠️  Window focus only available for simulators")
    
    # ═══════════════════════════════════════════════════════════════════════════
    # Utility Methods
    # ═══════════════════════════════════════════════════════════════════════════
    
    def create_backup(self, target: Union[str, Dict], backup_path: Path) -> None:
        """Create device backup (simulators only)."""
        udid = self._resolve_target(target)
        device = self.device_manager.get_device(udid)
        
        if device and device.device_type == DeviceType.SIMULATOR:
            # Get simulator data directory
            device_dir = Path.home() / "Library/Developer/CoreSimulator/Devices" / udid
            
            if device_dir.exists():
                import shutil
                backup_path = Path(backup_path)
                backup_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Create backup
                shutil.make_archive(str(backup_path.with_suffix('')), 'zip', device_dir)
                print(f"✅ Backup created: {backup_path}")
            else:
                raise DeviceError("Simulator data directory not found")
        else:
            print("⚠️  Backup only supported for simulators")
    
    def restore_backup(self, target: Union[str, Dict], backup_path: Path) -> None:
        """Restore device backup (simulators only)."""
        print("⚠️  Backup restore not implemented - requires careful handling")
    
    # ═══════════════════════════════════════════════════════════════════════════
    # Helper Methods
    # ═══════════════════════════════════════════════════════════════════════════
    
    def _verify_device_available(self, udid: str):
        """Verify device is available."""
        self.logger.debug(f"Verifying device availability: {udid}")
        if not self.device_manager.is_device_available(udid):
            raise DeviceNotAvailableError(f"Device not available: {udid}")
        self.logger.debug(f"Device {udid} is available")
    
    def _is_valid_url(self, url: str) -> bool:
        """Validate URL format."""
        # Allow various URL schemes
        patterns = [
            r'^https?://.*',  # HTTP/HTTPS
            r'^[a-zA-Z][a-zA-Z0-9+.-]*://',  # Custom schemes
            r'^mailto:.*',  # Email
            r'^tel:.*',  # Phone
            r'^sms:.*',  # SMS
        ]
        
        return any(re.match(pattern, url, re.IGNORECASE) for pattern in patterns)
    
    # ═══════════════════════════════════════════════════════════════════════════
    # Simulator-specific implementations
    # ═══════════════════════════════════════════════════════════════════════════
    
    def _open_url_simulator(self, udid: str, url: str):
        """Open URL on simulator."""
        try:
            self.logger.debug(f"Opening URL on simulator {udid}: {url}")
            self.run_command(f"{self.simctl_path} openurl {udid} '{url}'")
            self.logger.debug(f"Successfully opened URL on simulator")
        except Exception as e:
            raise DeviceError(f"Failed to open URL on simulator: {e}")
    
    def _get_permissions_simulator(self, udid: str, bundle_id: str) -> List[Permission]:
        """Get permissions on simulator."""
        permissions = []
        
        # Parse TCC database for permissions
        tcc_db = Path.home() / f"Library/Developer/CoreSimulator/Devices/{udid}/data/Library/TCC/TCC.db"
        
        if tcc_db.exists():
            try:
                conn = sqlite3.connect(str(tcc_db))
                cursor = conn.cursor()
                
                # Query permissions
                cursor.execute("""
                    SELECT service, allowed FROM access 
                    WHERE client = ? AND client_type = 0
                """, (bundle_id,))
                
                for service, allowed in cursor.fetchall():
                    permissions.append(Permission(
                        name=service,
                        service=service,
                        status='granted' if allowed else 'denied',
                        bundle_id=bundle_id
                    ))
                
                conn.close()
            except Exception as e:
                print(f"Warning: Could not read permissions: {e}")
        
        return permissions
    
    def _set_permission_simulator(self, udid: str, bundle_id: str, 
                                 service: str, status: str):
        """Set permission on simulator."""
        try:
            self.run_command(f"{self.simctl_path} privacy {udid} {status} {service} {bundle_id}")
        except Exception as e:
            raise DeviceError(f"Failed to set permission: {e}")
    
    def _clear_keychain_simulator(self, udid: str):
        """Clear keychain on simulator."""
        keychain_dir = Path.home() / f"Library/Developer/CoreSimulator/Devices/{udid}/data/Library/Keychains"
        
        if keychain_dir.exists():
            try:
                import shutil
                shutil.rmtree(keychain_dir)
                keychain_dir.mkdir()
                print("✅ Keychain cleared")
            except Exception as e:
                raise DeviceError(f"Failed to clear keychain: {e}")
        else:
            print("⚠️  Keychain directory not found")
    
    def _get_simulator_info(self, udid: str) -> Dict[str, Any]:
        """Get additional simulator info."""
        info = {}
        
        # Get device plist
        device_plist = Path.home() / f"Library/Developer/CoreSimulator/Devices/{udid}/device.plist"
        
        if device_plist.exists():
            try:
                with open(device_plist, 'rb') as f:
                    plist_data = plistlib.load(f)
                
                info['runtime'] = plist_data.get('runtime', '')
                info['device_type'] = plist_data.get('deviceType', '')
                
            except Exception as e:
                print(f"Warning: Could not read device plist: {e}")
        
        return info
    
    def _set_simulator_locale(self, udid: str, locale: str):
        """Set simulator locale."""
        # This would modify the simulator's GlobalPreferences.plist
        print(f"Setting locale to {locale} (requires app restart)")
    
    def _set_simulator_language(self, udid: str, language: str):
        """Set simulator language."""
        # This would modify the simulator's GlobalPreferences.plist
        print(f"Setting language to {language} (requires app restart)")
    
    def _set_simulator_timezone(self, udid: str, timezone: str):
        """Set simulator timezone."""
        try:
            self.run_command(f"{self.simctl_path} spawn {udid} defaults write /System/Library/User\\ Template/English.lproj/Library/Preferences/.GlobalPreferences.plist timezone '{timezone}'")
            print(f"✅ Timezone set to {timezone}")
        except:
            print("⚠️  Could not set timezone")
    
    # ═══════════════════════════════════════════════════════════════════════════
    # Real device-specific implementations
    # ═══════════════════════════════════════════════════════════════════════════
    
    def _open_url_real_device(self, udid: str, url: str):
        """Open URL on real device."""
        if self.available_tools.get('idb'):
            try:
                self.run_command(f"{self.idb_path} open --udid {udid} '{url}'")
            except Exception as e:
                raise DeviceError(f"Failed to open URL: {e}")
        else:
            raise DeviceError("idb required for real device URL operations")
    
    def _get_permissions_real_device(self, udid: str, bundle_id: str) -> List[Permission]:
        """Get permissions on real device."""
        # Limited permission querying on real devices
        print("⚠️  Permission querying limited on real devices")
        return []
    
    def _set_permission_real_device(self, udid: str, bundle_id: str,
                                   service: str, status: str):
        """Set permission on real device."""
        if self.available_tools.get('idb'):
            try:
                # idb approve command
                if status == 'grant':
                    self.run_command(f"{self.idb_path} approve --udid {udid} {bundle_id} {service}")
                else:
                    print("⚠️  Permission denial not supported on real devices")
            except Exception as e:
                raise DeviceError(f"Failed to set permission: {e}")
        else:
            print("⚠️  Permission management requires idb for real devices")
    
    def _clear_keychain_real_device(self, udid: str):
        """Clear keychain on real device."""
        if self.available_tools.get('idb'):
            try:
                self.run_command(f"{self.idb_path} clear_keychain --udid {udid}")
            except:
                print("⚠️  Keychain clearing not supported on this device")
        else:
            print("⚠️  Keychain operations require idb for real devices")
    
    def _get_real_device_info(self, udid: str) -> Dict[str, Any]:
        """Get additional real device info."""
        info = {}
        
        if self.available_tools.get('idb'):
            try:
                result = self.run_command(f"{self.idb_path} describe --udid {udid} --json")
                device_data = json.loads(result.stdout)
                info.update(device_data)
            except:
                pass
        
        return info