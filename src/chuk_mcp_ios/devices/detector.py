#!/usr/bin/env python3
# src/chuk_mcp_ios/devices/detector.py
"""
Unified device detection and discovery.

Provides a unified interface for discovering both simulators and real devices.
"""

import time
from typing import List, Optional, Dict, Any, Union
from dataclasses import dataclass

from ..core.base import (
    DeviceInfo,
    DeviceType,
    DeviceState,
    detect_available_tools
)
from .simulator import SimulatorManager, SimulatorDevice
from .real_device import RealDeviceManager, RealDevice

@dataclass
class UnifiedDevice:
    """
    Unified device representation that can be either a simulator or real device.
    """
    info: DeviceInfo
    raw_device: Union[SimulatorDevice, RealDevice]
    
    @property
    def udid(self) -> str:
        return self.info.udid
    
    @property
    def name(self) -> str:
        return self.info.name
    
    @property
    def device_type(self) -> DeviceType:
        return self.info.device_type
    
    @property
    def is_simulator(self) -> bool:
        return self.info.device_type == DeviceType.SIMULATOR
    
    @property
    def is_real_device(self) -> bool:
        return self.info.device_type == DeviceType.REAL_DEVICE
    
    @property
    def is_available(self) -> bool:
        return self.info.is_available
    
    @property
    def state(self) -> DeviceState:
        return self.info.state
    
    def get_capabilities(self) -> Dict[str, bool]:
        """Get device capabilities."""
        if self.is_simulator:
            return {
                'can_install_apps': True,
                'can_simulate_location': True,
                'can_add_media': True,
                'can_clear_keychain': True,
                'can_erase_device': True,
                'can_change_settings': True,
                'can_set_status_bar': True,
                'can_record_video': True,
                'can_take_screenshot': True,
                'requires_developer_profile': False,
                'supports_debugging': True,
                'supports_ui_automation': True,
                'supports_performance_monitoring': True,
                'supports_network_conditioning': True,
                'supports_clipboard': True,
                'supports_memory_warning': True
            }
        else:
            return {
                'can_install_apps': True,
                'can_simulate_location': True,
                'can_add_media': True,
                'can_clear_keychain': False,
                'can_erase_device': False,
                'can_change_settings': False,
                'can_set_status_bar': False,
                'can_record_video': True,
                'can_take_screenshot': True,
                'requires_developer_profile': True,
                'supports_debugging': True,
                'supports_ui_automation': True,
                'supports_performance_monitoring': True,
                'supports_network_conditioning': False,
                'supports_clipboard': False,
                'supports_memory_warning': False
            }

class DeviceDetector:
    """
    Unified device detector that discovers both simulators and real devices.
    """
    
    def __init__(self):
        self.available_tools = detect_available_tools()
        self.simulator_manager = None
        self.real_device_manager = None
        
        # Initialize managers based on available tools
        if self.available_tools.get('simctl'):
            self.simulator_manager = SimulatorManager()
        
        if any(self.available_tools.get(tool) for tool in ['idb', 'devicectl', 'instruments']):
            self.real_device_manager = RealDeviceManager()
        
        # Cache
        self._device_cache: Dict[str, UnifiedDevice] = {}
        self._cache_time = 0
        self._cache_timeout = 10  # seconds
    
    def discover_all_devices(self, refresh: bool = False) -> List[UnifiedDevice]:
        """
        Discover all available devices (simulators and real devices).
        
        Args:
            refresh: Force cache refresh
            
        Returns:
            List of unified devices
        """
        if not refresh and self._is_cache_valid():
            return list(self._device_cache.values())
        
        devices = []
        
        # Discover simulators
        if self.simulator_manager:
            try:
                simulators = self.simulator_manager.list_simulators()
                for sim in simulators:
                    unified = UnifiedDevice(
                        info=sim.to_device_info(),
                        raw_device=sim
                    )
                    devices.append(unified)
            except Exception as e:
                print(f"Warning: Failed to discover simulators: {e}")
        
        # Discover real devices
        if self.real_device_manager:
            try:
                real_devices = self.real_device_manager.list_devices()
                for device in real_devices:
                    unified = UnifiedDevice(
                        info=device.to_device_info(),
                        raw_device=device
                    )
                    devices.append(unified)
            except Exception as e:
                print(f"Warning: Failed to discover real devices: {e}")
        
        # Update cache
        self._device_cache = {d.udid: d for d in devices}
        self._cache_time = time.time()
        
        return devices
    
    def get_device(self, udid: str) -> Optional[UnifiedDevice]:
        """Get device by UDID."""
        # Try cache first
        if udid in self._device_cache and self._is_cache_valid():
            return self._device_cache[udid]
        
        # Refresh and try again
        self.discover_all_devices(refresh=True)
        return self._device_cache.get(udid)
    
    def get_device_by_name(self, name: str, 
                          device_type: Optional[DeviceType] = None) -> Optional[UnifiedDevice]:
        """
        Get device by name with optional type filter.
        
        Args:
            name: Device name
            device_type: Optional device type filter
            
        Returns:
            Unified device or None
        """
        devices = self.discover_all_devices()
        
        for device in devices:
            if device.name == name:
                if device_type is None or device.device_type == device_type:
                    return device
        
        return None
    
    def get_available_devices(self, device_type: Optional[DeviceType] = None) -> List[UnifiedDevice]:
        """
        Get all available (connected/booted) devices.
        
        Args:
            device_type: Optional device type filter
            
        Returns:
            List of available devices
        """
        devices = self.discover_all_devices()
        available = [d for d in devices if d.is_available]
        
        if device_type:
            available = [d for d in available if d.device_type == device_type]
        
        return available
    
    def get_simulators(self) -> List[UnifiedDevice]:
        """Get all simulators."""
        devices = self.discover_all_devices()
        return [d for d in devices if d.is_simulator]
    
    def get_real_devices(self) -> List[UnifiedDevice]:
        """Get all real devices."""
        devices = self.discover_all_devices()
        return [d for d in devices if d.is_real_device]
    
    def find_best_device(self, requirements: Optional[Dict[str, Any]] = None) -> Optional[UnifiedDevice]:
        """
        Find the best device matching requirements.
        
        Args:
            requirements: Optional requirements dict with keys:
                - device_type: DeviceType
                - min_ios_version: str
                - model_contains: str
                - prefer_available: bool
                
        Returns:
            Best matching device or None
        """
        devices = self.discover_all_devices()
        
        if not devices:
            return None
        
        if not requirements:
            # Return first available device
            available = [d for d in devices if d.is_available]
            return available[0] if available else devices[0]
        
        # Filter by requirements
        candidates = devices
        
        if 'device_type' in requirements:
            candidates = [d for d in candidates if d.device_type == requirements['device_type']]
        
        if 'min_ios_version' in requirements:
            min_version = requirements['min_ios_version']
            candidates = [d for d in candidates if self._compare_ios_version(d.info.os_version, min_version) >= 0]
        
        if 'model_contains' in requirements:
            model_str = requirements['model_contains'].lower()
            candidates = [d for d in candidates if model_str in d.info.model.lower()]
        
        if not candidates:
            return None
        
        # Sort by preference
        if requirements.get('prefer_available', True):
            # Prefer available devices
            available = [d for d in candidates if d.is_available]
            if available:
                return available[0]
        
        return candidates[0]
    
    def wait_for_any_device(self, timeout: int = 30, 
                           device_type: Optional[DeviceType] = None) -> Optional[UnifiedDevice]:
        """
        Wait for any device to become available.
        
        Args:
            timeout: Timeout in seconds
            device_type: Optional device type filter
            
        Returns:
            First available device or None
        """
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            available = self.get_available_devices(device_type)
            if available:
                return available[0]
            
            time.sleep(1)
            self.discover_all_devices(refresh=True)
        
        return None
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get device statistics."""
        devices = self.discover_all_devices()
        
        stats = {
            'total_devices': len(devices),
            'simulators': len([d for d in devices if d.is_simulator]),
            'real_devices': len([d for d in devices if d.is_real_device]),
            'available_devices': len([d for d in devices if d.is_available]),
            'available_simulators': len([d for d in devices if d.is_simulator and d.is_available]),
            'available_real_devices': len([d for d in devices if d.is_real_device and d.is_available]),
            'tools_available': self.available_tools,
            'by_ios_version': {},
            'by_model': {}
        }
        
        # Count by iOS version
        for device in devices:
            version = device.info.os_version
            stats['by_ios_version'][version] = stats['by_ios_version'].get(version, 0) + 1
        
        # Count by model
        for device in devices:
            model = device.info.model
            stats['by_model'][model] = stats['by_model'].get(model, 0) + 1
        
        return stats
    
    def print_device_summary(self):
        """Print a summary of all devices."""
        devices = self.discover_all_devices()
        
        if not devices:
            print("No devices found")
            print("\nAvailable tools:")
            for tool, available in self.available_tools.items():
                print(f"  {'✅' if available else '❌'} {tool}")
            return
        
        print(f"\n📱 Device Summary ({len(devices)} total)")
        print("=" * 60)
        
        # Group by type
        simulators = [d for d in devices if d.is_simulator]
        real_devices = [d for d in devices if d.is_real_device]
        
        if simulators:
            print(f"\n🖥️  Simulators ({len(simulators)}):")
            self._print_device_group(simulators)
        
        if real_devices:
            print(f"\n📱 Real Devices ({len(real_devices)}):")
            self._print_device_group(real_devices)
        
        # Statistics
        stats = self.get_statistics()
        print(f"\n📊 Statistics:")
        print(f"   Available: {stats['available_devices']}/{stats['total_devices']}")
        print(f"   iOS Versions: {len(stats['by_ios_version'])}")
        print(f"   Device Models: {len(stats['by_model'])}")
    
    def _print_device_group(self, devices: List[UnifiedDevice]):
        """Print a group of devices."""
        # Sort by availability, then name
        devices.sort(key=lambda d: (not d.is_available, d.name))
        
        for device in devices:
            state_icon = "🟢" if device.is_available else "🔴"
            
            print(f"  {state_icon} {device.name}")
            print(f"      UDID: {device.udid}")
            print(f"      Model: {device.info.model}")
            print(f"      OS: {device.info.os_version}")
            print(f"      State: {device.state.value}")
            
            if device.is_real_device:
                print(f"      Connection: {device.info.connection_type}")
    
    def _is_cache_valid(self) -> bool:
        """Check if cache is still valid."""
        return (time.time() - self._cache_time) < self._cache_timeout
    
    def _compare_ios_version(self, version1: str, version2: str) -> int:
        """
        Compare iOS versions.
        
        Returns:
            -1 if version1 < version2
            0 if version1 == version2
            1 if version1 > version2
        """
        # Extract version numbers
        import re
        
        def extract_version(v: str) -> tuple:
            match = re.search(r'(\d+)\.(\d+)(?:\.(\d+))?', v)
            if match:
                major = int(match.group(1))
                minor = int(match.group(2))
                patch = int(match.group(3) or 0)
                return (major, minor, patch)
            return (0, 0, 0)
        
        v1 = extract_version(version1)
        v2 = extract_version(version2)
        
        if v1 < v2:
            return -1
        elif v1 > v2:
            return 1
        else:
            return 0
    
    # Convenience Methods
    
    def find_iphone_simulator(self, ios_version: Optional[str] = None) -> Optional[UnifiedDevice]:
        """Find an iPhone simulator."""
        requirements = {
            'device_type': DeviceType.SIMULATOR,
            'model_contains': 'iPhone',
            'prefer_available': True
        }
        
        if ios_version:
            requirements['min_ios_version'] = ios_version
        
        return self.find_best_device(requirements)
    
    def find_ipad_simulator(self, ios_version: Optional[str] = None) -> Optional[UnifiedDevice]:
        """Find an iPad simulator."""
        requirements = {
            'device_type': DeviceType.SIMULATOR,
            'model_contains': 'iPad',
            'prefer_available': True
        }
        
        if ios_version:
            requirements['min_ios_version'] = ios_version
        
        return self.find_best_device(requirements)
    
    def find_connected_iphone(self) -> Optional[UnifiedDevice]:
        """Find a connected real iPhone."""
        requirements = {
            'device_type': DeviceType.REAL_DEVICE,
            'model_contains': 'iPhone',
            'prefer_available': True
        }
        
        return self.find_best_device(requirements)
    
    def find_connected_ipad(self) -> Optional[UnifiedDevice]:
        """Find a connected real iPad."""
        requirements = {
            'device_type': DeviceType.REAL_DEVICE,
            'model_contains': 'iPad',
            'prefer_available': True
        }
        
        return self.find_best_device(requirements)