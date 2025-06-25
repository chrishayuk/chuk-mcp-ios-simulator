#!/usr/bin/env python3
"""
Dynamic iOS Simulator Cleanup Script

Automatically detects and removes broken iOS simulators by:
1. Checking which iOS runtimes are actually available
2. Finding simulators that reference missing/unavailable runtimes
3. Optionally removing broken simulators
4. Creating replacement simulators with working runtimes

This script is safe and will ask for confirmation before making changes.
"""

import subprocess
import json
import sys
import argparse
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple


class SimulatorCleanup:
    """Dynamic iOS simulator cleanup tool."""
    
    def __init__(self, dry_run: bool = True, verbose: bool = False):
        self.dry_run = dry_run
        self.verbose = verbose
        self.available_runtimes: Dict[str, Dict] = {}
        self.all_simulators: List[Dict] = []
        self.broken_simulators: List[Dict] = []
        self.healthy_simulators: List[Dict] = []
        
    def log(self, message: str, level: str = "INFO"):
        """Log messages with optional verbose mode."""
        if level == "DEBUG" and not self.verbose:
            return
        
        icons = {
            "INFO": "ℹ️",
            "SUCCESS": "✅", 
            "WARNING": "⚠️",
            "ERROR": "❌",
            "DEBUG": "🔍"
        }
        icon = icons.get(level, "•")
        print(f"{icon} {message}")
    
    def run_command(self, cmd: List[str], timeout: int = 30) -> Tuple[int, str, str]:
        """Run command and return exit code, stdout, stderr."""
        try:
            if self.verbose:
                self.log(f"Running: {' '.join(cmd)}", "DEBUG")
                
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return 1, "", f"Command timed out after {timeout}s"
        except Exception as e:
            return 1, "", str(e)
    
    def get_available_runtimes(self) -> bool:
        """Get all available iOS runtimes."""
        self.log("Checking available iOS runtimes...")
        
        exit_code, stdout, stderr = self.run_command(["xcrun", "simctl", "list", "runtimes", "-j"])
        if exit_code != 0:
            self.log(f"Failed to get runtimes: {stderr}", "ERROR")
            return False
        
        try:
            data = json.loads(stdout)
            runtimes = data.get('runtimes', [])
            
            # Build lookup of available runtimes
            self.available_runtimes = {}
            available_count = 0
            
            for runtime in runtimes:
                identifier = runtime.get('identifier', '')
                is_available = runtime.get('isAvailable', False)
                name = runtime.get('name', 'Unknown')
                
                self.available_runtimes[identifier] = {
                    'name': name,
                    'available': is_available,
                    'identifier': identifier
                }
                
                if is_available:
                    available_count += 1
                    self.log(f"Available: {name} ({identifier})", "DEBUG")
                else:
                    self.log(f"Unavailable: {name} ({identifier})", "DEBUG")
            
            self.log(f"Found {len(runtimes)} total runtimes, {available_count} available", "SUCCESS")
            return available_count > 0
            
        except json.JSONDecodeError as e:
            self.log(f"Failed to parse runtimes JSON: {e}", "ERROR")
            return False
    
    def get_all_simulators(self) -> bool:
        """Get all simulators and categorize them."""
        self.log("Scanning all simulators...")
        
        exit_code, stdout, stderr = self.run_command(["xcrun", "simctl", "list", "devices", "-j"])
        if exit_code != 0:
            self.log(f"Failed to get devices: {stderr}", "ERROR")
            return False
        
        try:
            data = json.loads(stdout)
            devices_by_runtime = data.get('devices', {})
            
            self.all_simulators = []
            self.broken_simulators = []
            self.healthy_simulators = []
            
            for runtime_id, devices in devices_by_runtime.items():
                runtime_info = self.available_runtimes.get(runtime_id, {})
                runtime_available = runtime_info.get('available', False)
                runtime_name = runtime_info.get('name', runtime_id)
                
                for device in devices:
                    # Enhance device info
                    device['runtime_id'] = runtime_id
                    device['runtime_name'] = runtime_name
                    device['runtime_available'] = runtime_available
                    
                    self.all_simulators.append(device)
                    
                    # Categorize device
                    device_name = device.get('name', 'Unknown')
                    device_state = device.get('state', 'Unknown')
                    
                    # Check if device is broken
                    is_broken = (
                        not runtime_available or  # Runtime not available
                        runtime_id == 'com.apple.CoreSimulator.SimRuntime.iOS-unavailable' or  # Explicitly unavailable
                        'unavailable' in runtime_id.lower()  # Contains unavailable
                    )
                    
                    if is_broken:
                        self.broken_simulators.append(device)
                        self.log(f"Broken: {device_name} - {runtime_name}", "DEBUG")
                    else:
                        self.healthy_simulators.append(device)
                        self.log(f"Healthy: {device_name} - {runtime_name}", "DEBUG")
            
            self.log(f"Found {len(self.all_simulators)} total simulators", "SUCCESS")
            self.log(f"  Healthy: {len(self.healthy_simulators)}", "SUCCESS")
            self.log(f"  Broken: {len(self.broken_simulators)}", "WARNING")
            
            return True
            
        except json.JSONDecodeError as e:
            self.log(f"Failed to parse devices JSON: {e}", "ERROR")
            return False
    
    def analyze_broken_simulators(self):
        """Analyze and display broken simulators."""
        if not self.broken_simulators:
            self.log("No broken simulators found!", "SUCCESS")
            return
        
        self.log(f"Analyzing {len(self.broken_simulators)} broken simulators:", "WARNING")
        
        # Group by issue type
        by_runtime = {}
        for device in self.broken_simulators:
            runtime_id = device.get('runtime_id', 'unknown')
            if runtime_id not in by_runtime:
                by_runtime[runtime_id] = []
            by_runtime[runtime_id].append(device)
        
        for runtime_id, devices in by_runtime.items():
            runtime_name = devices[0].get('runtime_name', runtime_id)
            self.log(f"\nRuntime: {runtime_name} ({len(devices)} devices)")
            
            for device in devices:
                name = device.get('name', 'Unknown')
                udid = device.get('udid', 'Unknown')
                state = device.get('state', 'Unknown')
                
                # Show device type icon
                if 'iPhone' in name:
                    icon = "📱"
                elif 'iPad' in name:
                    icon = "📟"
                else:
                    icon = "📺"
                
                self.log(f"  {icon} {name} ({state}) - {udid[:8]}...", "WARNING")
    
    def remove_broken_simulators(self, confirm: bool = False) -> bool:
        """Remove broken simulators."""
        if not self.broken_simulators:
            self.log("No broken simulators to remove", "SUCCESS")
            return True
        
        self.log(f"Preparing to remove {len(self.broken_simulators)} broken simulators")
        
        if self.dry_run:
            self.log("DRY RUN MODE - No changes will be made", "WARNING")
            for device in self.broken_simulators:
                name = device.get('name', 'Unknown')
                udid = device.get('udid', 'Unknown')
                self.log(f"Would delete: {name} ({udid})", "INFO")
            return True
        
        if not confirm:
            print(f"\n⚠️  This will permanently delete {len(self.broken_simulators)} simulators.")
            print("Broken simulators to be removed:")
            for device in self.broken_simulators:
                name = device.get('name', 'Unknown')
                print(f"  • {name}")
            
            response = input(f"\nContinue with deletion? (y/N): ").strip().lower()
            if response != 'y':
                self.log("Deletion cancelled by user", "INFO")
                return False
        
        # Shutdown all simulators first
        self.log("Shutting down all simulators...")
        self.run_command(["xcrun", "simctl", "shutdown", "all"])
        
        # Delete broken simulators
        success_count = 0
        fail_count = 0
        
        for device in self.broken_simulators:
            name = device.get('name', 'Unknown')
            udid = device.get('udid', 'Unknown')
            
            self.log(f"Deleting: {name}...")
            
            exit_code, stdout, stderr = self.run_command(["xcrun", "simctl", "delete", udid])
            
            if exit_code == 0:
                success_count += 1
                self.log(f"Deleted: {name}", "SUCCESS")
            else:
                fail_count += 1
                self.log(f"Failed to delete {name}: {stderr}", "ERROR")
        
        self.log(f"Deletion complete: {success_count} successful, {fail_count} failed")
        return fail_count == 0
    
    def create_replacement_simulators(self, device_types: Optional[List[str]] = None) -> bool:
        """Create replacement simulators with available runtimes."""
        # Find best iOS runtime
        ios_runtimes = [
            r for r in self.available_runtimes.values()
            if r['available'] and 'iOS' in r['name']
        ]
        
        if not ios_runtimes:
            self.log("No available iOS runtimes for creating simulators", "ERROR")
            return False
        
        # Use the latest iOS runtime
        best_runtime = max(ios_runtimes, key=lambda x: x['name'])
        runtime_id = best_runtime['identifier']
        runtime_name = best_runtime['name']
        
        self.log(f"Using runtime: {runtime_name}")
        
        # Default device types to create
        if device_types is None:
            device_types = [
                ("iPhone 15 Pro", "iPhone 15 Pro"),
                ("iPhone 15", "iPhone 15"),
                ("iPad Pro 11", "iPad Pro (11-inch) (4th generation)")
            ]
        
        if self.dry_run:
            self.log("DRY RUN MODE - Simulators would be created:", "WARNING")
            for name, device_type in device_types:
                self.log(f"Would create: {name} ({device_type}) with {runtime_name}", "INFO")
            return True
        
        success_count = 0
        for name, device_type in device_types:
            self.log(f"Creating: {name}...")
            
            exit_code, stdout, stderr = self.run_command([
                "xcrun", "simctl", "create", name, device_type, runtime_id
            ])
            
            if exit_code == 0:
                success_count += 1
                self.log(f"Created: {name}", "SUCCESS")
            else:
                self.log(f"Failed to create {name}: {stderr}", "ERROR")
        
        return success_count > 0
    
    def test_simulator_boot(self) -> bool:
        """Test that at least one simulator can boot."""
        self.log("Testing simulator boot capability...")
        
        # Find an iPhone simulator to test
        iphone_sims = [
            s for s in self.healthy_simulators
            if 'iPhone' in s.get('name', '') and s.get('state') == 'Shutdown'
        ]
        
        if not iphone_sims:
            self.log("No iPhone simulators available for testing", "WARNING")
            return False
        
        test_sim = iphone_sims[0]
        name = test_sim.get('name', 'Unknown')
        udid = test_sim.get('udid', 'Unknown')
        
        if self.dry_run:
            self.log(f"DRY RUN: Would test boot {name}", "INFO")
            return True
        
        self.log(f"Testing boot: {name}")
        
        # Try to boot
        exit_code, stdout, stderr = self.run_command(
            ["xcrun", "simctl", "boot", udid], 
            timeout=60
        )
        
        if exit_code == 0:
            self.log(f"Boot test successful: {name}", "SUCCESS")
            
            # Shutdown test simulator
            self.run_command(["xcrun", "simctl", "shutdown", udid])
            return True
        else:
            self.log(f"Boot test failed: {stderr}", "ERROR")
            return False
    
    def run_cleanup(self, create_replacements: bool = True, test_boot: bool = True) -> bool:
        """Run the complete cleanup process."""
        self.log("🧹 iOS Simulator Cleanup Tool", "INFO")
        self.log("=" * 40, "INFO")
        
        if self.dry_run:
            self.log("RUNNING IN DRY-RUN MODE - No changes will be made", "WARNING")
        
        # Step 1: Get available runtimes
        if not self.get_available_runtimes():
            return False
        
        # Step 2: Scan all simulators
        if not self.get_all_simulators():
            return False
        
        # Step 3: Analyze broken simulators
        self.analyze_broken_simulators()
        
        # Step 4: Remove broken simulators
        if self.broken_simulators:
            if not self.remove_broken_simulators():
                return False
        
        # Step 5: Create replacement simulators
        if create_replacements and not self.dry_run:
            self.create_replacement_simulators()
        
        # Step 6: Test simulator boot
        if test_boot:
            self.test_simulator_boot()
        
        # Final summary
        self.log("\n📊 Cleanup Summary:", "INFO")
        self.log(f"  Total simulators scanned: {len(self.all_simulators)}")
        self.log(f"  Broken simulators found: {len(self.broken_simulators)}")
        self.log(f"  Healthy simulators: {len(self.healthy_simulators)}")
        
        if not self.dry_run and self.broken_simulators:
            self.log("  Broken simulators removed: ✅")
            if create_replacements:
                self.log("  Replacement simulators created: ✅")
        
        self.log("\n✅ Cleanup completed!", "SUCCESS")
        return True


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Dynamic iOS Simulator Cleanup Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Dry run (safe, shows what would be done)
  python simulator_cleanup.py --dry-run
  
  # Actually perform cleanup
  python simulator_cleanup.py --execute
  
  # Cleanup with verbose output
  python simulator_cleanup.py --execute --verbose
  
  # Just analyze, don't create replacements
  python simulator_cleanup.py --execute --no-create
        """
    )
    
    parser.add_argument(
        "--dry-run", 
        action="store_true", 
        default=True,
        help="Show what would be done without making changes (default)"
    )
    
    parser.add_argument(
        "--execute", 
        action="store_true",
        help="Actually perform the cleanup (overrides --dry-run)"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show detailed output"
    )
    
    parser.add_argument(
        "--no-create",
        action="store_true", 
        help="Don't create replacement simulators"
    )
    
    parser.add_argument(
        "--no-test",
        action="store_true",
        help="Don't test simulator boot"
    )
    
    args = parser.parse_args()
    
    # Determine if this is a dry run
    dry_run = args.dry_run and not args.execute
    
    cleanup = SimulatorCleanup(dry_run=dry_run, verbose=args.verbose)
    
    success = cleanup.run_cleanup(
        create_replacements=not args.no_create,
        test_boot=not args.no_test
    )
    
    if not success:
        sys.exit(1)
    
    if dry_run:
        print(f"\n💡 To actually perform cleanup, run:")
        print(f"   python {sys.argv[0]} --execute")


if __name__ == "__main__":
    main()