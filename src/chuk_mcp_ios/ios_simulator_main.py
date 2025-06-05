#!/usr/bin/env python3
"""
Simple Standalone iOS Simulator Demo
A self-contained demo that works with just xcrun simctl (no idb required).
"""

import subprocess
import json
import time
import os
from typing import List, Dict, Optional

class SimpleiOSController:
    """Simple iOS simulator controller using only xcrun simctl."""
    
    def __init__(self):
        self.simctl_path = "xcrun simctl"
    
    def run_command(self, command: str, timeout: Optional[int] = None) -> subprocess.CompletedProcess:
        """Execute a shell command and return the result."""
        try:
            result = subprocess.run(
                command, 
                shell=True, 
                capture_output=True, 
                text=True, 
                check=True,
                timeout=timeout
            )
            return result
        except subprocess.CalledProcessError as e:
            print(f"Error executing command: {command}")
            print(f"Error: {e.stderr}")
            raise e
        except subprocess.TimeoutExpired as e:
            print(f"Command timed out: {command}")
            raise e
    
    def check_prerequisites(self):
        """Check if required tools are available."""
        print("🔧 Checking prerequisites...")
        
        # Check simctl
        try:
            self.run_command(f"{self.simctl_path} help")
            print("✅ xcrun simctl is available")
            return True
        except Exception as e:
            print(f"❌ xcrun simctl not available: {e}")
            print("   Please install Xcode and command line tools:")
            print("   xcode-select --install")
            return False
    
    def list_simulators(self) -> List[Dict]:
        """List all available simulators."""
        result = self.run_command(f"{self.simctl_path} list devices --json")
        data = json.loads(result.stdout)
        simulators = []
        
        for runtime_name, devices in data['devices'].items():
            for device in devices:
                simulators.append({
                    'udid': device['udid'],
                    'name': device['name'],
                    'state': device['state'],
                    'os': runtime_name.replace('com.apple.CoreSimulator.SimRuntime.', ''),
                    'available': device.get('isAvailable', True)
                })
        
        return simulators
    
    def print_simulators(self):
        """Print a formatted list of simulators."""
        simulators = self.list_simulators()
        
        print("\n📱 Available iOS Simulators:")
        print("=" * 60)
        
        # Group by OS
        os_groups = {}
        for sim in simulators:
            os_name = sim['os']
            if os_name not in os_groups:
                os_groups[os_name] = []
            os_groups[os_name].append(sim)
        
        for os_name, sims in sorted(os_groups.items()):
            if sims:  # Only show OS versions that have devices
                print(f"\n{os_name}:")
                for sim in sorted(sims, key=lambda x: x['name']):
                    if sim['available']:
                        state_emoji = "🟢" if sim['state'] == 'Booted' else "⚪"
                        print(f"  {state_emoji} {sim['name']}")
                        print(f"     UDID: {sim['udid'][:8]}...")
                        print(f"     State: {sim['state']}")
    
    def get_booted_simulators(self) -> List[Dict]:
        """Get list of booted simulators."""
        simulators = self.list_simulators()
        return [sim for sim in simulators if sim['state'] == 'Booted']
    
    def boot_simulator(self, udid: str) -> bool:
        """Boot a simulator."""
        # Check if already booted
        booted = self.get_booted_simulators()
        if any(sim['udid'] == udid for sim in booted):
            print(f"Simulator {udid[:8]}... is already booted")
            return True
        
        try:
            print(f"Booting simulator {udid[:8]}...")
            self.run_command(f"{self.simctl_path} boot {udid}")
            
            # Wait for boot
            for i in range(30):  # 30 second timeout
                booted = self.get_booted_simulators()
                if any(sim['udid'] == udid for sim in booted):
                    print(f"✅ Simulator booted successfully")
                    time.sleep(2)  # Allow full initialization
                    return True
                time.sleep(1)
            
            print(f"❌ Timeout waiting for simulator to boot")
            return False
            
        except Exception as e:
            print(f"❌ Failed to boot simulator: {e}")
            return False
    
    def shutdown_simulator(self, udid: str) -> bool:
        """Shutdown a simulator."""
        try:
            self.run_command(f"{self.simctl_path} shutdown {udid}")
            print(f"✅ Simulator {udid[:8]}... shutdown")
            return True
        except Exception as e:
            print(f"❌ Failed to shutdown simulator: {e}")
            return False
    
    def take_screenshot(self, udid: str, output_path: str) -> bool:
        """Take a screenshot using simctl."""
        try:
            self.run_command(f"{self.simctl_path} io {udid} screenshot '{output_path}'")
            print(f"📸 Screenshot saved: {output_path}")
            return True
        except Exception as e:
            print(f"❌ Failed to take screenshot: {e}")
            return False
    
    def launch_app(self, udid: str, bundle_id: str) -> bool:
        """Launch an app using simctl."""
        try:
            self.run_command(f"{self.simctl_path} launch {udid} {bundle_id}")
            print(f"🚀 Launched app: {bundle_id}")
            return True
        except Exception as e:
            print(f"❌ Failed to launch app {bundle_id}: {e}")
            return False
    
    def terminate_app(self, udid: str, bundle_id: str) -> bool:
        """Terminate an app using simctl."""
        try:
            self.run_command(f"{self.simctl_path} terminate {udid} {bundle_id}")
            print(f"🛑 Terminated app: {bundle_id}")
            return True
        except Exception as e:
            print(f"⚠️  Could not terminate app {bundle_id}: {e}")
            return False
    
    def set_location(self, udid: str, latitude: float, longitude: float) -> bool:
        """Set simulator location."""
        try:
            self.run_command(f"{self.simctl_path} location {udid} set {latitude} {longitude}")
            print(f"📍 Location set to: {latitude}, {longitude}")
            return True
        except Exception as e:
            print(f"❌ Failed to set location: {e}")
            return False
    
    def add_photos(self, udid: str, photo_paths: List[str]) -> bool:
        """Add photos to simulator using simctl."""
        try:
            # Validate files exist
            valid_photos = [p for p in photo_paths if os.path.exists(p)]
            if not valid_photos:
                print("❌ No valid photo files found")
                return False
            
            photos_str = ' '.join([f"'{p}'" for p in valid_photos])
            self.run_command(f"{self.simctl_path} addmedia {udid} {photos_str}")
            print(f"📸 Added {len(valid_photos)} photos to simulator")
            return True
        except Exception as e:
            print(f"❌ Failed to add photos: {e}")
            return False
    
    def open_url(self, udid: str, url: str) -> bool:
        """Open URL in simulator."""
        try:
            self.run_command(f"{self.simctl_path} openurl {udid} '{url}'")
            print(f"🔗 Opened URL: {url}")
            return True
        except Exception as e:
            print(f"❌ Failed to open URL: {e}")
            return False
    
    def simulate_hardware_button(self, udid: str, button: str) -> bool:
        """Simulate hardware button press."""
        try:
            # Available buttons: home, lock, volume-up, volume-down, etc.
            self.run_command(f"{self.simctl_path} device {udid} hardware {button}")
            print(f"🔘 Pressed {button} button")
            return True
        except Exception as e:
            print(f"❌ Failed to press {button} button: {e}")
            return False

def run_quick_demo():
    """Run a quick demonstration of key features."""
    print("⚡ Quick iOS Simulator Demo (simctl only)")
    print("=" * 50)
    
    controller = SimpleiOSController()
    
    # Check prerequisites
    if not controller.check_prerequisites():
        print("❌ Prerequisites not met. Please install Xcode and command line tools.")
        return
    
    try:
        # Show available simulators
        print("\n1️⃣  Listing available simulators...")
        controller.print_simulators()
        
        # Find a suitable simulator
        simulators = controller.list_simulators()
        available_sims = [s for s in simulators if s['available'] and 'iPhone' in s['name']]
        
        if not available_sims:
            print("❌ No available iPhone simulators found")
            return
        
        # Use the first available iPhone simulator
        target_sim = available_sims[0]
        udid = target_sim['udid']
        name = target_sim['name']
        
        print(f"\n2️⃣  Selected simulator: {name}")
        
        # Boot simulator if not already booted
        print(f"\n3️⃣  Ensuring simulator is booted...")
        if not controller.boot_simulator(udid):
            print("❌ Failed to boot simulator")
            return
        
        # Take a screenshot
        print(f"\n4️⃣  Taking initial screenshot...")
        controller.take_screenshot(udid, "demo_initial.png")
        
        # Launch Settings app
        print(f"\n5️⃣  Launching Settings app...")
        controller.launch_app(udid, "com.apple.Preferences")
        time.sleep(3)
        
        # Take screenshot of Settings
        print(f"\n6️⃣  Taking Settings screenshot...")
        controller.take_screenshot(udid, "demo_settings.png")
        
        # Set location to different places
        print(f"\n7️⃣  Testing location simulation...")
        locations = [
            ("San Francisco", 37.7749, -122.4194),
            ("New York", 40.7128, -74.0060),
            ("London", 51.5074, -0.1278)
        ]
        
        for name, lat, lng in locations:
            print(f"   📍 Setting location to {name}...")
            controller.set_location(udid, lat, lng)
            time.sleep(1)
        
        # Launch Maps to see location
        print(f"\n8️⃣  Launching Maps app...")
        controller.launch_app(udid, "com.apple.Maps")
        time.sleep(4)
        
        # Final screenshot
        print(f"\n9️⃣  Taking final screenshot...")
        controller.take_screenshot(udid, "demo_maps.png")
        
        # Test URL opening
        print(f"\n🔟 Testing URL opening...")
        controller.open_url(udid, "https://www.apple.com")
        time.sleep(2)
        
        print(f"\n✅ Demo completed successfully!")
        print(f"📁 Files created:")
        for filename in ["demo_initial.png", "demo_settings.png", "demo_maps.png"]:
            if os.path.exists(filename):
                print(f"   📸 {filename}")
        
        # Ask if user wants to shutdown
        try:
            response = input("\n🤔 Shutdown simulator? (y/N): ").strip().lower()
            if response in ['y', 'yes']:
                controller.shutdown_simulator(udid)
        except KeyboardInterrupt:
            print("\nDemo completed.")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")

def run_comprehensive_demo():
    """Run a comprehensive demo showing all simctl capabilities."""
    print("🍎 Comprehensive iOS Simulator Demo")
    print("=" * 50)
    
    controller = SimpleiOSController()
    
    if not controller.check_prerequisites():
        return
    
    try:
        # Show all simulators
        controller.print_simulators()
        
        # Get user choice
        simulators = controller.list_simulators()
        available_sims = [s for s in simulators if s['available']]
        
        if not available_sims:
            print("❌ No available simulators found")
            return
        
        print(f"\nSelect a simulator (1-{min(10, len(available_sims))}):")
        for i, sim in enumerate(available_sims[:10]):
            state_emoji = "🟢" if sim['state'] == 'Booted' else "⚪"
            print(f"{i+1:2}. {state_emoji} {sim['name']} ({sim['os']})")
        
        try:
            choice = int(input(f"\nEnter choice (1-{min(10, len(available_sims))}): ")) - 1
            if 0 <= choice < min(10, len(available_sims)):
                selected_sim = available_sims[choice]
                udid = selected_sim['udid']
                name = selected_sim['name']
                
                print(f"\n✅ Selected: {name}")
                
                # Comprehensive testing
                if controller.boot_simulator(udid):
                    print(f"\n🧪 Running comprehensive tests...")
                    
                    # Test screenshots
                    controller.take_screenshot(udid, f"test_home_{int(time.time())}.png")
                    
                    # Test app launching
                    apps_to_test = [
                        ("Settings", "com.apple.Preferences"),
                        ("Safari", "com.apple.mobilesafari"),
                        ("Maps", "com.apple.Maps"),
                        ("Photos", "com.apple.mobileslideshow")
                    ]
                    
                    for app_name, bundle_id in apps_to_test:
                        print(f"   🚀 Testing {app_name}...")
                        if controller.launch_app(udid, bundle_id):
                            time.sleep(2)
                            controller.take_screenshot(udid, f"test_{app_name.lower()}_{int(time.time())}.png")
                            time.sleep(1)
                    
                    # Test location changes
                    print(f"   🌍 Testing location simulation...")
                    test_locations = [
                        ("Apple Park", 37.3348, -122.0090),
                        ("Times Square", 40.7580, -73.9855),
                        ("Eiffel Tower", 48.8584, 2.2945)
                    ]
                    
                    for loc_name, lat, lng in test_locations:
                        print(f"     📍 {loc_name}: {lat}, {lng}")
                        controller.set_location(udid, lat, lng)
                        time.sleep(1)
                    
                    # Test URL opening
                    print(f"   🔗 Testing URL opening...")
                    test_urls = [
                        "https://www.apple.com",
                        "https://developer.apple.com",
                        "maps://?q=cupertino"
                    ]
                    
                    for url in test_urls:
                        controller.open_url(udid, url)
                        time.sleep(2)
                    
                    print(f"\n✅ Comprehensive demo completed!")
                
            else:
                print("❌ Invalid choice")
                
        except (ValueError, KeyboardInterrupt):
            print("\n❌ Demo cancelled")
            
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")

def main():
    """Main demo runner with options."""
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "--quick":
            run_quick_demo()
        elif sys.argv[1] == "--comprehensive":
            run_comprehensive_demo()
        else:
            print("❌ Unknown option. Use --quick or --comprehensive")
    else:
        print("🍎 iOS Simulator Demo (simctl only)")
        print("\nThis demo works with just Xcode - no additional tools needed!")
        print("\nOptions:")
        print("  --quick          Quick demonstration (automatic)")
        print("  --comprehensive  Full demo with user interaction")
        print("\nExamples:")
        print("  python simple_demo.py --quick")
        print("  python simple_demo.py --comprehensive")
        print()
        
        choice = input("Choose demo type (q)uick or (c)omprehensive: ").strip().lower()
        if choice in ['q', 'quick']:
            run_quick_demo()
        elif choice in ['c', 'comprehensive']:
            run_comprehensive_demo()
        else:
            print("Invalid choice")

if __name__ == "__main__":
    main()