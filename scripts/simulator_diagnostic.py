#!/usr/bin/env python3
"""
iOS Simulator Runtime Diagnostic and Fix Script

This script diagnoses and fixes common iOS simulator runtime issues,
particularly the "Unable to boot device because we cannot determine the runtime bundle" error.
"""

import subprocess
import json
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional


class SimulatorRuntimeFixer:
    """Diagnose and fix iOS simulator runtime issues."""
    
    def __init__(self):
        self.available_runtimes = []
        self.available_devices = []
        self.problematic_devices = []
        
    def run_command(self, cmd: str) -> tuple[int, str, str]:
        """Run shell command and return exit code, stdout, stderr."""
        try:
            result = subprocess.run(
                cmd.split(),
                capture_output=True,
                text=True,
                timeout=30
            )
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return 1, "", "Command timed out"
        except Exception as e:
            return 1, "", str(e)
    
    def get_available_runtimes(self) -> List[Dict]:
        """Get all available iOS runtimes."""
        print("🔍 Checking available iOS runtimes...")
        
        exit_code, stdout, stderr = self.run_command("xcrun simctl list runtimes -j")
        if exit_code != 0:
            print(f"❌ Failed to get runtimes: {stderr}")
            return []
        
        try:
            data = json.loads(stdout)
            self.available_runtimes = data.get('runtimes', [])
            
            print(f"✅ Found {len(self.available_runtimes)} runtimes:")
            for runtime in self.available_runtimes:
                available = "✅" if runtime.get('isAvailable', False) else "❌"
                print(f"   {available} {runtime.get('name', 'Unknown')} - {runtime.get('identifier', 'Unknown')}")
            
            return self.available_runtimes
            
        except json.JSONDecodeError as e:
            print(f"❌ Failed to parse runtimes JSON: {e}")
            return []
    
    def get_all_devices(self) -> List[Dict]:
        """Get all simulators with their runtime info."""
        print("\n🔍 Checking all simulators...")
        
        exit_code, stdout, stderr = self.run_command("xcrun simctl list devices -j")
        if exit_code != 0:
            print(f"❌ Failed to get devices: {stderr}")
            return []
        
        try:
            data = json.loads(stdout)
            devices_by_runtime = data.get('devices', {})
            
            all_devices = []
            for runtime_id, devices in devices_by_runtime.items():
                for device in devices:
                    device['runtime_id'] = runtime_id
                    all_devices.append(device)
            
            self.available_devices = all_devices
            print(f"✅ Found {len(all_devices)} simulators total")
            
            return all_devices
            
        except json.JSONDecodeError as e:
            print(f"❌ Failed to parse devices JSON: {e}")
            return []
    
    def diagnose_runtime_issues(self):
        """Diagnose which devices have runtime issues."""
        print("\n🩺 Diagnosing runtime issues...")
        
        available_runtime_ids = {r.get('identifier') for r in self.available_runtimes if r.get('isAvailable')}
        
        self.problematic_devices = []
        healthy_devices = []
        
        for device in self.available_devices:
            runtime_id = device.get('runtime_id', '')
            device_name = device.get('name', 'Unknown')
            device_udid = device.get('udid', 'Unknown')
            
            if runtime_id not in available_runtime_ids:
                self.problematic_devices.append(device)
                print(f"❌ {device_name} ({device_udid[:8]}...) - Missing runtime: {runtime_id}")
            else:
                healthy_devices.append(device)
        
        print(f"\n📊 Diagnosis Results:")
        print(f"   ✅ Healthy devices: {len(healthy_devices)}")
        print(f"   ❌ Problematic devices: {len(self.problematic_devices)}")
        
        if self.problematic_devices:
            print(f"\n🔧 Devices that need fixing:")
            for device in self.problematic_devices:
                print(f"   • {device.get('name')} - {device.get('udid')}")
    
    def suggest_fixes(self):
        """Suggest fixes for the issues found."""
        print(f"\n💡 Recommended Fixes:")
        
        if not self.problematic_devices:
            print("✅ No issues found! All simulators should work correctly.")
            return
        
        print(f"\n1. 🗑️  DELETE PROBLEMATIC SIMULATORS")
        print(f"   The easiest fix is to delete simulators with missing runtimes:")
        for device in self.problematic_devices:
            udid = device.get('udid')
            name = device.get('name')
            print(f"   xcrun simctl delete {udid}  # {name}")
        
        print(f"\n2. 📱 CREATE NEW SIMULATORS")
        print(f"   Create new simulators with available runtimes:")
        
        # Find the latest available iOS runtime
        ios_runtimes = [r for r in self.available_runtimes 
                       if r.get('isAvailable') and 'iOS' in r.get('name', '')]
        
        if ios_runtimes:
            latest_runtime = max(ios_runtimes, key=lambda x: x.get('version', '0.0'))
            runtime_id = latest_runtime.get('identifier')
            
            device_types = [
                "iPhone 14 Pro",
                "iPhone 15", 
                "iPad Pro (11-inch) (4th generation)"
            ]
            
            for device_type in device_types:
                clean_name = device_type.replace(' ', '_').replace('(', '').replace(')', '')
                print(f"   xcrun simctl create \"{device_type}_Fixed\" \"{device_type}\" \"{runtime_id}\"")
        
        print(f"\n3. 🔄 RESET SIMULATOR SERVICE")
        print(f"   If issues persist, reset the simulator service:")
        print(f"   sudo killall -9 com.apple.CoreSimulator.CoreSimulatorService")
        print(f"   xcrun simctl shutdown all")
        print(f"   xcrun simctl erase all")
        
        print(f"\n4. 🛠️  REINSTALL XCODE SIMULATORS")
        print(f"   In Xcode → Settings → Platforms → iOS")
        print(f"   Download the latest iOS simulator runtime")
    
    def auto_fix_problematic_devices(self, confirm: bool = False):
        """Automatically fix problematic devices by deleting and recreating them."""
        if not self.problematic_devices:
            print("✅ No devices need fixing.")
            return
        
        print(f"\n🔧 Auto-fix mode:")
        print(f"   Will delete {len(self.problematic_devices)} problematic simulators")
        print(f"   Will create new working simulators")
        
        if not confirm:
            response = input(f"\n⚠️  This will delete {len(self.problematic_devices)} simulators. Continue? (y/N): ")
            if response.lower() != 'y':
                print("❌ Auto-fix cancelled.")
                return
        
        # Delete problematic devices
        print(f"\n🗑️  Deleting problematic devices...")
        for device in self.problematic_devices:
            udid = device.get('udid')
            name = device.get('name')
            print(f"   Deleting {name}...")
            
            exit_code, stdout, stderr = self.run_command(f"xcrun simctl delete {udid}")
            if exit_code == 0:
                print(f"   ✅ Deleted {name}")
            else:
                print(f"   ❌ Failed to delete {name}: {stderr}")
        
        # Create new devices
        print(f"\n📱 Creating new simulators...")
        self._create_replacement_simulators()
    
    def _create_replacement_simulators(self):
        """Create replacement simulators with available runtimes."""
        # Find best iOS runtime
        ios_runtimes = [r for r in self.available_runtimes 
                       if r.get('isAvailable') and 'iOS' in r.get('name', '')]
        
        if not ios_runtimes:
            print("❌ No iOS runtimes available for creating new simulators")
            return
        
        # Use latest iOS runtime
        latest_runtime = max(ios_runtimes, key=lambda x: x.get('version', '0.0'))
        runtime_id = latest_runtime.get('identifier')
        runtime_name = latest_runtime.get('name')
        
        print(f"   Using runtime: {runtime_name}")
        
        # Create essential device types
        devices_to_create = [
            ("iPhone 14 Pro", "iPhone 14 Pro"),
            ("iPhone 15", "iPhone 15"), 
            ("iPad Pro 11", "iPad Pro (11-inch) (4th generation)")
        ]
        
        for device_name, device_type in devices_to_create:
            print(f"   Creating {device_name}...")
            
            exit_code, stdout, stderr = self.run_command(
                f"xcrun simctl create \"{device_name}\" \"{device_type}\" \"{runtime_id}\""
            )
            
            if exit_code == 0:
                print(f"   ✅ Created {device_name}")
            else:
                print(f"   ❌ Failed to create {device_name}: {stderr}")
    
    def test_fixed_simulators(self):
        """Test that the fixed simulators can boot properly."""
        print(f"\n🧪 Testing fixed simulators...")
        
        # Get updated device list
        self.get_all_devices()
        
        # Find iPhone simulators to test
        iphone_simulators = [
            d for d in self.available_devices 
            if 'iPhone' in d.get('name', '') and d.get('state') == 'Shutdown'
        ]
        
        if not iphone_simulators:
            print("❌ No iPhone simulators found to test")
            return
        
        # Test boot the first iPhone simulator
        test_device = iphone_simulators[0]
        device_name = test_device.get('name')
        device_udid = test_device.get('udid')
        
        print(f"   Testing boot: {device_name}")
        
        exit_code, stdout, stderr = self.run_command(f"xcrun simctl boot {device_udid}")
        
        if exit_code == 0:
            print(f"   ✅ {device_name} booted successfully!")
            
            # Shutdown the test device
            print(f"   Shutting down test device...")
            self.run_command(f"xcrun simctl shutdown {device_udid}")
            print(f"   ✅ Test completed successfully")
            
        else:
            print(f"   ❌ Failed to boot {device_name}: {stderr}")
    
    def run_full_diagnostic(self, auto_fix: bool = False):
        """Run complete diagnostic and fix process."""
        print("🍎 iOS Simulator Runtime Diagnostic Tool")
        print("=" * 50)
        
        # Step 1: Check runtimes
        self.get_available_runtimes()
        
        # Step 2: Check devices
        self.get_all_devices()
        
        # Step 3: Diagnose issues
        self.diagnose_runtime_issues()
        
        # Step 4: Suggest or apply fixes
        if auto_fix and self.problematic_devices:
            self.auto_fix_problematic_devices(confirm=True)
            self.test_fixed_simulators()
        else:
            self.suggest_fixes()
        
        print(f"\n✅ Diagnostic complete!")


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="iOS Simulator Runtime Diagnostic and Fix Tool")
    parser.add_argument("--auto-fix", action="store_true", 
                       help="Automatically fix problematic simulators")
    parser.add_argument("--test-only", action="store_true",
                       help="Only run diagnostics, don't suggest fixes")
    
    args = parser.parse_args()
    
    fixer = SimulatorRuntimeFixer()
    
    if args.test_only:
        fixer.get_available_runtimes()
        fixer.get_all_devices() 
        fixer.diagnose_runtime_issues()
    else:
        fixer.run_full_diagnostic(auto_fix=args.auto_fix)


if __name__ == "__main__":
    main()