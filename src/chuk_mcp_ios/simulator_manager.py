#!/usr/bin/env python3
# chuk_mcp/simulator_manager.py
"""
Simulator Manager Module
Handles simulator lifecycle operations including boot, shutdown, and discovery.
"""

import json
import time
from typing import Dict, List, Optional
from ios_simulator_base import (
    SimulatorManagerInterface,
    SimulatorInfo,
    CommandExecutor,
    SimulatorError,
    SimulatorNotBootedError
)

class SimulatorManager(CommandExecutor, SimulatorManagerInterface):
    """Manages iOS simulator lifecycle and state operations."""
    
    def __init__(self):
        super().__init__()
        self._simulator_cache = {}
        self._cache_timeout = 30  # Cache simulators for 30 seconds
        self._last_cache_time = 0
    
    def list_available_simulators(self, refresh_cache: bool = False) -> List[SimulatorInfo]:
        """
        List all available simulators with optional caching.
        
        Args:
            refresh_cache: Force refresh of simulator cache
            
        Returns:
            List[SimulatorInfo]: List of available simulators
        """
        current_time = time.time()
        
        # Use cache if it's still valid and not forcing refresh
        if (not refresh_cache and 
            self._simulator_cache and 
            current_time - self._last_cache_time < self._cache_timeout):
            return self._simulator_cache.get('simulators', [])
        
        result = self.run_command(f"{self.simctl_path} list devices --json")
        data = json.loads(result.stdout)
        simulators = []
        
        for runtime_name, devices in data['devices'].items():
            for device in devices:
                state = self._normalize_state(device['state'])
                
                simulators.append(SimulatorInfo(
                    udid=device['udid'],
                    name=device['name'],
                    state=state,
                    os=self._normalize_os_name(runtime_name),
                    device_type=device.get('deviceTypeIdentifier', 'Unknown')
                ))
        
        # Update cache
        self._simulator_cache = {'simulators': simulators}
        self._last_cache_time = current_time
        
        return simulators
    
    def list_booted_simulators(self, refresh_cache: bool = False) -> List[SimulatorInfo]:
        """
        List all currently booted simulators.
        
        Args:
            refresh_cache: Force refresh of simulator cache
            
        Returns:
            List[SimulatorInfo]: List of booted simulators
        """
        simulators = self.list_available_simulators(refresh_cache)
        return [sim for sim in simulators if sim.state == 'Booted']
    
    def boot_simulator_by_udid(self, udid: str, timeout: int = 30) -> None:
        """
        Boot a simulator by UDID with timeout and status monitoring.
        
        Args:
            udid: Simulator UDID to boot
            timeout: Maximum time to wait for boot completion
            
        Raises:
            SimulatorError: If boot fails or times out
        """
        # Check if already booted
        booted = self.list_booted_simulators(refresh_cache=True)
        if any(sim.udid == udid for sim in booted):
            print(f"Simulator {udid} is already booted")
            return
        
        print(f"Booting simulator {udid}...")
        try:
            self.run_command(f"{self.simctl_path} boot {udid}")
        except Exception as e:
            raise SimulatorError(f"Failed to boot simulator {udid}: {str(e)}")
        
        # Wait for boot completion
        attempts = 0
        while attempts < timeout:
            try:
                booted = self.list_booted_simulators(refresh_cache=True)
                if any(sim.udid == udid for sim in booted):
                    print(f"Simulator {udid} booted successfully")
                    time.sleep(2)  # Give it a moment to fully initialize
                    return
            except:
                pass
            
            time.sleep(1)
            attempts += 1
        
        raise SimulatorError(f"Timeout waiting for simulator {udid} to boot after {timeout} seconds")
    
    def shutdown_simulator_by_udid(self, udid: str) -> None:
        """
        Shutdown a simulator by UDID.
        
        Args:
            udid: Simulator UDID to shutdown
            
        Raises:
            SimulatorError: If shutdown fails
        """
        try:
            self.run_command(f"{self.simctl_path} shutdown {udid}")
            print(f"Simulator {udid} shutdown successfully")
            # Invalidate cache after state change
            self._simulator_cache = {}
        except Exception as e:
            raise SimulatorError(f"Failed to shutdown simulator {udid}: {str(e)}")
    
    def shutdown_all_simulators(self) -> None:
        """
        Shutdown all running simulators.
        
        Raises:
            SimulatorError: If shutdown fails
        """
        try:
            self.run_command(f"{self.simctl_path} shutdown all")
            print("All simulators shutdown successfully")
            # Invalidate cache after state change
            self._simulator_cache = {}
        except Exception as e:
            raise SimulatorError(f"Failed to shutdown all simulators: {str(e)}")
    
    def is_simulator_booted(self, udid: str) -> bool:
        """
        Check if a specific simulator is currently booted.
        
        Args:
            udid: Simulator UDID to check
            
        Returns:
            bool: True if simulator is booted
        """
        booted = self.list_booted_simulators(refresh_cache=True)
        return any(sim.udid == udid for sim in booted)
    
    def erase_simulator(self, udid: str) -> None:
        """
        Erase all content and settings from a simulator.
        
        Args:
            udid: Simulator UDID to erase
            
        Raises:
            SimulatorError: If erase fails
        """
        # Ensure simulator is shutdown before erasing
        if self.is_simulator_booted(udid):
            self.shutdown_simulator_by_udid(udid)
            time.sleep(2)  # Wait for shutdown to complete
        
        try:
            self.run_command(f"{self.simctl_path} erase {udid}")
            print(f"Simulator {udid} erased successfully")
        except Exception as e:
            raise SimulatorError(f"Failed to erase simulator {udid}: {str(e)}")
    
    def get_simulator_by_name(self, name: str, os_version: Optional[str] = None) -> Optional[SimulatorInfo]:
        """
        Find a simulator by name and optionally OS version.
        
        Args:
            name: Simulator name to search for
            os_version: Optional OS version filter
            
        Returns:
            Optional[SimulatorInfo]: Found simulator or None
        """
        simulators = self.list_available_simulators()
        
        for sim in simulators:
            if sim.name == name:
                if os_version is None or os_version in sim.os:
                    return sim
        
        return None
    
    def get_simulator_by_udid(self, udid: str) -> Optional[SimulatorInfo]:
        """
        Find a simulator by UDID.
        
        Args:
            udid: Simulator UDID to search for
            
        Returns:
            Optional[SimulatorInfo]: Found simulator or None
        """
        simulators = self.list_available_simulators()
        return next((sim for sim in simulators if sim.udid == udid), None)
    
    def wait_for_simulator_boot(self, udid: str, timeout: int = 60) -> bool:
        """
        Wait for a simulator to complete booting.
        
        Args:
            udid: Simulator UDID to wait for
            timeout: Maximum time to wait
            
        Returns:
            bool: True if simulator is booted within timeout
        """
        attempts = 0
        while attempts < timeout:
            if self.is_simulator_booted(udid):
                return True
            time.sleep(1)
            attempts += 1
        
        return False
    
    def get_simulator_status(self, udid: str) -> Dict[str, any]:
        """
        Get detailed status information for a simulator.
        
        Args:
            udid: Simulator UDID
            
        Returns:
            Dict: Status information including state, device info, etc.
        """
        simulator = self.get_simulator_by_udid(udid)
        if not simulator:
            return {"exists": False}
        
        return {
            "exists": True,
            "udid": simulator.udid,
            "name": simulator.name,
            "state": simulator.state,
            "os": simulator.os,
            "device_type": simulator.device_type,
            "is_booted": simulator.state == 'Booted'
        }
    
    def _normalize_state(self, state: str) -> str:
        """Normalize simulator state strings."""
        state_mapping = {
            'Booted': 'Booted',
            'Shutdown': 'Shutdown',
            'Shutting Down': 'Shutdown',
            'Booting': 'Booted'  # Treat booting as booted for simplicity
        }
        return state_mapping.get(state, 'Unknown')
    
    def _normalize_os_name(self, runtime_name: str) -> str:
        """Normalize OS runtime names to readable format."""
        return runtime_name.replace('com.apple.CoreSimulator.SimRuntime.', '').replace('-', ' ')
    
    def print_device_list(self) -> None:
        """Print a formatted list of available devices."""
        simulators = self.list_available_simulators(refresh_cache=True)
        
        print("\n📱 Available iOS Simulators:")
        print("=" * 70)
        
        # Group by OS
        os_groups = {}
        for sim in simulators:
            if sim.os not in os_groups:
                os_groups[sim.os] = []
            os_groups[sim.os].append(sim)
        
        for os_name, sims in sorted(os_groups.items()):
            print(f"\n{os_name}:")
            for sim in sorted(sims, key=lambda x: x.name):
                state_emoji = "🟢" if sim.state == 'Booted' else "⚪"
                print(f"  {state_emoji} {sim.name}")
                print(f"     UDID: {sim.udid}")
                print(f"     State: {sim.state}")
                print(f"     Type: {sim.device_type}")
                print()