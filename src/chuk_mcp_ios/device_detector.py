#!/usr/bin/env python3
# chuk_mcp_ios/device_detector.py
"""
Device Detector Module
Enhanced device detection supporting both simulators and real iOS devices.
"""

import json
import re
from typing import List, Dict, Optional, Union
from dataclasses import dataclass
from enum import Enum
from ios_simulator_base import CommandExecutor

class DeviceType(Enum):
    SIMULATOR = "simulator"
    REAL_DEVICE = "real_device"

@dataclass
class UnifiedDeviceInfo:
    """Unified device information for both simulators and real devices."""
    udid: str
    name: str
    state: str
    device_type: DeviceType
    os_version: str
    model: str
    connection_type: str  # usb, wifi, simulator
    architecture: Optional[str] = None
    is_available: bool = True

class DeviceDetector(CommandExecutor):
    """
    Enhanced device detection supporting both iOS simulators and real devices.
    Provides unified interface for device discovery and management.
    """
    
    def __init__(self):
        super().__init__()
        self._device_cache = {}
        self._cache_timeout = 30
        self._last_cache_time = 0
    
    def discover_all_devices(self, refresh_cache: bool = False) -> List[UnifiedDeviceInfo]:
        """
        Discover all available devices (simulators and real devices).
        
        Args:
            refresh_cache: Force refresh of device cache
            
        Returns:
            List[UnifiedDeviceInfo]: All discovered devices
        """
        import time
        current_time = time.time()
        
        # Use cache if valid
        if (not refresh_cache and 
            self._device_cache and 
            current_time - self._last_cache_time < self._cache_timeout):
            return self._device_cache.get('all_devices', [])
        
        all_devices = []
        
        # Discover simulators
        try:
            simulators = self._discover_simulators()
            all_devices.extend(simulators)
        except Exception as e:
            print(f"Warning: Could not discover simulators: {e}")
        
        # Discover real devices
        try:
            real_devices = self._discover_real_devices()
            all_devices.extend(real_devices)
        except Exception as e:
            print(f"Warning: Could not discover real devices: {e}")
        
        # Update cache
        self._device_cache = {'all_devices': all_devices}
        self._last_cache_time = current_time
        
        return all_devices
    
    def _discover_simulators(self) -> List[UnifiedDeviceInfo]:
        """Discover iOS simulators."""
        result = self.run_command(f"{self.simctl_path} list devices --json")
        data = json.loads(result.stdout)
        simulators = []
        
        for runtime_name, devices in data['devices'].items():
            for device in devices:
                simulators.append(UnifiedDeviceInfo(
                    udid=device['udid'],
                    name=device['name'],
                    state='Booted' if device['state'] == 'Booted' else 'Shutdown',
                    device_type=DeviceType.SIMULATOR,
                    os_version=self._extract_os_version(runtime_name),
                    model=device.get('deviceTypeIdentifier', 'Unknown'),
                    connection_type='simulator',
                    is_available=device['isAvailable']
                ))
        
        return simulators
    
    def _discover_real_devices(self) -> List[UnifiedDeviceInfo]:
        """Discover real iOS devices using multiple methods."""
        devices = []
        
        # Method 1: Try idb list-targets
        try:
            devices.extend(self._discover_via_idb())
        except Exception as e:
            print(f"IDB discovery failed: {e}")
        
        # Method 2: Try instruments -s devices
        try:
            devices.extend(self._discover_via_instruments())
        except Exception as e:
            print(f"Instruments discovery failed: {e}")
        
        # Method 3: Try xcrun devicectl (Xcode 15+)
        try:
            devices.extend(self._discover_via_devicectl())
        except Exception as e:
            print(f"Devicectl discovery failed: {e}")
        
        # Remove duplicates based on UDID
        unique_devices = {}
        for device in devices:
            if device.udid not in unique_devices:
                unique_devices[device.udid] = device
        
        return list(unique_devices.values())
    
    def _discover_via_idb(self) -> List[UnifiedDeviceInfo]:
        """Discover devices using idb list-targets."""
        try:
            result = self.run_command(f"{self.idb_path} list-targets --json")
            targets = json.loads(result.stdout)
            
            devices = []
            for target in targets:
                if target.get('type') == 'device':  # Real device
                    devices.append(UnifiedDeviceInfo(
                        udid=target.get('udid', ''),
                        name=target.get('name', 'Unknown Device'),
                        state='Connected' if target.get('state') == 'connected' else 'Disconnected',
                        device_type=DeviceType.REAL_DEVICE,
                        os_version=target.get('os_version', 'Unknown'),
                        model=target.get('model', 'Unknown'),
                        connection_type='usb' if target.get('connection_type') == 'usb' else 'wifi',
                        architecture=target.get('architecture')
                    ))
            
            return devices
        except Exception:
            return []
    
    def _discover_via_instruments(self) -> List[UnifiedDeviceInfo]:
        """Discover devices using instruments command."""
        try:
            result = self.run_command("instruments -s devices")
            lines = result.stdout.split('\n')
            
            devices = []
            for line in lines:
                line = line.strip()
                # Parse format: "iPhone Name (15.0) [UDID]" or "iPhone Name [UDID]"
                device_match = re.match(r'^(.+?)\s*(?:\(([^)]+)\))?\s*\[([A-F0-9-]{36})\]', line)
                
                if device_match and len(device_match.group(3)) == 36:  # Real device UDID format
                    name = device_match.group(1).strip()
                    os_version = device_match.group(2) or 'Unknown'
                    udid = device_match.group(3)
                    
                    # Skip simulator entries
                    if 'Simulator' not in name and 'simulator' not in name.lower():
                        devices.append(UnifiedDeviceInfo(
                            udid=udid,
                            name=name,
                            state='Connected',
                            device_type=DeviceType.REAL_DEVICE,
                            os_version=os_version,
                            model=name,
                            connection_type='usb'
                        ))
            
            return devices
        except Exception:
            return []
    
    def _discover_via_devicectl(self) -> List[UnifiedDeviceInfo]:
        """Discover devices using xcrun devicectl (Xcode 15+)."""
        try:
            result = self.run_command("xcrun devicectl list devices --json")
            data = json.loads(result.stdout)
            
            devices = []
            for device_data in data.get('result', {}).get('devices', []):
                device_props = device_data.get('deviceProperties', {})
                hardware_props = device_data.get('hardwareProperties', {})
                
                devices.append(UnifiedDeviceInfo(
                    udid=device_data.get('identifier', ''),
                    name=device_props.get('name', 'Unknown Device'),
                    state='Connected' if device_data.get('connectionProperties', {}).get('transportType') else 'Disconnected',
                    device_type=DeviceType.REAL_DEVICE,
                    os_version=device_props.get('osVersionNumber', 'Unknown'),
                    model=hardware_props.get('marketingName', 'Unknown'),
                    connection_type=device_data.get('connectionProperties', {}).get('transportType', 'unknown').lower(),
                    architecture=hardware_props.get('cpuType', {}).get('name')
                ))
            
            return devices
        except Exception:
            return []
    
    def get_simulators_only(self) -> List[UnifiedDeviceInfo]:
        """Get only simulator devices."""
        all_devices = self.discover_all_devices()
        return [d for d in all_devices if d.device_type == DeviceType.SIMULATOR]
    
    def get_real_devices_only(self) -> List[UnifiedDeviceInfo]:
        """Get only real devices."""
        all_devices = self.discover_all_devices()
        return [d for d in all_devices if d.device_type == DeviceType.REAL_DEVICE]
    
    def get_connected_devices(self) -> List[UnifiedDeviceInfo]:
        """Get only connected/booted devices."""
        all_devices = self.discover_all_devices()
        return [d for d in all_devices if d.state in ['Booted', 'Connected']]
    
    def find_device_by_name(self, name: str, device_type: Optional[DeviceType] = None) -> Optional[UnifiedDeviceInfo]:
        """
        Find a device by name with optional type filter.
        
        Args:
            name: Device name to search for
            device_type: Optional device type filter
            
        Returns:
            Optional[UnifiedDeviceInfo]: Found device or None
        """
        all_devices = self.discover_all_devices()
        
        for device in all_devices:
            if device.name == name:
                if device_type is None or device.device_type == device_type:
                    return device
        
        return None
    
    def find_device_by_udid(self, udid: str) -> Optional[UnifiedDeviceInfo]:
        """Find a device by UDID."""
        all_devices = self.discover_all_devices()
        return next((d for d in all_devices if d.udid == udid), None)
    
    def is_real_device(self, udid: str) -> bool:
        """Check if a UDID belongs to a real device."""
        device = self.find_device_by_udid(udid)
        return device is not None and device.device_type == DeviceType.REAL_DEVICE
    
    def is_simulator(self, udid: str) -> bool:
        """Check if a UDID belongs to a simulator."""
        device = self.find_device_by_udid(udid)
        return device is not None and device.device_type == DeviceType.SIMULATOR
    
    def get_device_capabilities(self, udid: str) -> Dict[str, bool]:
        """
        Get device capabilities based on type.
        
        Args:
            udid: Device UDID
            
        Returns:
            Dict[str, bool]: Capability flags
        """
        device = self.find_device_by_udid(udid)
        
        if not device:
            return {}
        
        if device.device_type == DeviceType.SIMULATOR:
            return {
                'can_install_apps': True,
                'can_simulate_location': True,
                'can_add_media': True,
                'can_clear_keychain': True,
                'can_erase_device': True,
                'can_change_device_settings': True,
                'requires_developer_profile': False,
                'supports_debugging': True
            }
        else:  # Real device
            return {
                'can_install_apps': True,  # With developer profile
                'can_simulate_location': True,
                'can_add_media': True,
                'can_clear_keychain': False,  # Limited on real devices
                'can_erase_device': False,  # Cannot erase real devices
                'can_change_device_settings': False,  # Limited access
                'requires_developer_profile': True,
                'supports_debugging': True
            }
    
    def _extract_os_version(self, runtime_name: str) -> str:
        """Extract OS version from runtime name."""
        # Convert "com.apple.CoreSimulator.SimRuntime.iOS-16-0" to "iOS 16.0"
        cleaned = runtime_name.replace('com.apple.CoreSimulator.SimRuntime.', '')
        parts = cleaned.split('-')
        if len(parts) >= 3:
            os_name = parts[0]
            major = parts[1]
            minor = parts[2] if len(parts) > 2 else '0'
            return f"{os_name} {major}.{minor}"
        return cleaned
    
    def print_device_list(self, show_capabilities: bool = False):
        """Print a formatted list of all devices."""
        devices = self.discover_all_devices()
        
        print("\n📱 All Available Devices:")
        print("=" * 80)
        
        # Group by type
        simulators = [d for d in devices if d.device_type == DeviceType.SIMULATOR]
        real_devices = [d for d in devices if d.device_type == DeviceType.REAL_DEVICE]
        
        if simulators:
            print(f"\n🖥️  Simulators ({len(simulators)}):")
            for sim in simulators:
                state_emoji = "🟢" if sim.state == 'Booted' else "⚪"
                print(f"  {state_emoji} {sim.name}")
                print(f"     UDID: {sim.udid}")
                print(f"     OS: {sim.os_version}")
                print(f"     State: {sim.state}")
                if show_capabilities:
                    caps = self.get_device_capabilities(sim.udid)
                    print(f"     Capabilities: {', '.join([k for k, v in caps.items() if v])}")
                print()
        
        if real_devices:
            print(f"\n📱 Real Devices ({len(real_devices)}):")
            for device in real_devices:
                state_emoji = "🟢" if device.state == 'Connected' else "🔴"
                print(f"  {state_emoji} {device.name}")
                print(f"     UDID: {device.udid}")
                print(f"     OS: {device.os_version}")
                print(f"     Model: {device.model}")
                print(f"     Connection: {device.connection_type}")
                print(f"     State: {device.state}")
                if show_capabilities:
                    caps = self.get_device_capabilities(device.udid)
                    print(f"     Capabilities: {', '.join([k for k, v in caps.items() if v])}")
                print()
        
        if not devices:
            print("No devices found")
    
    def wait_for_device_connection(self, udid: str, timeout: int = 30) -> bool:
        """
        Wait for a specific device to become available.
        
        Args:
            udid: Device UDID to wait for
            timeout: Maximum wait time in seconds
            
        Returns:
            bool: True if device became available
        """
        import time
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            device = self.find_device_by_udid(udid)
            if device and device.state in ['Booted', 'Connected']:
                return True
            time.sleep(1)
        
        return False