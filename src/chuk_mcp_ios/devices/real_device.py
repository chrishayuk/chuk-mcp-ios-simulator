#!/usr/bin/env python3
# src/chuk_mcp_ios/devices/real_device.py
"""
Real iOS device specific implementation.

Handles all real device-specific operations using idb, devicectl, and other tools.
"""

import os
import json
import re
import time
import subprocess
from typing import List, Optional, Dict, Any, Tuple
from dataclasses import dataclass
from pathlib import Path
from datetime import datetime

from ..core.base import (
    CommandExecutor,
    DeviceInfo,
    DeviceType,
    DeviceState,
    DeviceError,
    DeviceNotFoundError,
    DeviceNotAvailableError,
    detect_available_tools
)

@dataclass
class RealDevice:
    """Represents a real iOS device."""
    udid: str
    name: str
    model: str
    ios_version: str
    architecture: str
    connection_type: str  # usb, wifi
    is_connected: bool
    developer_mode_enabled: bool = False
    trusted: bool = False
    paired: bool = False
    
    def to_device_info(self) -> DeviceInfo:
        """Convert to generic DeviceInfo."""
        return DeviceInfo(
            udid=self.udid,
            name=self.name,
            state=DeviceState.CONNECTED if self.is_connected else DeviceState.DISCONNECTED,
            device_type=DeviceType.REAL_DEVICE,
            os_version=f"iOS {self.ios_version}",
            model=self.model,
            connection_type=self.connection_type,
            architecture=self.architecture,
            is_available=self.is_connected and self.trusted
        )

class RealDeviceManager(CommandExecutor):
    """
    Manages real iOS devices using idb, devicectl, and other tools.
    """
    
    def __init__(self):
        super().__init__()
        self.available_tools = detect_available_tools()
        self._device_cache = {}
        self._cache_time = 0
        self._cache_timeout = 5  # seconds
    
    # Device Discovery
    
    def list_devices(self, refresh: bool = False) -> List[RealDevice]:
        """List all connected real devices."""
        # Check cache
        if not refresh and self._is_cache_valid():
            return list(self._device_cache.values())
        
        devices = {}
        
        # Try multiple discovery methods
        if self.available_tools.get('idb'):
            self._discover_via_idb(devices)
        
        if self.available_tools.get('devicectl'):
            self._discover_via_devicectl(devices)
        
        if self.available_tools.get('instruments'):
            self._discover_via_instruments(devices)
        
        # Update cache
        self._device_cache = devices
        self._cache_time = time.time()
        
        return list(devices.values())
    
    def get_device(self, udid: str) -> Optional[RealDevice]:
        """Get specific device by UDID."""
        devices = self.list_devices()
        return next((d for d in devices if d.udid == udid), None)
    
    def wait_for_device(self, udid: str, timeout: int = 30) -> bool:
        """Wait for a device to connect."""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            device = self.get_device(udid)
            if device and device.is_connected:
                return True
            time.sleep(1)
            self.list_devices(refresh=True)  # Force refresh
        
        return False
    
    # Device Connection Management
    
    def connect_device(self, udid: str, timeout: int = 30) -> None:
        """
        Connect to a device (primarily for WiFi connections).
        
        Args:
            udid: Device UDID
            timeout: Connection timeout
        """
        device = self.get_device(udid)
        if not device:
            raise DeviceNotFoundError(f"Device not found: {udid}")
        
        if device.is_connected:
            print(f"Device {device.name} is already connected")
            return
        
        if device.connection_type == 'wifi':
            self._connect_wifi_device(udid, timeout)
        else:
            print("USB devices connect automatically when plugged in")
    
    def disconnect_device(self, udid: str) -> None:
        """Disconnect from a device (WiFi only)."""
        device = self.get_device(udid)
        if not device:
            raise DeviceNotFoundError(f"Device not found: {udid}")
        
        if device.connection_type == 'wifi':
            self._disconnect_wifi_device(udid)
        else:
            print("USB devices disconnect when unplugged")
    
    def pair_device(self, udid: str) -> None:
        """Pair with a device."""
        if self.available_tools.get('idb'):
            try:
                self.run_command(f"{self.idb_path} pair --udid {udid}")
                print(f"✅ Device paired: {udid}")
            except Exception as e:
                raise DeviceError(f"Failed to pair device: {e}")
        else:
            print("⚠️  Device pairing requires idb or manual action in Xcode")
    
    def trust_device(self, udid: str) -> None:
        """
        Trust a device (requires user interaction on device).
        """
        print("📱 Please unlock your device and tap 'Trust' when prompted")
        
        if self.available_tools.get('idb'):
            try:
                # This will prompt the trust dialog
                self.run_command(f"{self.idb_path} list-apps --udid {udid}", timeout=30)
                print("✅ Device trusted")
            except Exception as e:
                if "trust" in str(e).lower():
                    raise DeviceError("Device not trusted. Please tap 'Trust' on your device")
                raise
        else:
            print("⚠️  Please ensure device is trusted via Xcode or iTunes")
    
    # App Management
    
    def install_app(self, udid: str, app_path: str, 
                   developer_team_id: Optional[str] = None) -> None:
        """Install an app on the device."""
        if not os.path.exists(app_path):
            raise FileNotFoundError(f"App not found: {app_path}")
        
        device = self.get_device(udid)
        if not device:
            raise DeviceNotFoundError(f"Device not found: {udid}")
        
        if not device.is_connected:
            raise DeviceNotAvailableError(f"Device not connected: {device.name}")
        
        if self.available_tools.get('idb'):
            self._install_app_idb(udid, app_path, developer_team_id)
        elif self.available_tools.get('devicectl'):
            self._install_app_devicectl(udid, app_path)
        else:
            raise DeviceError("No suitable tool available for app installation")
    
    def uninstall_app(self, udid: str, bundle_id: str) -> None:
        """Uninstall an app from the device."""
        if self.available_tools.get('idb'):
            try:
                self.run_command(f"{self.idb_path} uninstall --udid {udid} {bundle_id}")
                print(f"✅ App uninstalled: {bundle_id}")
            except Exception as e:
                raise DeviceError(f"Failed to uninstall app: {e}")
        else:
            raise DeviceError("App uninstallation requires idb")
    
    def launch_app(self, udid: str, bundle_id: str, args: Optional[List[str]] = None) -> None:
        """Launch an app on the device."""
        if self.available_tools.get('idb'):
            try:
                cmd = f"{self.idb_path} launch --udid {udid} {bundle_id}"
                if args:
                    cmd += " -- " + " ".join(args)
                
                self.run_command(cmd)
                print(f"✅ App launched: {bundle_id}")
            except Exception as e:
                raise DeviceError(f"Failed to launch app: {e}")
        else:
            raise DeviceError("App launch requires idb")
    
    def terminate_app(self, udid: str, bundle_id: str) -> None:
        """Terminate an app on the device."""
        if self.available_tools.get('idb'):
            try:
                self.run_command(f"{self.idb_path} terminate --udid {udid} {bundle_id}")
                print(f"✅ App terminated: {bundle_id}")
            except Exception as e:
                # App might not be running
                pass
        else:
            print("⚠️  App termination requires idb")
    
    def list_apps(self, udid: str) -> List[Dict[str, str]]:
        """List installed apps on the device."""
        apps = []
        
        if self.available_tools.get('idb'):
            try:
                result = self.run_command(f"{self.idb_path} list-apps --udid {udid} --json")
                app_list = json.loads(result.stdout)
                
                for app in app_list:
                    apps.append({
                        'bundle_id': app.get('bundle_id', ''),
                        'name': app.get('name', ''),
                        'version': app.get('version', ''),
                        'type': app.get('type', 'user')
                    })
                    
            except Exception as e:
                print(f"Warning: Failed to list apps: {e}")
        
        return apps
    
    # Device Operations
    
    def take_screenshot(self, udid: str, output_path: str) -> str:
        """Take a screenshot of the device."""
        if self.available_tools.get('idb'):
            try:
                self.run_command(f"{self.idb_path} screenshot --udid {udid} '{output_path}'")
                return output_path
            except Exception as e:
                raise DeviceError(f"Failed to take screenshot: {e}")
        else:
            raise DeviceError("Screenshot requires idb")
    
    def record_video(self, udid: str, output_path: str, duration: Optional[int] = None) -> None:
        """Record video from the device."""
        if self.available_tools.get('idb'):
            try:
                cmd = f"{self.idb_path} record-video --udid {udid} '{output_path}'"
                
                if duration:
                    # Use timeout to limit recording
                    self.run_command(f"timeout {duration} {cmd}", timeout=duration + 5)
                else:
                    # Start recording in background
                    subprocess.Popen(cmd, shell=True)
                    print(f"📹 Started recording to: {output_path}")
                    print("   Stop with: idb kill")
                    
            except Exception as e:
                if "timeout" not in str(e).lower():
                    raise DeviceError(f"Failed to record video: {e}")
        else:
            raise DeviceError("Video recording requires idb")
    
    def push_file(self, udid: str, local_path: str, device_path: str) -> None:
        """Push a file to the device."""
        if not os.path.exists(local_path):
            raise FileNotFoundError(f"Local file not found: {local_path}")
        
        if self.available_tools.get('idb'):
            try:
                self.run_command(
                    f"{self.idb_path} file push --udid {udid} '{local_path}' '{device_path}'"
                )
                print(f"✅ File pushed: {local_path} -> {device_path}")
            except Exception as e:
                raise DeviceError(f"Failed to push file: {e}")
        else:
            raise DeviceError("File push requires idb")
    
    def pull_file(self, udid: str, device_path: str, local_path: str) -> None:
        """Pull a file from the device."""
        if self.available_tools.get('idb'):
            try:
                self.run_command(
                    f"{self.idb_path} file pull --udid {udid} '{device_path}' '{local_path}'"
                )
                print(f"✅ File pulled: {device_path} -> {local_path}")
            except Exception as e:
                raise DeviceError(f"Failed to pull file: {e}")
        else:
            raise DeviceError("File pull requires idb")
    
    def get_device_info(self, udid: str) -> Dict[str, Any]:
        """Get detailed device information."""
        device = self.get_device(udid)
        if not device:
            raise DeviceNotFoundError(f"Device not found: {udid}")
        
        info = {
            'udid': device.udid,
            'name': device.name,
            'model': device.model,
            'ios_version': device.ios_version,
            'architecture': device.architecture,
            'connection_type': device.connection_type,
            'is_connected': device.is_connected,
            'developer_mode_enabled': device.developer_mode_enabled,
            'trusted': device.trusted,
            'paired': device.paired
        }
        
        # Get additional info via idb if available
        if self.available_tools.get('idb') and device.is_connected:
            try:
                result = self.run_command(f"{self.idb_path} describe --udid {udid} --json")
                idb_info = json.loads(result.stdout)
                info['idb_info'] = idb_info
            except:
                pass
        
        return info
    
    def restart_device(self, udid: str) -> None:
        """Restart the device."""
        if self.available_tools.get('idb'):
            try:
                # Note: This might not work on all devices
                self.run_command(f"{self.idb_path} restart --udid {udid}")
                print("✅ Device restart initiated")
            except Exception as e:
                print(f"⚠️  Device restart may require manual action: {e}")
        else:
            print("⚠️  Please restart the device manually")
    
    # Developer Mode
    
    def check_developer_mode(self, udid: str) -> bool:
        """Check if developer mode is enabled."""
        device = self.get_device(udid)
        if not device:
            return False
        
        # Try to perform a developer action
        if self.available_tools.get('idb'):
            try:
                # List apps is a developer action
                self.run_command(f"{self.idb_path} list-apps --udid {udid}", timeout=5)
                return True
            except Exception as e:
                if "developer mode" in str(e).lower():
                    return False
        
        return device.developer_mode_enabled
    
    def enable_developer_mode_instructions(self) -> List[str]:
        """Get instructions for enabling developer mode."""
        return [
            "To enable Developer Mode on iOS 16+:",
            "1. Connect device to Xcode once",
            "2. On device: Settings > Privacy & Security",
            "3. Scroll down and tap 'Developer Mode'",
            "4. Toggle 'Developer Mode' ON",
            "5. Tap 'Restart' to restart device",
            "6. After restart, tap 'Turn On' and enter passcode"
        ]
    
    # Helper Methods
    
    def _is_cache_valid(self) -> bool:
        """Check if device cache is still valid."""
        return (time.time() - self._cache_time) < self._cache_timeout
    
    def _discover_via_idb(self, devices: Dict[str, RealDevice]) -> None:
        """Discover devices using idb."""
        try:
            result = self.run_command(f"{self.idb_path} list-targets --json", show_errors=False)
            targets = json.loads(result.stdout)
            
            for target in targets:
                if target.get('type') == 'device':
                    udid = target.get('udid', '')
                    if udid and udid not in devices:
                        devices[udid] = RealDevice(
                            udid=udid,
                            name=target.get('name', 'Unknown Device'),
                            model=target.get('model', 'Unknown'),
                            ios_version=target.get('os_version', 'Unknown'),
                            architecture=target.get('architecture', 'Unknown'),
                            connection_type=target.get('connection_type', 'usb').lower(),
                            is_connected=target.get('state') == 'connected',
                            trusted=True  # Assume trusted if visible to idb
                        )
        except Exception as e:
            # Silent failure - don't print warning during discovery
            pass
    
    def _discover_via_devicectl(self, devices: Dict[str, RealDevice]) -> None:
        """Discover devices using devicectl (Xcode 15+)."""
        try:
            # Fix: Use --json-output instead of --json
            result = self.run_command(f"{self.devicectl_path} list devices --json-output /dev/stdout", show_errors=False)
            data = json.loads(result.stdout)
            
            for device_data in data.get('result', {}).get('devices', []):
                udid = device_data.get('identifier', '')
                if udid and udid not in devices:
                    props = device_data.get('deviceProperties', {})
                    hw_props = device_data.get('hardwareProperties', {})
                    conn_props = device_data.get('connectionProperties', {})
                    
                    devices[udid] = RealDevice(
                        udid=udid,
                        name=props.get('name', 'Unknown Device'),
                        model=hw_props.get('marketingName', 'Unknown'),
                        ios_version=props.get('osVersionNumber', 'Unknown'),
                        architecture=hw_props.get('cpuType', {}).get('name', 'Unknown'),
                        connection_type=conn_props.get('transportType', 'usb').lower(),
                        is_connected=bool(conn_props.get('transportType')),
                        developer_mode_enabled=props.get('developerModeStatus') == 'enabled',
                        paired=props.get('isPaired', False)
                    )
        except Exception as e:
            # Silent failure - don't print warning during discovery
            pass
    
    def _discover_via_instruments(self, devices: Dict[str, RealDevice]) -> None:
        """Discover devices using instruments (legacy)."""
        try:
            result = self.run_command("instruments -s devices", show_errors=False)
            lines = result.stdout.split('\n')
            
            for line in lines:
                # Parse: iPhone Name (iOS Version) [UDID]
                match = re.match(r'^(.+?)\s*\(([^)]+)\)\s*\[([A-F0-9-]{36,})\]', line)
                if match:
                    name = match.group(1).strip()
                    ios_version = match.group(2).strip()
                    udid = match.group(3).strip()
                    
                    # Skip simulators
                    if 'Simulator' not in name and udid not in devices:
                        devices[udid] = RealDevice(
                            udid=udid,
                            name=name,
                            model=name,  # instruments doesn't provide model
                            ios_version=ios_version,
                            architecture='Unknown',
                            connection_type='usb',
                            is_connected=True,
                            trusted=True
                        )
        except Exception as e:
            # Silent failure - don't print warning during discovery
            pass
    
    def _connect_wifi_device(self, udid: str, timeout: int) -> None:
        """Connect to a WiFi device."""
        if self.available_tools.get('devicectl'):
            try:
                self.run_command(
                    f"{self.devicectl_path} device connect --device {udid} --timeout {timeout}"
                )
                print(f"✅ Connected to device: {udid}")
            except Exception as e:
                raise DeviceError(f"Failed to connect: {e}")
        else:
            print("⚠️  WiFi connection requires devicectl (Xcode 15+)")
    
    def _disconnect_wifi_device(self, udid: str) -> None:
        """Disconnect from a WiFi device."""
        if self.available_tools.get('devicectl'):
            try:
                self.run_command(f"{self.devicectl_path} device disconnect --device {udid}")
                print(f"✅ Disconnected from device: {udid}")
            except:
                pass
    
    def _install_app_idb(self, udid: str, app_path: str, 
                        developer_team_id: Optional[str]) -> None:
        """Install app using idb."""
        try:
            cmd = f"{self.idb_path} install --udid {udid} '{app_path}'"
            if developer_team_id:
                cmd += f" --team-id {developer_team_id}"
            
            self.run_command(cmd, timeout=120)
            print(f"✅ App installed: {os.path.basename(app_path)}")
        except Exception as e:
            raise DeviceError(f"Failed to install app: {e}")
    
    def _install_app_devicectl(self, udid: str, app_path: str) -> None:
        """Install app using devicectl."""
        try:
            self.run_command(
                f"{self.devicectl_path} device install app --device {udid} --path '{app_path}'"
            )
            print(f"✅ App installed: {os.path.basename(app_path)}")
        except Exception as e:
            raise DeviceError(f"Failed to install app: {e}")