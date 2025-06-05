#!/usr/bin/env python3
"""
iOS Simulator Controller
A Python script to control iOS Simulator using xcrun simctl commands.
"""

import subprocess
import json
import sys
import time
from typing import List, Dict, Optional

class iOSSimulatorController:
    def __init__(self):
        self.simctl_path = "xcrun simctl"
    
    def _run_command(self, command: str) -> subprocess.CompletedProcess:
        """Execute a shell command and return the result."""
        try:
            result = subprocess.run(
                command, 
                shell=True, 
                capture_output=True, 
                text=True, 
                check=True
            )
            return result
        except subprocess.CalledProcessError as e:
            print(f"Error executing command: {command}")
            print(f"Error: {e.stderr}")
            raise e
    
    def list_devices(self) -> Dict:
        """List all available simulators."""
        command = f"{self.simctl_path} list devices --json"
        result = self._run_command(command)
        return json.loads(result.stdout)
    
    def get_booted_devices(self) -> List[Dict]:
        """Get list of currently booted simulators."""
        devices = self.list_devices()
        booted = []
        
        for runtime, device_list in devices['devices'].items():
            for device in device_list:
                if device['state'] == 'Booted':
                    device['runtime'] = runtime
                    booted.append(device)
        
        return booted
    
    def boot_simulator(self, device_id: str) -> bool:
        """Boot a simulator by device ID."""
        try:
            command = f"{self.simctl_path} boot {device_id}"
            self._run_command(command)
            print(f"Successfully booted simulator: {device_id}")
            return True
        except subprocess.CalledProcessError:
            print(f"Failed to boot simulator: {device_id}")
            return False
    
    def shutdown_simulator(self, device_id: str) -> bool:
        """Shutdown a simulator by device ID."""
        try:
            command = f"{self.simctl_path} shutdown {device_id}"
            self._run_command(command)
            print(f"Successfully shutdown simulator: {device_id}")
            return True
        except subprocess.CalledProcessError:
            print(f"Failed to shutdown simulator: {device_id}")
            return False
    
    def shutdown_all(self) -> bool:
        """Shutdown all running simulators."""
        try:
            command = f"{self.simctl_path} shutdown all"
            self._run_command(command)
            print("Successfully shutdown all simulators")
            return True
        except subprocess.CalledProcessError:
            print("Failed to shutdown all simulators")
            return False
    
    def erase_simulator(self, device_id: str) -> bool:
        """Erase all content and settings from a simulator."""
        try:
            command = f"{self.simctl_path} erase {device_id}"
            self._run_command(command)
            print(f"Successfully erased simulator: {device_id}")
            return True
        except subprocess.CalledProcessError:
            print(f"Failed to erase simulator: {device_id}")
            return False
    
    def install_app(self, device_id: str, app_path: str) -> bool:
        """Install an app on the simulator."""
        try:
            command = f"{self.simctl_path} install {device_id} '{app_path}'"
            self._run_command(command)
            print(f"Successfully installed app: {app_path}")
            return True
        except subprocess.CalledProcessError:
            print(f"Failed to install app: {app_path}")
            return False
    
    def launch_app(self, device_id: str, bundle_id: str) -> bool:
        """Launch an app by bundle identifier."""
        try:
            command = f"{self.simctl_path} launch {device_id} {bundle_id}"
            self._run_command(command)
            print(f"Successfully launched app: {bundle_id}")
            return True
        except subprocess.CalledProcessError:
            print(f"Failed to launch app: {bundle_id}")
            return False
    
    def terminate_app(self, device_id: str, bundle_id: str) -> bool:
        """Terminate an app by bundle identifier."""
        try:
            command = f"{self.simctl_path} terminate {device_id} {bundle_id}"
            self._run_command(command)
            print(f"Successfully terminated app: {bundle_id}")
            return True
        except subprocess.CalledProcessError:
            print(f"Failed to terminate app: {bundle_id}")
            return False
    
    def take_screenshot(self, device_id: str, output_path: str) -> bool:
        """Take a screenshot of the simulator."""
        try:
            command = f"{self.simctl_path} io {device_id} screenshot '{output_path}'"
            self._run_command(command)
            print(f"Screenshot saved to: {output_path}")
            return True
        except subprocess.CalledProcessError:
            print(f"Failed to take screenshot")
            return False
    
    def record_video(self, device_id: str, output_path: str, duration: int = 10) -> bool:
        """Record video from the simulator."""
        try:
            command = f"timeout {duration} {self.simctl_path} io {device_id} recordVideo '{output_path}'"
            self._run_command(command)
            print(f"Video recorded to: {output_path}")
            return True
        except subprocess.CalledProcessError:
            print(f"Failed to record video")
            return False
    
    def send_push_notification(self, device_id: str, bundle_id: str, payload_file: str) -> bool:
        """Send a push notification to an app."""
        try:
            command = f"{self.simctl_path} push {device_id} {bundle_id} '{payload_file}'"
            self._run_command(command)
            print(f"Push notification sent to: {bundle_id}")
            return True
        except subprocess.CalledProcessError:
            print(f"Failed to send push notification")
            return False
    
    def set_location(self, device_id: str, latitude: float, longitude: float) -> bool:
        """Set the location of the simulator."""
        try:
            command = f"{self.simctl_path} location {device_id} set {latitude} {longitude}"
            self._run_command(command)
            print(f"Location set to: {latitude}, {longitude}")
            return True
        except subprocess.CalledProcessError:
            print(f"Failed to set location")
            return False
    
    def print_device_list(self):
        """Print a formatted list of available devices."""
        devices = self.list_devices()
        
        print("\n📱 Available iOS Simulators:")
        print("=" * 50)
        
        for runtime, device_list in devices['devices'].items():
            if device_list:  # Only show runtimes that have devices
                print(f"\n{runtime}:")
                for device in device_list:
                    state_emoji = "🟢" if device['state'] == 'Booted' else "⚪"
                    print(f"  {state_emoji} {device['name']} ({device['udid'][:8]}...)")
                    print(f"     State: {device['state']}")

def main():
    controller = iOSSimulatorController()
    
    if len(sys.argv) < 2:
        print("iOS Simulator Controller")
        print("\nUsage:")
        print("  python ios_simulator.py list                    - List all devices")
        print("  python ios_simulator.py boot <device_id>        - Boot a device")
        print("  python ios_simulator.py shutdown <device_id>    - Shutdown a device")
        print("  python ios_simulator.py shutdown_all            - Shutdown all devices")
        print("  python ios_simulator.py screenshot <device_id> <path> - Take screenshot")
        print("  python ios_simulator.py install <device_id> <app_path> - Install app")
        print("  python ios_simulator.py launch <device_id> <bundle_id> - Launch app")
        return
    
    command = sys.argv[1]
    
    try:
        if command == "list":
            controller.print_device_list()
        
        elif command == "boot" and len(sys.argv) >= 3:
            device_id = sys.argv[2]
            controller.boot_simulator(device_id)
        
        elif command == "shutdown" and len(sys.argv) >= 3:
            device_id = sys.argv[2]
            controller.shutdown_simulator(device_id)
        
        elif command == "shutdown_all":
            controller.shutdown_all()
        
        elif command == "screenshot" and len(sys.argv) >= 4:
            device_id = sys.argv[2]
            output_path = sys.argv[3]
            controller.take_screenshot(device_id, output_path)
        
        elif command == "install" and len(sys.argv) >= 4:
            device_id = sys.argv[2]
            app_path = sys.argv[3]
            controller.install_app(device_id, app_path)
        
        elif command == "launch" and len(sys.argv) >= 4:
            device_id = sys.argv[2]
            bundle_id = sys.argv[3]
            controller.launch_app(device_id, bundle_id)
        
        else:
            print("Invalid command or missing arguments")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()