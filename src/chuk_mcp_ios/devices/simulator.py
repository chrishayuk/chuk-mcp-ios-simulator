#!/usr/bin/env python3
# src/chuk_mcp_ios/devices/simulator.py
"""
iOS Simulator specific implementation.

Handles all simulator-specific operations using xcrun simctl and other tools.
"""

import os
import json
import time
import plistlib
import shutil
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
    DeviceNotAvailableError
)

@dataclass
class SimulatorDevice:
    """Represents an iOS simulator device."""
    udid: str
    name: str
    state: str
    runtime: str
    device_type_identifier: str
    is_available: bool
    data_path: Optional[Path] = None
    log_path: Optional[Path] = None
    
    def to_device_info(self) -> DeviceInfo:
        """Convert to generic DeviceInfo."""
        return DeviceInfo(
            udid=self.udid,
            name=self.name,
            state=self._normalize_state(self.state),
            device_type=DeviceType.SIMULATOR,
            os_version=self._extract_os_version(self.runtime),
            model=self.device_type_identifier,
            connection_type='simulator',
            is_available=self.is_available
        )
    
    def _normalize_state(self, state: str) -> DeviceState:
        """Normalize simulator state to DeviceState."""
        state_map = {
            'Booted': DeviceState.BOOTED,
            'Shutdown': DeviceState.SHUTDOWN,
            'Booting': DeviceState.BOOTED,
            'Shutting Down': DeviceState.SHUTDOWN
        }
        return state_map.get(state, DeviceState.UNKNOWN)
    
    def _extract_os_version(self, runtime: str) -> str:
        """Extract OS version from runtime string."""
        # Convert "com.apple.CoreSimulator.SimRuntime.iOS-16-4" to "iOS 16.4"
        parts = runtime.replace('com.apple.CoreSimulator.SimRuntime.', '').split('-')
        if len(parts) >= 3:
            return f"{parts[0]} {parts[1]}.{parts[2]}"
        return runtime

class SimulatorManager(CommandExecutor):
    """
    Manages iOS simulators using xcrun simctl.
    """
    
    def __init__(self):
        super().__init__()
        self.simulator_app_path = "/Applications/Xcode.app/Contents/Developer/Applications/Simulator.app"
        self._runtime_cache = None
        self._device_type_cache = None
    
    # Device Discovery and Management
    
    def list_simulators(self, refresh: bool = False) -> List[SimulatorDevice]:
        """List all available simulators."""
        try:
            result = self.run_command(f"{self.simctl_path} list devices -j")
            data = json.loads(result.stdout)
            
            simulators = []
            for runtime, devices in data['devices'].items():
                for device in devices:
                    sim = SimulatorDevice(
                        udid=device['udid'],
                        name=device['name'],
                        state=device['state'],
                        runtime=runtime,
                        device_type_identifier=device.get('deviceTypeIdentifier', ''),
                        is_available=device.get('isAvailable', True)
                    )
                    
                    # Add data paths
                    sim.data_path = self._get_simulator_data_path(sim.udid)
                    sim.log_path = self._get_simulator_log_path(sim.udid)
                    
                    simulators.append(sim)
            
            return simulators
            
        except Exception as e:
            raise DeviceError(f"Failed to list simulators: {e}")
    
    def get_simulator(self, udid: str) -> Optional[SimulatorDevice]:
        """Get specific simulator by UDID."""
        simulators = self.list_simulators()
        return next((s for s in simulators if s.udid == udid), None)
    
    def get_booted_simulators(self) -> List[SimulatorDevice]:
        """Get all booted simulators."""
        simulators = self.list_simulators()
        return [s for s in simulators if s.state == 'Booted']
    
    def create_simulator(self, name: str, device_type: str, runtime: str) -> SimulatorDevice:
        """
        Create a new simulator.
        
        Args:
            name: Simulator name
            device_type: Device type identifier (e.g., "iPhone 14")
            runtime: Runtime identifier (e.g., "iOS 16.4")
            
        Returns:
            SimulatorDevice: Created simulator
        """
        try:
            # Get proper identifiers
            device_type_id = self._get_device_type_identifier(device_type)
            runtime_id = self._get_runtime_identifier(runtime)
            
            # Create simulator
            result = self.run_command(
                f"{self.simctl_path} create '{name}' {device_type_id} {runtime_id}"
            )
            
            udid = result.stdout.strip()
            
            # Get the created simulator
            simulator = self.get_simulator(udid)
            if not simulator:
                raise DeviceError("Failed to get created simulator")
            
            print(f"✅ Created simulator: {name} ({udid})")
            return simulator
            
        except Exception as e:
            raise DeviceError(f"Failed to create simulator: {e}")
    
    def delete_simulator(self, udid: str) -> None:
        """Delete a simulator."""
        try:
            self.run_command(f"{self.simctl_path} delete {udid}")
            print(f"✅ Deleted simulator: {udid}")
        except Exception as e:
            raise DeviceError(f"Failed to delete simulator: {e}")
    
    def clone_simulator(self, source_udid: str, new_name: str) -> SimulatorDevice:
        """Clone an existing simulator."""
        source = self.get_simulator(source_udid)
        if not source:
            raise DeviceNotFoundError(f"Source simulator not found: {source_udid}")
        
        try:
            # Get device type from source
            device_type = source.device_type_identifier.split('.')[-1]
            runtime = source.runtime.split('.')[-1]
            
            # Create new simulator
            new_sim = self.create_simulator(new_name, device_type, runtime)
            
            # Clone data if source is shutdown
            if source.state == 'Shutdown':
                self._clone_simulator_data(source_udid, new_sim.udid)
            
            return new_sim
            
        except Exception as e:
            raise DeviceError(f"Failed to clone simulator: {e}")
    
    # Simulator Lifecycle
    
    def boot_simulator(self, udid: str, timeout: int = 60) -> None:
        """Boot a simulator."""
        simulator = self.get_simulator(udid)
        if not simulator:
            raise DeviceNotFoundError(f"Simulator not found: {udid}")
        
        if simulator.state == 'Booted':
            print(f"Simulator {simulator.name} is already booted")
            return
        
        try:
            print(f"Booting {simulator.name}...")
            self.run_command(f"{self.simctl_path} boot {udid}")
            
            # Wait for boot completion
            start_time = time.time()
            while time.time() - start_time < timeout:
                sim = self.get_simulator(udid)
                if sim and sim.state == 'Booted':
                    # Open Simulator app
                    self._open_simulator_app()
                    time.sleep(2)  # Allow UI to settle
                    print(f"✅ Simulator {simulator.name} booted successfully")
                    return
                time.sleep(1)
            
            raise DeviceError(f"Timeout waiting for simulator to boot")
            
        except Exception as e:
            raise DeviceError(f"Failed to boot simulator: {e}")
    
    def shutdown_simulator(self, udid: str) -> None:
        """Shutdown a simulator."""
        simulator = self.get_simulator(udid)
        if not simulator:
            raise DeviceNotFoundError(f"Simulator not found: {udid}")
        
        if simulator.state == 'Shutdown':
            print(f"Simulator {simulator.name} is already shutdown")
            return
        
        try:
            self.run_command(f"{self.simctl_path} shutdown {udid}")
            print(f"✅ Simulator {simulator.name} shutdown")
        except Exception as e:
            raise DeviceError(f"Failed to shutdown simulator: {e}")
    
    def erase_simulator(self, udid: str) -> None:
        """Erase simulator content and settings."""
        simulator = self.get_simulator(udid)
        if not simulator:
            raise DeviceNotFoundError(f"Simulator not found: {udid}")
        
        # Shutdown first if booted
        if simulator.state == 'Booted':
            self.shutdown_simulator(udid)
            time.sleep(2)
        
        try:
            self.run_command(f"{self.simctl_path} erase {udid}")
            print(f"✅ Simulator {simulator.name} erased")
        except Exception as e:
            raise DeviceError(f"Failed to erase simulator: {e}")
    
    def rename_simulator(self, udid: str, new_name: str) -> None:
        """Rename a simulator."""
        try:
            self.run_command(f"{self.simctl_path} rename {udid} '{new_name}'")
            print(f"✅ Simulator renamed to: {new_name}")
        except Exception as e:
            raise DeviceError(f"Failed to rename simulator: {e}")
    
    # Simulator-specific Operations
    
    def take_screenshot(self, udid: str, output_path: str) -> str:
        """Take a screenshot of the simulator."""
        simulator = self.get_simulator(udid)
        if not simulator or simulator.state != 'Booted':
            raise DeviceNotAvailableError("Simulator must be booted")
        
        try:
            self.run_command(f"{self.simctl_path} io {udid} screenshot '{output_path}'")
            return output_path
        except Exception as e:
            raise DeviceError(f"Failed to take screenshot: {e}")
    
    def record_video(self, udid: str, output_path: str, options: Optional[Dict[str, Any]] = None) -> None:
        """Start video recording (must be stopped manually)."""
        simulator = self.get_simulator(udid)
        if not simulator or simulator.state != 'Booted':
            raise DeviceNotAvailableError("Simulator must be booted")
        
        try:
            cmd = f"{self.simctl_path} io {udid} recordVideo"
            
            if options:
                if options.get('codec'):
                    cmd += f" --codec {options['codec']}"
                if options.get('mask'):
                    cmd += f" --mask {options['mask']}"
                if options.get('force'):
                    cmd += " --force"
            
            cmd += f" '{output_path}'"
            
            # This will start recording in background
            import subprocess
            subprocess.Popen(cmd, shell=True)
            print(f"📹 Started recording to: {output_path}")
            print("   Press Ctrl+C in the terminal to stop recording")
            
        except Exception as e:
            raise DeviceError(f"Failed to start recording: {e}")
    
    def set_status_bar(self, udid: str, time: Optional[str] = None, 
                      battery_level: Optional[int] = None,
                      cellular_bars: Optional[int] = None,
                      wifi_bars: Optional[int] = None) -> None:
        """Override status bar appearance."""
        simulator = self.get_simulator(udid)
        if not simulator or simulator.state != 'Booted':
            raise DeviceNotAvailableError("Simulator must be booted")
        
        try:
            cmd = f"{self.simctl_path} status_bar {udid} override"
            
            if time:
                cmd += f" --time '{time}'"
            if battery_level is not None:
                cmd += f" --batteryLevel {battery_level}"
            if cellular_bars is not None:
                cmd += f" --cellularBars {cellular_bars}"
            if wifi_bars is not None:
                cmd += f" --wifiBars {wifi_bars}"
            
            self.run_command(cmd)
            print("✅ Status bar overridden")
            
        except Exception as e:
            raise DeviceError(f"Failed to set status bar: {e}")
    
    def clear_status_bar(self, udid: str) -> None:
        """Clear status bar overrides."""
        try:
            self.run_command(f"{self.simctl_path} status_bar {udid} clear")
            print("✅ Status bar cleared")
        except Exception as e:
            raise DeviceError(f"Failed to clear status bar: {e}")
    
    def trigger_icloud_sync(self, udid: str) -> None:
        """Trigger iCloud sync."""
        try:
            self.run_command(
                f"{self.simctl_path} spawn {udid} notifyutil -p com.apple.icloud.sync"
            )
            print("✅ iCloud sync triggered")
        except Exception as e:
            raise DeviceError(f"Failed to trigger iCloud sync: {e}")
    
    def simulate_memory_warning(self, udid: str) -> None:
        """Simulate memory warning."""
        try:
            self.run_command(
                f"{self.simctl_path} spawn {udid} memory_pressure -S critical"
            )
            print("✅ Memory warning simulated")
        except Exception as e:
            raise DeviceError(f"Failed to simulate memory warning: {e}")
    
    def get_app_container(self, udid: str, bundle_id: str, 
                         container_type: str = 'app') -> Optional[Path]:
        """
        Get app container path.
        
        Args:
            udid: Simulator UDID
            bundle_id: App bundle identifier
            container_type: Type of container (app, data, groups)
            
        Returns:
            Path to container or None
        """
        try:
            result = self.run_command(
                f"{self.simctl_path} get_app_container {udid} {bundle_id} {container_type}"
            )
            
            path_str = result.stdout.strip()
            if path_str and os.path.exists(path_str):
                return Path(path_str)
            
            return None
            
        except Exception:
            return None
    
    def install_app(self, udid: str, app_path: str) -> None:
        """Install an app on the simulator."""
        if not os.path.exists(app_path):
            raise FileNotFoundError(f"App not found: {app_path}")
        
        try:
            self.run_command(f"{self.simctl_path} install {udid} '{app_path}'")
            print(f"✅ App installed: {os.path.basename(app_path)}")
        except Exception as e:
            raise DeviceError(f"Failed to install app: {e}")
    
    def uninstall_app(self, udid: str, bundle_id: str) -> None:
        """Uninstall an app from the simulator."""
        try:
            self.run_command(f"{self.simctl_path} uninstall {udid} {bundle_id}")
            print(f"✅ App uninstalled: {bundle_id}")
        except Exception as e:
            raise DeviceError(f"Failed to uninstall app: {e}")
    
    def launch_app(self, udid: str, bundle_id: str, args: Optional[List[str]] = None) -> None:
        """Launch an app on the simulator."""
        try:
            cmd = f"{self.simctl_path} launch {udid} {bundle_id}"
            if args:
                cmd += " " + " ".join(args)
            
            self.run_command(cmd)
            print(f"✅ App launched: {bundle_id}")
        except Exception as e:
            raise DeviceError(f"Failed to launch app: {e}")
    
    def terminate_app(self, udid: str, bundle_id: str) -> None:
        """Terminate an app on the simulator."""
        try:
            self.run_command(f"{self.simctl_path} terminate {udid} {bundle_id}")
            print(f"✅ App terminated: {bundle_id}")
        except Exception as e:
            # App might not be running
            pass
    
    def get_device_info(self, udid: str) -> Dict[str, Any]:
        """Get detailed device information."""
        simulator = self.get_simulator(udid)
        if not simulator:
            raise DeviceNotFoundError(f"Simulator not found: {udid}")
        
        info = {
            'udid': simulator.udid,
            'name': simulator.name,
            'state': simulator.state,
            'runtime': simulator.runtime,
            'device_type': simulator.device_type_identifier,
            'is_available': simulator.is_available,
            'data_path': str(simulator.data_path) if simulator.data_path else None,
            'log_path': str(simulator.log_path) if simulator.log_path else None
        }
        
        # Add runtime info
        runtime_info = self._get_runtime_info(simulator.runtime)
        if runtime_info:
            info['runtime_info'] = runtime_info
        
        # Add device type info  
        device_info = self._get_device_type_info(simulator.device_type_identifier)
        if device_info:
            info['device_info'] = device_info
        
        return info
    
    # Helper Methods
    
    def _get_simulator_data_path(self, udid: str) -> Optional[Path]:
        """Get simulator data directory path."""
        path = Path.home() / "Library/Developer/CoreSimulator/Devices" / udid
        return path if path.exists() else None
    
    def _get_simulator_log_path(self, udid: str) -> Optional[Path]:
        """Get simulator log directory path."""
        path = Path.home() / "Library/Logs/CoreSimulator" / udid
        return path if path.exists() else None
    
    def _open_simulator_app(self) -> None:
        """Open the Simulator application."""
        try:
            self.run_command(f"open -a Simulator")
        except:
            # Try alternate path
            if os.path.exists(self.simulator_app_path):
                self.run_command(f"open '{self.simulator_app_path}'")
    
    def _clone_simulator_data(self, source_udid: str, dest_udid: str) -> None:
        """Clone data from one simulator to another."""
        source_path = self._get_simulator_data_path(source_udid)
        dest_path = self._get_simulator_data_path(dest_udid)
        
        if not source_path or not dest_path:
            raise DeviceError("Cannot access simulator data paths")
        
        # Copy specific directories
        dirs_to_copy = ['data/Containers', 'data/Library']
        
        for dir_name in dirs_to_copy:
            src_dir = source_path / dir_name
            if src_dir.exists():
                dst_dir = dest_path / dir_name
                if dst_dir.exists():
                    shutil.rmtree(dst_dir)
                shutil.copytree(src_dir, dst_dir)
    
    def _get_device_type_identifier(self, device_type: str) -> str:
        """Convert device type name to identifier."""
        if not self._device_type_cache:
            self._load_device_types()
        
        # Try exact match first
        for dt in self._device_type_cache:
            if dt['name'] == device_type:
                return dt['identifier']
        
        # Try partial match
        for dt in self._device_type_cache:
            if device_type.lower() in dt['name'].lower():
                return dt['identifier']
        
        raise ValueError(f"Unknown device type: {device_type}")
    
    def _get_runtime_identifier(self, runtime: str) -> str:
        """Convert runtime name to identifier."""
        if not self._runtime_cache:
            self._load_runtimes()
        
        # Try exact match first
        for rt in self._runtime_cache:
            if rt['name'] == runtime:
                return rt['identifier']
        
        # Try partial match
        for rt in self._runtime_cache:
            if runtime.lower() in rt['name'].lower():
                return rt['identifier']
        
        raise ValueError(f"Unknown runtime: {runtime}")
    
    def _load_device_types(self) -> None:
        """Load available device types."""
        try:
            result = self.run_command(f"{self.simctl_path} list devicetypes -j")
            data = json.loads(result.stdout)
            self._device_type_cache = data.get('devicetypes', [])
        except:
            self._device_type_cache = []
    
    def _load_runtimes(self) -> None:
        """Load available runtimes."""
        try:
            result = self.run_command(f"{self.simctl_path} list runtimes -j")
            data = json.loads(result.stdout)
            self._runtime_cache = data.get('runtimes', [])
        except:
            self._runtime_cache = []
    
    def _get_runtime_info(self, runtime_id: str) -> Optional[Dict[str, Any]]:
        """Get runtime information."""
        if not self._runtime_cache:
            self._load_runtimes()
        
        for rt in self._runtime_cache:
            if rt.get('identifier') == runtime_id:
                return rt
        
        return None
    
    def _get_device_type_info(self, device_type_id: str) -> Optional[Dict[str, Any]]:
        """Get device type information."""
        if not self._device_type_cache:
            self._load_device_types()
        
        for dt in self._device_type_cache:
            if dt.get('identifier') == device_type_id:
                return dt
        
        return None
    
    # Status Bar Presets
    
    def set_demo_status_bar(self, udid: str) -> None:
        """Set status bar to demo-friendly appearance."""
        self.set_status_bar(
            udid,
            time="9:41",  # Apple's standard demo time
            battery_level=100,
            cellular_bars=4,
            wifi_bars=3
        )
    
    def set_screenshot_status_bar(self, udid: str) -> None:
        """Set status bar for screenshots."""
        self.set_status_bar(
            udid,
            time="9:41",
            battery_level=100,
            cellular_bars=4,
            wifi_bars=3
        )