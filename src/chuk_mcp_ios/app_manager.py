#!/usr/bin/env python3
# chuk_mcp/app_manager.py
"""
App Manager Module
Handles app installation, management, and lifecycle operations.
"""

import json
import os
import plistlib
from pathlib import Path
from typing import List, Optional, Dict
from ios_simulator_base import (
    AppManagerInterface,
    AppInfo,
    CommandExecutor,
    AppNotFoundError,
    SimulatorNotBootedError
)

class AppManager(CommandExecutor, AppManagerInterface):
    """Manages iOS app operations including installation, launching, and management."""
    
    def __init__(self):
        super().__init__()
        self.verify_idb_availability()
    
    def install_app(self, udid: str, app_path: str) -> AppInfo:
        """
        Install an app on the simulator.
        
        Args:
            udid: Simulator UDID
            app_path: Path to the .app bundle
            
        Returns:
            AppInfo: Information about the installed app
            
        Raises:
            AppNotFoundError: If app bundle doesn't exist
            SimulatorNotBootedError: If simulator is not running
        """
        if not os.path.exists(app_path):
            raise AppNotFoundError(f"App bundle does not exist: {app_path}")
        
        # Verify simulator is booted
        if not self._is_simulator_booted(udid):
            raise SimulatorNotBootedError(f"Simulator {udid} is not booted")
        
        try:
            self.run_command(f"{self.idb_path} install --udid {udid} '{app_path}'")
            print(f"Successfully installed app: {app_path}")
        except Exception as e:
            raise AppNotFoundError(f"Failed to install app {app_path}: {str(e)}")
        
        # Extract app info from bundle
        app_info = self._extract_app_info(app_path)
        return app_info
    
    def uninstall_app(self, udid: str, bundle_id: str) -> None:
        """
        Uninstall an app from the simulator.
        
        Args:
            udid: Simulator UDID
            bundle_id: App bundle identifier
            
        Raises:
            AppNotFoundError: If app is not installed
            SimulatorNotBootedError: If simulator is not running
        """
        if not self._is_simulator_booted(udid):
            raise SimulatorNotBootedError(f"Simulator {udid} is not booted")
        
        if not self.is_app_installed(udid, bundle_id):
            raise AppNotFoundError(f"App {bundle_id} is not installed")
        
        try:
            self.run_command(f"{self.idb_path} uninstall --udid {udid} {bundle_id}")
            print(f"Successfully uninstalled app: {bundle_id}")
        except Exception as e:
            raise AppNotFoundError(f"Failed to uninstall app {bundle_id}: {str(e)}")
    
    def launch_app(self, udid: str, bundle_id: str, arguments: Optional[List[str]] = None) -> None:
        """
        Launch an app by bundle identifier.
        
        Args:
            udid: Simulator UDID
            bundle_id: App bundle identifier
            arguments: Optional launch arguments
            
        Raises:
            AppNotFoundError: If app is not installed
            SimulatorNotBootedError: If simulator is not running
        """
        if not self._is_simulator_booted(udid):
            raise SimulatorNotBootedError(f"Simulator {udid} is not booted")
        
        if not self.is_app_installed(udid, bundle_id):
            raise AppNotFoundError(f"App {bundle_id} is not installed")
        
        try:
            command = f"{self.idb_path} launch --udid {udid} {bundle_id}"
            if arguments:
                args_str = ' '.join(f'"{arg}"' for arg in arguments)
                command += f" -- {args_str}"
            
            self.run_command(command)
            print(f"Successfully launched app: {bundle_id}")
        except Exception as e:
            raise AppNotFoundError(f"Failed to launch app {bundle_id}: {str(e)}")
    
    def terminate_app(self, udid: str, bundle_id: str) -> None:
        """
        Terminate an app by bundle identifier.
        
        Args:
            udid: Simulator UDID
            bundle_id: App bundle identifier
            
        Raises:
            AppNotFoundError: If app is not running
            SimulatorNotBootedError: If simulator is not running
        """
        if not self._is_simulator_booted(udid):
            raise SimulatorNotBootedError(f"Simulator {udid} is not booted")
        
        try:
            self.run_command(f"{self.idb_path} terminate --udid {udid} {bundle_id}")
            print(f"Successfully terminated app: {bundle_id}")
        except Exception as e:
            # Don't raise error if app wasn't running
            print(f"Note: App {bundle_id} may not have been running: {str(e)}")
    
    def list_apps(self, udid: str, user_apps_only: bool = True) -> List[AppInfo]:
        """
        List all installed apps on the simulator.
        
        Args:
            udid: Simulator UDID
            user_apps_only: If True, only return user-installed apps
            
        Returns:
            List[AppInfo]: List of installed apps
            
        Raises:
            SimulatorNotBootedError: If simulator is not running
        """
        if not self._is_simulator_booted(udid):
            raise SimulatorNotBootedError(f"Simulator {udid} is not booted")
        
        try:
            command = f"{self.idb_path} list-apps --udid {udid} --json"
            result = self.run_command(command)
            apps_data = json.loads(result.stdout)
            
            apps = []
            for app in apps_data:
                # Filter system apps if requested
                if user_apps_only and self._is_system_app(app.get('bundle_id', '')):
                    continue
                
                apps.append(AppInfo(
                    bundle_id=app.get('bundle_id', ''),
                    name=app.get('name', app.get('bundle_id', 'Unknown')),
                    installed_path=app.get('install_path', '')
                ))
            
            return apps
        except Exception as e:
            raise AppNotFoundError(f"Failed to list apps: {str(e)}")
    
    def is_app_installed(self, udid: str, bundle_id: str) -> bool:
        """
        Check if an app is installed on the simulator.
        
        Args:
            udid: Simulator UDID
            bundle_id: App bundle identifier
            
        Returns:
            bool: True if app is installed
        """
        try:
            apps = self.list_apps(udid, user_apps_only=False)
            return any(app.bundle_id == bundle_id for app in apps)
        except:
            return False
    
    def is_app_running(self, udid: str, bundle_id: str) -> bool:
        """
        Check if an app is currently running.
        
        Args:
            udid: Simulator UDID
            bundle_id: App bundle identifier
            
        Returns:
            bool: True if app is running
        """
        try:
            result = self.run_command(f"{self.idb_path} list-targets --udid {udid} --json")
            targets = json.loads(result.stdout)
            
            for target in targets:
                if target.get('bundle_id') == bundle_id:
                    return True
            return False
        except:
            return False
    
    def get_app_info(self, udid: str, bundle_id: str) -> Optional[AppInfo]:
        """
        Get detailed information about a specific app.
        
        Args:
            udid: Simulator UDID
            bundle_id: App bundle identifier
            
        Returns:
            Optional[AppInfo]: App information or None if not found
        """
        apps = self.list_apps(udid, user_apps_only=False)
        return next((app for app in apps if app.bundle_id == bundle_id), None)
    
    def install_multiple_apps(self, udid: str, app_paths: List[str]) -> List[AppInfo]:
        """
        Install multiple apps in sequence.
        
        Args:
            udid: Simulator UDID
            app_paths: List of paths to app bundles
            
        Returns:
            List[AppInfo]: List of successfully installed apps
        """
        installed_apps = []
        failed_apps = []
        
        for app_path in app_paths:
            try:
                app_info = self.install_app(udid, app_path)
                installed_apps.append(app_info)
                print(f"✅ Installed: {app_info.name}")
            except Exception as e:
                failed_apps.append((app_path, str(e)))
                print(f"❌ Failed to install {app_path}: {str(e)}")
        
        if failed_apps:
            print(f"\nFailed to install {len(failed_apps)} apps:")
            for app_path, error in failed_apps:
                print(f"  - {app_path}: {error}")
        
        return installed_apps
    
    def uninstall_multiple_apps(self, udid: str, bundle_ids: List[str]) -> Dict[str, bool]:
        """
        Uninstall multiple apps.
        
        Args:
            udid: Simulator UDID
            bundle_ids: List of bundle identifiers
            
        Returns:
            Dict[str, bool]: Map of bundle_id to success status
        """
        results = {}
        
        for bundle_id in bundle_ids:
            try:
                self.uninstall_app(udid, bundle_id)
                results[bundle_id] = True
                print(f"✅ Uninstalled: {bundle_id}")
            except Exception as e:
                results[bundle_id] = False
                print(f"❌ Failed to uninstall {bundle_id}: {str(e)}")
        
        return results
    
    def _extract_app_info(self, app_path: str) -> AppInfo:
        """
        Extract app information from bundle.
        
        Args:
            app_path: Path to app bundle
            
        Returns:
            AppInfo: Extracted app information
        """
        # Try to read Info.plist
        info_plist_path = os.path.join(app_path, 'Info.plist')
        
        if os.path.exists(info_plist_path):
            try:
                with open(info_plist_path, 'rb') as f:
                    plist_data = plistlib.load(f)
                
                bundle_id = plist_data.get('CFBundleIdentifier', '')
                display_name = (plist_data.get('CFBundleDisplayName') or 
                              plist_data.get('CFBundleName') or 
                              os.path.splitext(os.path.basename(app_path))[0])
                
                return AppInfo(
                    bundle_id=bundle_id,
                    name=display_name,
                    installed_path=app_path
                )
            except Exception as e:
                print(f"Warning: Could not read Info.plist: {e}")
        
        # Fallback to filename
        app_name = os.path.splitext(os.path.basename(app_path))[0]
        return AppInfo(
            bundle_id=f"com.example.{app_name.lower().replace(' ', '')}",
            name=app_name,
            installed_path=app_path
        )
    
    def _is_system_app(self, bundle_id: str) -> bool:
        """Check if an app is a system app."""
        system_prefixes = [
            'com.apple.',
            'com.facebook.WebDriverAgentRunner',
            'com.facebook.wda.',
            'io.appium.'
        ]
        return any(bundle_id.startswith(prefix) for prefix in system_prefixes)
    
    def _is_simulator_booted(self, udid: str) -> bool:
        """Check if simulator is booted."""
        from simulator_manager import SimulatorManager
        sim_manager = SimulatorManager()
        return sim_manager.is_simulator_booted(udid)
    
    def print_installed_apps(self, udid: str, user_apps_only: bool = True) -> None:
        """Print a formatted list of installed apps."""
        try:
            apps = self.list_apps(udid, user_apps_only)
            
            if not apps:
                print("No apps installed" + (" (user apps only)" if user_apps_only else ""))
                return
            
            print(f"\n📱 Installed Apps {'(User Apps Only)' if user_apps_only else ''}:")
            print("=" * 60)
            
            for app in sorted(apps, key=lambda x: x.name):
                running_indicator = "🟢" if self.is_app_running(udid, app.bundle_id) else "⚪"
                print(f"{running_indicator} {app.name}")
                print(f"   Bundle ID: {app.bundle_id}")
                if app.installed_path:
                    print(f"   Path: {app.installed_path}")
                print()
                
        except Exception as e:
            print(f"Error listing apps: {e}")