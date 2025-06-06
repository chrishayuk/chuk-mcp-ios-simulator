#!/usr/bin/env python3
# chuk_mcp_ios/core/app_manager.py
"""
Unified App Manager for iOS Device Control

Manages app installation, launching, and lifecycle for both simulators and real devices.
"""

import os
import json
import plistlib
import shutil
import tempfile
from pathlib import Path
from typing import List, Optional, Dict, Any, Union
from dataclasses import dataclass
from datetime import datetime

from .base import (
    AppManagerInterface,
    CommandExecutor,
    AppInfo,
    DeviceType,
    AppNotFoundError,
    DeviceNotAvailableError,
    DeviceError,
    validate_bundle_id
)
from .device_manager import UnifiedDeviceManager
from .session_manager import UnifiedSessionManager

@dataclass
class AppInstallConfig:
    """Configuration for app installation."""
    force_reinstall: bool = False  # Uninstall before installing
    skip_if_installed: bool = False  # Skip if already installed
    launch_after_install: bool = False  # Launch app after installation
    developer_team_id: Optional[str] = None  # For real device signing
    install_timeout: int = 120  # Installation timeout in seconds

class UnifiedAppManager(CommandExecutor, AppManagerInterface):
    """
    Unified app manager supporting both iOS simulators and real devices.
    Handles app installation, management, and lifecycle operations.
    """
    
    def __init__(self):
        super().__init__()
        self.device_manager = UnifiedDeviceManager()
        self.session_manager = None  # Optional session manager
        self._app_cache = {}
        self._cache_timeout = 60
        self._last_cache_time = {}
    
    def set_session_manager(self, session_manager: UnifiedSessionManager):
        """Set session manager for session-based operations."""
        self.session_manager = session_manager
    
    def install_app(self, target: Union[str, Dict], app_path: str, 
                   config: Optional[AppInstallConfig] = None) -> AppInfo:
        """
        Install an app on the device.
        
        Args:
            target: Device UDID or session ID
            app_path: Path to .app bundle or .ipa file
            config: Installation configuration
            
        Returns:
            AppInfo: Installed app information
            
        Raises:
            AppNotFoundError: If app file doesn't exist
            DeviceNotAvailableError: If device is not available
        """
        if config is None:
            config = AppInstallConfig()
        
        # Resolve target to UDID
        udid = self._resolve_target(target)
        
        # Validate app path
        if not os.path.exists(app_path):
            raise AppNotFoundError(f"App not found: {app_path}")
        
        # Get device info
        device = self.device_manager.get_device(udid)
        if not device:
            raise DeviceNotAvailableError(f"Device not found: {udid}")
        
        if not self.device_manager.is_device_available(udid):
            raise DeviceNotAvailableError(f"Device not available: {device.name}")
        
        # Extract app info
        app_info = self._extract_app_info(app_path)
        
        # Check if already installed
        if config.skip_if_installed and self.is_app_installed(udid, app_info.bundle_id):
            print(f"App {app_info.name} already installed, skipping")
            return app_info
        
        # Force reinstall if requested
        if config.force_reinstall and self.is_app_installed(udid, app_info.bundle_id):
            print(f"Force reinstalling {app_info.name}...")
            self.uninstall_app(udid, app_info.bundle_id)
        
        # Install based on device type
        if device.device_type == DeviceType.SIMULATOR:
            self._install_simulator_app(udid, app_path, app_info)
        else:
            self._install_real_device_app(udid, app_path, app_info, config)
        
        # Update cache
        self._invalidate_app_cache(udid)
        
        print(f"✅ Installed: {app_info.name} ({app_info.bundle_id})")
        
        # Launch if requested
        if config.launch_after_install:
            self.launch_app(udid, app_info.bundle_id)
        
        return app_info
    
    def uninstall_app(self, target: Union[str, Dict], bundle_id: str) -> None:
        """
        Uninstall an app from the device.
        
        Args:
            target: Device UDID or session ID
            bundle_id: App bundle identifier
            
        Raises:
            AppNotFoundError: If app is not installed
            DeviceNotAvailableError: If device is not available
        """
        udid = self._resolve_target(target)
        
        if not validate_bundle_id(bundle_id):
            raise ValueError(f"Invalid bundle ID: {bundle_id}")
        
        if not self.is_app_installed(udid, bundle_id):
            raise AppNotFoundError(f"App not installed: {bundle_id}")
        
        device = self.device_manager.get_device(udid)
        if not device:
            raise DeviceNotAvailableError(f"Device not found: {udid}")
        
        # Uninstall based on device type
        if device.device_type == DeviceType.SIMULATOR:
            self._uninstall_simulator_app(udid, bundle_id)
        else:
            self._uninstall_real_device_app(udid, bundle_id)
        
        # Update cache
        self._invalidate_app_cache(udid)
        
        print(f"✅ Uninstalled: {bundle_id}")
    
    def launch_app(self, target: Union[str, Dict], bundle_id: str, 
                  arguments: Optional[List[str]] = None) -> None:
        """
        Launch an app on the device.
        
        Args:
            target: Device UDID or session ID
            bundle_id: App bundle identifier
            arguments: Optional launch arguments
            
        Raises:
            AppNotFoundError: If app is not installed
            DeviceNotAvailableError: If device is not available
        """
        udid = self._resolve_target(target)
        
        if not validate_bundle_id(bundle_id):
            raise ValueError(f"Invalid bundle ID: {bundle_id}")
        
        if not self.is_app_installed(udid, bundle_id):
            raise AppNotFoundError(f"App not installed: {bundle_id}")
        
        device = self.device_manager.get_device(udid)
        if not device:
            raise DeviceNotAvailableError(f"Device not found: {udid}")
        
        # Launch based on device type
        if device.device_type == DeviceType.SIMULATOR:
            self._launch_simulator_app(udid, bundle_id, arguments)
        else:
            self._launch_real_device_app(udid, bundle_id, arguments)
        
        print(f"✅ Launched: {bundle_id}")
    
    def terminate_app(self, target: Union[str, Dict], bundle_id: str) -> None:
        """
        Terminate a running app.
        
        Args:
            target: Device UDID or session ID
            bundle_id: App bundle identifier
            
        Raises:
            AppNotFoundError: If app is not installed
            DeviceNotAvailableError: If device is not available
        """
        udid = self._resolve_target(target)
        
        if not validate_bundle_id(bundle_id):
            raise ValueError(f"Invalid bundle ID: {bundle_id}")
        
        device = self.device_manager.get_device(udid)
        if not device:
            raise DeviceNotAvailableError(f"Device not found: {udid}")
        
        # Terminate based on device type
        try:
            if device.device_type == DeviceType.SIMULATOR:
                self._terminate_simulator_app(udid, bundle_id)
            else:
                self._terminate_real_device_app(udid, bundle_id)
            
            print(f"✅ Terminated: {bundle_id}")
        except Exception as e:
            print(f"⚠️  App may not have been running: {e}")
    
    def list_apps(self, target: Union[str, Dict], user_apps_only: bool = True) -> List[AppInfo]:
        """
        List installed apps.
        
        Args:
            target: Device UDID or session ID
            user_apps_only: If True, exclude system apps
            
        Returns:
            List[AppInfo]: List of installed apps
            
        Raises:
            DeviceNotAvailableError: If device is not available
        """
        udid = self._resolve_target(target)
        
        # Check cache
        cache_key = f"{udid}_{user_apps_only}"
        if self._is_cache_valid(cache_key):
            return self._app_cache.get(cache_key, [])
        
        device = self.device_manager.get_device(udid)
        if not device:
            raise DeviceNotAvailableError(f"Device not found: {udid}")
        
        # List apps based on device type
        if device.device_type == DeviceType.SIMULATOR:
            apps = self._list_simulator_apps(udid)
        else:
            apps = self._list_real_device_apps(udid)
        
        # Filter system apps if requested
        if user_apps_only:
            apps = [app for app in apps if not self._is_system_app(app.bundle_id)]
        
        # Update cache
        self._app_cache[cache_key] = apps
        self._last_cache_time[cache_key] = time.time()
        
        return apps
    
    def is_app_installed(self, target: Union[str, Dict], bundle_id: str) -> bool:
        """
        Check if an app is installed.
        
        Args:
            target: Device UDID or session ID
            bundle_id: App bundle identifier
            
        Returns:
            bool: True if app is installed
        """
        try:
            apps = self.list_apps(target, user_apps_only=False)
            return any(app.bundle_id == bundle_id for app in apps)
        except:
            return False
    
    def is_app_running(self, target: Union[str, Dict], bundle_id: str) -> bool:
        """
        Check if an app is currently running.
        
        Args:
            target: Device UDID or session ID
            bundle_id: App bundle identifier
            
        Returns:
            bool: True if app is running
        """
        udid = self._resolve_target(target)
        device = self.device_manager.get_device(udid)
        
        if not device:
            return False
        
        try:
            if device.device_type == DeviceType.SIMULATOR:
                # Use simctl for simulators
                result = self.run_command(f"{self.simctl_path} spawn {udid} launchctl list | grep {bundle_id}")
                return bundle_id in result.stdout
            else:
                # Use idb for real devices
                result = self.run_command(f"{self.idb_path} list-targets --udid {udid} --json")
                targets = json.loads(result.stdout)
                return any(t.get('bundle_id') == bundle_id for t in targets)
        except:
            return False
    
    def get_app_info(self, target: Union[str, Dict], bundle_id: str) -> Optional[AppInfo]:
        """
        Get detailed information about a specific app.
        
        Args:
            target: Device UDID or session ID
            bundle_id: App bundle identifier
            
        Returns:
            Optional[AppInfo]: App information or None
        """
        apps = self.list_apps(target, user_apps_only=False)
        return next((app for app in apps if app.bundle_id == bundle_id), None)
    
    def install_multiple_apps(self, target: Union[str, Dict], app_paths: List[str], 
                            config: Optional[AppInstallConfig] = None) -> List[AppInfo]:
        """
        Install multiple apps in sequence.
        
        Args:
            target: Device UDID or session ID
            app_paths: List of app paths
            config: Installation configuration
            
        Returns:
            List[AppInfo]: Successfully installed apps
        """
        installed = []
        failed = []
        
        for app_path in app_paths:
            try:
                app_info = self.install_app(target, app_path, config)
                installed.append(app_info)
            except Exception as e:
                failed.append((app_path, str(e)))
                print(f"❌ Failed to install {app_path}: {e}")
        
        if failed:
            print(f"\nFailed to install {len(failed)} apps:")
            for path, error in failed:
                print(f"  - {path}: {error}")
        
        return installed
    
    def export_app_list(self, target: Union[str, Dict], output_file: Path):
        """Export installed apps list to file."""
        apps = self.list_apps(target, user_apps_only=False)
        
        data = {
            'export_time': datetime.now().isoformat(),
            'device_udid': self._resolve_target(target),
            'total_apps': len(apps),
            'user_apps': len([a for a in apps if not self._is_system_app(a.bundle_id)]),
            'apps': [
                {
                    'bundle_id': app.bundle_id,
                    'name': app.name,
                    'version': app.version,
                    'is_system': self._is_system_app(app.bundle_id)
                }
                for app in apps
            ]
        }
        
        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"📄 Exported {len(apps)} apps to {output_file}")
    
    def _resolve_target(self, target: Union[str, Dict]) -> str:
        """Resolve target to device UDID."""
        if isinstance(target, str):
            # Check if it's a session ID
            if self.session_manager and target.startswith(('session_', 'automation_')):
                try:
                    return self.session_manager.get_device_udid(target)
                except:
                    pass
            # Otherwise assume it's a UDID
            return target
        elif isinstance(target, dict):
            # Extract UDID from dict
            return target.get('udid', target.get('device_udid', ''))
        else:
            raise ValueError(f"Invalid target: {target}")
    
    def _extract_app_info(self, app_path: str) -> AppInfo:
        """Extract app information from app bundle or IPA."""
        if app_path.endswith('.ipa'):
            return self._extract_ipa_info(app_path)
        else:
            return self._extract_app_bundle_info(app_path)
    
    def _extract_app_bundle_info(self, app_path: str) -> AppInfo:
        """Extract info from .app bundle."""
        info_plist_path = os.path.join(app_path, 'Info.plist')
        
        if not os.path.exists(info_plist_path):
            # Fallback info
            app_name = os.path.basename(app_path).replace('.app', '')
            return AppInfo(
                bundle_id=f"com.unknown.{app_name.lower()}",
                name=app_name,
                version="1.0"
            )
        
        try:
            with open(info_plist_path, 'rb') as f:
                plist_data = plistlib.load(f)
            
            return AppInfo(
                bundle_id=plist_data.get('CFBundleIdentifier', ''),
                name=plist_data.get('CFBundleDisplayName') or 
                     plist_data.get('CFBundleName') or 
                     os.path.basename(app_path).replace('.app', ''),
                version=plist_data.get('CFBundleShortVersionString', '1.0'),
                installed_path=app_path
            )
        except Exception as e:
            print(f"Warning: Could not read Info.plist: {e}")
            app_name = os.path.basename(app_path).replace('.app', '')
            return AppInfo(
                bundle_id=f"com.unknown.{app_name.lower()}",
                name=app_name,
                version="1.0"
            )
    
    def _extract_ipa_info(self, ipa_path: str) -> AppInfo:
        """Extract info from .ipa file."""
        import zipfile
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Extract IPA
            with zipfile.ZipFile(ipa_path, 'r') as zip_file:
                zip_file.extractall(temp_dir)
            
            # Find .app bundle
            payload_dir = os.path.join(temp_dir, 'Payload')
            if not os.path.exists(payload_dir):
                raise AppNotFoundError("Invalid IPA: No Payload directory")
            
            app_bundles = [d for d in os.listdir(payload_dir) if d.endswith('.app')]
            if not app_bundles:
                raise AppNotFoundError("Invalid IPA: No .app bundle found")
            
            app_path = os.path.join(payload_dir, app_bundles[0])
            return self._extract_app_bundle_info(app_path)
    
    def _is_system_app(self, bundle_id: str) -> bool:
        """Check if app is a system app."""
        system_prefixes = [
            'com.apple.',
            'com.facebook.WebDriverAgent',
            'com.facebook.wda.',
            'io.appium.'
        ]
        return any(bundle_id.startswith(prefix) for prefix in system_prefixes)
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cache is still valid."""
        import time
        if cache_key not in self._last_cache_time:
            return False
        
        age = time.time() - self._last_cache_time[cache_key]
        return age < self._cache_timeout
    
    def _invalidate_app_cache(self, udid: str):
        """Invalidate app cache for a device."""
        keys_to_remove = [k for k in self._app_cache.keys() if k.startswith(udid)]
        for key in keys_to_remove:
            del self._app_cache[key]
            if key in self._last_cache_time:
                del self._last_cache_time[key]
    
    # Simulator-specific methods
    def _install_simulator_app(self, udid: str, app_path: str, app_info: AppInfo):
        """Install app on simulator."""
        try:
            self.run_command(f"{self.simctl_path} install {udid} '{app_path}'")
        except Exception as e:
            raise DeviceError(f"Failed to install app on simulator: {e}")
    
    def _uninstall_simulator_app(self, udid: str, bundle_id: str):
        """Uninstall app from simulator."""
        try:
            self.run_command(f"{self.simctl_path} uninstall {udid} {bundle_id}")
        except Exception as e:
            raise DeviceError(f"Failed to uninstall app from simulator: {e}")
    
    def _launch_simulator_app(self, udid: str, bundle_id: str, arguments: Optional[List[str]]):
        """Launch app on simulator."""
        try:
            command = f"{self.simctl_path} launch {udid} {bundle_id}"
            if arguments:
                args_str = ' '.join([f'"{arg}"' for arg in arguments])
                command += f" {args_str}"
            self.run_command(command)
        except Exception as e:
            raise DeviceError(f"Failed to launch app on simulator: {e}")
    
    def _terminate_simulator_app(self, udid: str, bundle_id: str):
        """Terminate app on simulator."""
        try:
            self.run_command(f"{self.simctl_path} terminate {udid} {bundle_id}")
        except Exception as e:
            raise DeviceError(f"Failed to terminate app on simulator: {e}")
    
    def _list_simulator_apps(self, udid: str) -> List[AppInfo]:
        """List apps on simulator."""
        apps = []
        
        # Get installed apps directory
        device_data_path = os.path.expanduser(f"~/Library/Developer/CoreSimulator/Devices/{udid}/data")
        containers_path = os.path.join(device_data_path, "Containers/Bundle/Application")
        
        if os.path.exists(containers_path):
            for app_dir in os.listdir(containers_path):
                app_path = os.path.join(containers_path, app_dir)
                
                # Find .app bundle
                for item in os.listdir(app_path):
                    if item.endswith('.app'):
                        full_app_path = os.path.join(app_path, item)
                        try:
                            app_info = self._extract_app_bundle_info(full_app_path)
                            apps.append(app_info)
                        except:
                            pass
        
        return apps
    
    # Real device-specific methods
    def _install_real_device_app(self, udid: str, app_path: str, app_info: AppInfo, config: AppInstallConfig):
        """Install app on real device."""
        try:
            if self.idb_path:
                command = f"{self.idb_path} install --udid {udid} '{app_path}'"
                if config.developer_team_id:
                    command += f" --team-id {config.developer_team_id}"
                self.run_command(command, timeout=config.install_timeout)
            else:
                raise DeviceError("idb not available for real device installation")
        except Exception as e:
            raise DeviceError(f"Failed to install app on real device: {e}")
    
    def _uninstall_real_device_app(self, udid: str, bundle_id: str):
        """Uninstall app from real device."""
        try:
            if self.idb_path:
                self.run_command(f"{self.idb_path} uninstall --udid {udid} {bundle_id}")
            else:
                raise DeviceError("idb not available for real device uninstallation")
        except Exception as e:
            raise DeviceError(f"Failed to uninstall app from real device: {e}")
    
    def _launch_real_device_app(self, udid: str, bundle_id: str, arguments: Optional[List[str]]):
        """Launch app on real device."""
        try:
            if self.idb_path:
                command = f"{self.idb_path} launch --udid {udid} {bundle_id}"
                if arguments:
                    args_str = ' '.join([f'"{arg}"' for arg in arguments])
                    command += f" -- {args_str}"
                self.run_command(command)
            else:
                raise DeviceError("idb not available for real device app launch")
        except Exception as e:
            raise DeviceError(f"Failed to launch app on real device: {e}")
    
    def _terminate_real_device_app(self, udid: str, bundle_id: str):
        """Terminate app on real device."""
        try:
            if self.idb_path:
                self.run_command(f"{self.idb_path} terminate --udid {udid} {bundle_id}")
            else:
                raise DeviceError("idb not available for real device app termination")
        except Exception as e:
            raise DeviceError(f"Failed to terminate app on real device: {e}")
    
    def _list_real_device_apps(self, udid: str) -> List[AppInfo]:
        """List apps on real device."""
        apps = []
        
        try:
            if self.idb_path:
                result = self.run_command(f"{self.idb_path} list-apps --udid {udid} --json")
                apps_data = json.loads(result.stdout)
                
                for app in apps_data:
                    apps.append(AppInfo(
                        bundle_id=app.get('bundle_id', ''),
                        name=app.get('name', app.get('bundle_id', 'Unknown')),
                        version=app.get('version', ''),
                        installed_path=app.get('install_path', '')
                    ))
            else:
                raise DeviceError("idb not available for real device app listing")
        except Exception as e:
            print(f"Warning: Failed to list real device apps: {e}")
        
        return apps