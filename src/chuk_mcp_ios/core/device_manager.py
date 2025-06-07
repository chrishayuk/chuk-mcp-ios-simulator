#!/usr/bin/env python3
# chuk_mcp_ios/core/device_manager.py
"""
Unified device manager that handles both simulators and real iOS devices.
"""

import json
import time
from typing import List, Optional, Dict, Any
from .base import (
    DeviceControllerInterface,
    CommandExecutor,
    DeviceInfo,
    DeviceType,
    DeviceState,
    DeviceNotFoundError,
    DeviceNotAvailableError,
    detect_available_tools
)

class UnifiedDeviceManager(CommandExecutor, DeviceControllerInterface):
    """
    Unified device manager supporting both iOS simulators and real devices.
    Automatically detects and uses available tools.
    """
    
    def __init__(self):
        super().__init__()
        self.available_tools = detect_available_tools()
        self._device_cache = {}
        self._cache_timeout = 30
        self._last_cache_time = 0
        
        # Initialize specific managers based on available tools
        self.simulator_manager = None
        self.real_device_manager = None
        
        if self.available_tools['simctl']:
            from ..devices.simulator import SimulatorManager
            self.simulator_manager = SimulatorManager()
        
        if self.available_tools['idb'] or self.available_tools['devicectl']:
            from ..devices.real_device import RealDeviceManager
            self.real_device_manager = RealDeviceManager()
    
    def discover_all_devices(self, refresh_cache: bool = False) -> List[DeviceInfo]:
        """Discover all available devices (simulators and real devices)."""
        import time
        current_time = time.time()
        
        # Use cache if valid
        if (not refresh_cache and 
            self._device_cache and 
            current_time - self._last_cache_time < self._cache_timeout):
            return self._device_cache.get('all_devices', [])
        
        all_devices = []
        
        # Discover simulators
        if self.simulator_manager:
            try:
                simulators = self.simulator_manager.list_simulators()
                # Fix: Convert SimulatorDevice to DeviceInfo properly
                for sim in simulators:
                    device_info = sim.to_device_info()
                    all_devices.append(device_info)
            except Exception as e:
                # Silent failure during discovery
                pass
        
        # Discover real devices
        if self.real_device_manager:
            try:
                real_devices = self.real_device_manager.list_devices()
                # Fix: Convert RealDevice to DeviceInfo properly  
                for device in real_devices:
                    device_info = device.to_device_info()
                    all_devices.append(device_info)
            except Exception as e:
                # Silent failure during discovery
                pass
        
        # Update cache
        self._device_cache = {'all_devices': all_devices}
        self._last_cache_time = current_time
        
        return all_devices

    def get_device(self, udid: str) -> Optional[DeviceInfo]:
        """Get device by UDID."""
        devices = self.discover_all_devices()
        return next((d for d in devices if d.udid == udid), None)
    
    def get_device_by_name(self, name: str, device_type: Optional[DeviceType] = None) -> Optional[DeviceInfo]:
        """Get device by name with optional type filter."""
        devices = self.discover_all_devices()
        
        for device in devices:
            if device.name == name:
                if device_type is None or device.device_type == device_type:
                    return device
        
        return None
    
    def boot_device(self, udid: str, timeout: int = 30) -> None:
        """Boot/connect to a device."""
        device = self.get_device(udid)
        if not device:
            raise DeviceNotFoundError(f"Device not found: {udid}")
        
        if device.device_type == DeviceType.SIMULATOR:
            if not self.simulator_manager:
                raise DeviceError("Simulator tools not available")
            self.simulator_manager.boot_simulator(udid, timeout)
        else:
            if not self.real_device_manager:
                raise DeviceError("Real device tools not available")
            self.real_device_manager.connect_device(udid, timeout)
    
    def shutdown_device(self, udid: str) -> None:
        """Shutdown/disconnect a device."""
        device = self.get_device(udid)
        if not device:
            raise DeviceNotFoundError(f"Device not found: {udid}")
        
        if device.device_type == DeviceType.SIMULATOR:
            if not self.simulator_manager:
                raise DeviceError("Simulator tools not available")
            self.simulator_manager.shutdown_simulator(udid)
        else:
            # Real devices typically can't be shutdown programmatically
            print(f"Note: Cannot shutdown real device {device.name}")
    
    def is_device_available(self, udid: str) -> bool:
        """Check if device is available."""
        device = self.get_device(udid)
        if not device:
            return False
        
        return device.state in [DeviceState.BOOTED, DeviceState.CONNECTED]
    
    def get_device_info(self, udid: str) -> Optional[DeviceInfo]:
        """Get device information."""
        return self.get_device(udid)
    
    def get_available_devices(self, device_type: Optional[DeviceType] = None) -> List[DeviceInfo]:
        """Get available (connected/booted) devices."""
        devices = self.discover_all_devices()
        available = [d for d in devices if d.state in [DeviceState.BOOTED, DeviceState.CONNECTED]]
        
        if device_type:
            available = [d for d in available if d.device_type == device_type]
        
        return available
    
    def wait_for_device(self, udid: str, timeout: int = 30) -> bool:
        """Wait for a device to become available."""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            if self.is_device_available(udid):
                return True
            time.sleep(1)
            self.discover_all_devices(refresh_cache=True)  # Refresh cache
        
        return False
    
    def get_device_capabilities(self, udid: str) -> Dict[str, bool]:
        """Get device capabilities."""
        device = self.get_device(udid)
        if not device:
            return {}
        
        if device.device_type == DeviceType.SIMULATOR:
            return {
                'can_install_apps': True,
                'can_simulate_location': True,
                'can_add_media': True,
                'can_clear_keychain': True,
                'can_erase_device': True,
                'can_change_settings': True,
                'requires_developer_profile': False,
                'supports_debugging': True,
                'supports_ui_automation': True,
                'supports_performance_monitoring': True
            }
        else:  # Real device
            return {
                'can_install_apps': True,  # With developer profile
                'can_simulate_location': True,
                'can_add_media': True,
                'can_clear_keychain': False,
                'can_erase_device': False,
                'can_change_settings': False,
                'requires_developer_profile': True,
                'supports_debugging': True,
                'supports_ui_automation': True,
                'supports_performance_monitoring': True
            }
    
    def erase_device(self, udid: str) -> None:
        """Erase device (simulators only)."""
        device = self.get_device(udid)
        if not device:
            raise DeviceNotFoundError(f"Device not found: {udid}")
        
        if device.device_type != DeviceType.SIMULATOR:
            raise DeviceError("Cannot erase real devices")
        
        if not self.simulator_manager:
            raise DeviceError("Simulator tools not available")
        
        self.simulator_manager.erase_simulator(udid)
    
    def print_device_list(self, show_capabilities: bool = False):
        """Print formatted device list."""
        devices = self.discover_all_devices()
        
        print("\n📱 iOS Devices:")
        print("=" * 80)
        
        # Group by type
        simulators = [d for d in devices if d.device_type == DeviceType.SIMULATOR]
        real_devices = [d for d in devices if d.device_type == DeviceType.REAL_DEVICE]
        
        if simulators:
            print(f"\n🖥️  Simulators ({len(simulators)}):")
            for sim in sorted(simulators, key=lambda x: (x.os_version, x.name)):
                self._print_device(sim, show_capabilities)
        
        if real_devices:
            print(f"\n📱 Real Devices ({len(real_devices)}):")
            for device in sorted(real_devices, key=lambda x: x.name):
                self._print_device(device, show_capabilities)
        
        if not devices:
            print("No devices found")
            print("\nAvailable tools:")
            for tool, available in self.available_tools.items():
                status = "✅" if available else "❌"
                print(f"  {status} {tool}")
    
    def _print_device(self, device: DeviceInfo, show_capabilities: bool):
        """Print a single device."""
        from ..base import format_device_info
        
        print(f"  {format_device_info(device)}")
        print(f"     UDID: {device.udid}")
        print(f"     Model: {device.model}")
        print(f"     Connection: {device.connection_type}")
        
        if show_capabilities:
            caps = self.get_device_capabilities(device.udid)
            enabled = [k.replace('_', ' ') for k, v in caps.items() if v]
            if enabled:
                print(f"     Capabilities: {', '.join(enabled[:3])}")
        print()
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get device statistics."""
        devices = self.discover_all_devices()
        
        return {
            'total_devices': len(devices),
            'simulators': len([d for d in devices if d.device_type == DeviceType.SIMULATOR]),
            'real_devices': len([d for d in devices if d.device_type == DeviceType.REAL_DEVICE]),
            'available_devices': len([d for d in devices if d.state in [DeviceState.BOOTED, DeviceState.CONNECTED]]),
            'tools_available': self.available_tools,
            'cache_age': time.time() - self._last_cache_time if self._last_cache_time else None
        }