#!/usr/bin/env python3
# examples/interactive_demo.py
"""
Interactive iOS Simulator Demo

Provides hands-on control of the simulator with a menu-driven interface.
"""

import subprocess
import json
import time
import os
from datetime import datetime
from pathlib import Path

class InteractiveSimulatorDemo:
    """Interactive iOS Simulator demonstration."""
    
    def __init__(self):
        self.simctl = "xcrun simctl"
        self.selected_udid = None
        self.selected_name = None
        self.demo_dir = Path("simulator_demo_output")
        self.demo_dir.mkdir(exist_ok=True)
    
    def run_command(self, cmd, ignore_errors=False):
        """Execute a shell command."""
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=True)
            return result.stdout
        except subprocess.CalledProcessError as e:
            if not ignore_errors:
                print(f"❌ Command failed: {e.stderr}")
            return None
    
    def run(self):
        """Run the interactive demo."""
        print("\n🍎 iOS Simulator Interactive Demo")
        print("=" * 50)
        print("Control your iOS Simulator with simple menu options!")
        print()
        
        try:
            # Setup
            if not self.check_prerequisites():
                return
            
            if not self.select_simulator():
                return
            
            if not self.boot_simulator():
                return
            
            # Main menu loop
            self.main_menu()
            
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
        except Exception as e:
            print(f"\n❌ Error: {e}")
    
    def check_prerequisites(self):
        """Check if Xcode and simctl are available."""
        print("🔍 Checking prerequisites...")
        
        try:
            self.run_command(f"{self.simctl} help")
            print("✅ Simulator tools available")
            return True
        except:
            print("❌ Xcode Command Line Tools not found")
            print("   Install with: xcode-select --install")
            return False
    
    def select_simulator(self):
        """Select a simulator to use."""
        print("\n📱 Available simulators:")
        
        # Get simulators
        output = self.run_command(f"{self.simctl} list devices -j")
        data = json.loads(output)
        
        # Find iPhone simulators
        iphones = []
        for runtime, devices in data['devices'].items():
            if 'iOS' in runtime:
                for device in devices:
                    if 'iPhone' in device['name'] and device.get('isAvailable', True):
                        device['runtime'] = runtime.split('.')[-1]
                        iphones.append(device)
        
        if not iphones:
            print("❌ No iPhone simulators found")
            return False
        
        # Show list
        for i, device in enumerate(iphones[:10]):  # Show max 10
            state = "🟢" if device['state'] == 'Booted' else "⚪"
            print(f"{i+1}. {state} {device['name']} ({device['runtime']})")
        
        # Let user choose
        while True:
            try:
                choice = input(f"\nSelect simulator (1-{min(len(iphones), 10)}): ").strip()
                idx = int(choice) - 1
                if 0 <= idx < min(len(iphones), 10):
                    selected = iphones[idx]
                    self.selected_udid = selected['udid']
                    self.selected_name = selected['name']
                    print(f"\n✅ Selected: {selected['name']}")
                    return True
                else:
                    print("Invalid choice")
            except (ValueError, KeyboardInterrupt):
                return False
    
    def boot_simulator(self):
        """Boot the selected simulator if needed."""
        print(f"\n🚀 Checking {self.selected_name}...")
        
        # Check current state
        output = self.run_command(f"{self.simctl} list devices -j")
        data = json.loads(output)
        
        is_booted = False
        for runtime, devices in data['devices'].items():
            for device in devices:
                if device['udid'] == self.selected_udid:
                    is_booted = device['state'] == 'Booted'
                    break
        
        if is_booted:
            print("✅ Simulator already running")
        else:
            print("📲 Booting simulator...")
            self.run_command(f"{self.simctl} boot {self.selected_udid}")
            time.sleep(3)
            
            # Open Simulator app
            self.run_command("open -a Simulator")
            time.sleep(2)
            print("✅ Simulator booted")
        
        return True
    
    def main_menu(self):
        """Main interactive menu."""
        while True:
            print(f"\n📱 {self.selected_name} - Main Menu")
            print("=" * 40)
            print("1. 📸 Take Screenshot")
            print("2. 🚀 Launch App")
            print("3. 📍 Set Location")
            print("4. 🌐 Open URL")
            print("5. 🖼️  Add Photo")
            print("6. 📊 Status Bar")
            print("7. 🎨 Appearance")
            print("8. ℹ️  Device Info")
            print("9. 🔄 Switch Simulator")
            print("0. 🚪 Exit")
            
            try:
                choice = input("\nChoice: ").strip()
                
                if choice == '0':
                    self.exit_demo()
                    break
                elif choice == '1':
                    self.take_screenshot()
                elif choice == '2':
                    self.launch_app()
                elif choice == '3':
                    self.set_location()
                elif choice == '4':
                    self.open_url()
                elif choice == '5':
                    self.add_photo()
                elif choice == '6':
                    self.status_bar_menu()
                elif choice == '7':
                    self.appearance_menu()
                elif choice == '8':
                    self.show_device_info()
                elif choice == '9':
                    if self.select_simulator():
                        self.boot_simulator()
                else:
                    print("Invalid choice")
                    
            except KeyboardInterrupt:
                print("\n(Use 0 to exit)")
            except Exception as e:
                print(f"❌ Error: {e}")
    
    def take_screenshot(self):
        """Take a screenshot."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"screenshot_{timestamp}.png"
        path = self.demo_dir / filename
        
        print(f"\n📸 Taking screenshot...")
        self.run_command(f"{self.simctl} io {self.selected_udid} screenshot '{path}'")
        print(f"✅ Saved: {filename}")
        print(f"   Location: {path}")
    
    def launch_app(self):
        """Launch an app."""
        apps = [
            ("Settings", "com.apple.Preferences"),
            ("Safari", "com.apple.mobilesafari"),
            ("Photos", "com.apple.mobileslideshow"),
            ("Maps", "com.apple.Maps"),
            ("Calendar", "com.apple.mobilecal"),
            ("Mail", "com.apple.mobilemail"),
            ("Messages", "com.apple.MobileSMS"),
            ("Camera", "com.apple.camera"),
            ("Custom", None)
        ]
        
        print("\n🚀 Launch App")
        for i, (name, _) in enumerate(apps):
            print(f"{i+1}. {name}")
        
        try:
            choice = input(f"Select app (1-{len(apps)}): ").strip()
            idx = int(choice) - 1
            
            if 0 <= idx < len(apps):
                name, bundle_id = apps[idx]
                
                if bundle_id is None:  # Custom
                    bundle_id = input("Enter bundle ID: ").strip()
                    name = bundle_id
                
                print(f"Launching {name}...")
                result = self.run_command(f"{self.simctl} launch {self.selected_udid} {bundle_id}", ignore_errors=True)
                if result is not None:
                    print(f"✅ {name} launched")
                else:
                    print(f"❌ Failed to launch {name}")
                    
        except (ValueError, IndexError):
            print("Invalid choice")
    
    def set_location(self):
        """Set device location."""
        locations = [
            ("San Francisco", 37.7749, -122.4194),
            ("New York", 40.7128, -74.0060),
            ("London", 51.5074, -0.1278),
            ("Paris", 48.8566, 2.3522),
            ("Tokyo", 35.6762, 139.6503),
            ("Sydney", -33.8688, 151.2093),
            ("Custom", None, None)
        ]
        
        print("\n📍 Set Location")
        for i, (name, _, _) in enumerate(locations):
            print(f"{i+1}. {name}")
        
        try:
            choice = input(f"Select location (1-{len(locations)}): ").strip()
            idx = int(choice) - 1
            
            if 0 <= idx < len(locations):
                name, lat, lng = locations[idx]
                
                if lat is None:  # Custom
                    lat = float(input("Latitude: "))
                    lng = float(input("Longitude: "))
                    name = f"Custom ({lat}, {lng})"
                
                print(f"Setting location to {name}...")
                self.run_command(f"{self.simctl} location {self.selected_udid} set {lat},{lng}")
                print(f"✅ Location set to {name}")
                
                # Offer to open Maps
                if input("Open Maps? (y/N): ").lower() == 'y':
                    self.run_command(f"{self.simctl} launch {self.selected_udid} com.apple.Maps")
                    
        except (ValueError, IndexError):
            print("Invalid input")
    
    def open_url(self):
        """Open a URL."""
        print("\n🌐 Open URL")
        print("1. Apple.com")
        print("2. Google.com")
        print("3. GitHub.com")
        print("4. Custom URL")
        
        urls = [
            "https://www.apple.com",
            "https://www.google.com",
            "https://www.github.com",
            None
        ]
        
        try:
            choice = input("Select (1-4): ").strip()
            idx = int(choice) - 1
            
            if 0 <= idx < len(urls):
                url = urls[idx]
                
                if url is None:  # Custom
                    url = input("Enter URL: ").strip()
                    if not url.startswith(('http://', 'https://')):
                        url = 'https://' + url
                
                print(f"Opening {url}...")
                self.run_command(f"{self.simctl} openurl {self.selected_udid} '{url}'")
                print("✅ URL opened in Safari")
                
        except (ValueError, IndexError):
            print("Invalid choice")
    
    def add_photo(self):
        """Add a photo to the device."""
        print("\n🖼️  Add Photo")
        
        # Try to find or create an image
        image_path = None
        
        # First check for existing screenshots
        screenshots = list(self.demo_dir.glob("*.png"))
        if screenshots:
            print(f"Found {len(screenshots)} screenshots in demo folder")
            if input("Use a screenshot? (Y/n): ").lower() != 'n':
                image_path = screenshots[-1]  # Use most recent
        
        if not image_path:
            # Try to create with PIL
            try:
                from PIL import Image, ImageDraw
                print("Creating sample image...")
                
                img = Image.new('RGB', (800, 600), color='lightblue')
                draw = ImageDraw.Draw(img)
                draw.rectangle([100, 100, 700, 500], fill='white', outline='darkblue', width=5)
                draw.text((250, 250), "Sample Image", fill='darkblue')
                draw.text((250, 300), datetime.now().strftime("%Y-%m-%d %H:%M"), fill='darkblue')
                
                image_path = self.demo_dir / "sample_image.png"
                img.save(image_path)
                
            except ImportError:
                print("❌ PIL not installed - can't create sample image")
                print("   Install with: pip install pillow")
                return
        
        if image_path:
            print(f"Adding {image_path.name} to Photos...")
            result = self.run_command(f"{self.simctl} addmedia {self.selected_udid} '{image_path}'", ignore_errors=True)
            
            if result is not None:
                print("✅ Photo added to library")
                if input("Open Photos app? (y/N): ").lower() == 'y':
                    self.run_command(f"{self.simctl} launch {self.selected_udid} com.apple.mobileslideshow")
            else:
                print("❌ Failed to add photo")
    
    def status_bar_menu(self):
        """Status bar customization menu."""
        print("\n📊 Status Bar Options")
        print("1. Demo mode (9:41, 100% battery)")
        print("2. Low battery")
        print("3. No signal")
        print("4. Custom time")
        print("5. Clear overrides")
        
        try:
            choice = input("Select (1-5): ").strip()
            
            if choice == '1':
                self.run_command(f"{self.simctl} status_bar {self.selected_udid} override "
                               "--time '9:41' --batteryLevel 100 --cellularBars 4 --wifiBars 3")
                print("✅ Demo status bar set")
            elif choice == '2':
                self.run_command(f"{self.simctl} status_bar {self.selected_udid} override "
                               "--batteryLevel 10 --batteryState charging")
                print("✅ Low battery set")
            elif choice == '3':
                self.run_command(f"{self.simctl} status_bar {self.selected_udid} override "
                               "--cellularBars 0 --wifiBars 0")
                print("✅ No signal set")
            elif choice == '4':
                time_str = input("Enter time (HH:MM): ").strip()
                self.run_command(f"{self.simctl} status_bar {self.selected_udid} override "
                               f"--time '{time_str}'")
                print(f"✅ Time set to {time_str}")
            elif choice == '5':
                self.run_command(f"{self.simctl} status_bar {self.selected_udid} clear")
                print("✅ Status bar cleared")
                
        except Exception as e:
            print(f"❌ Error: {e}")
    
    def appearance_menu(self):
        """Appearance customization menu."""
        print("\n🎨 Appearance Options")
        print("1. Light mode")
        print("2. Dark mode")
        print("3. Toggle appearance")
        
        try:
            choice = input("Select (1-3): ").strip()
            
            if choice == '1':
                self.run_command(f"{self.simctl} ui {self.selected_udid} appearance light")
                print("✅ Light mode set")
            elif choice == '2':
                self.run_command(f"{self.simctl} ui {self.selected_udid} appearance dark")
                print("✅ Dark mode set")
            elif choice == '3':
                # Get current appearance
                result = self.run_command(f"{self.simctl} ui {self.selected_udid} appearance")
                if result and 'dark' in result.lower():
                    self.run_command(f"{self.simctl} ui {self.selected_udid} appearance light")
                    print("✅ Switched to light mode")
                else:
                    self.run_command(f"{self.simctl} ui {self.selected_udid} appearance dark")
                    print("✅ Switched to dark mode")
                    
        except Exception as e:
            print(f"❌ Error: {e}")
    
    def show_device_info(self):
        """Show device information."""
        print(f"\nℹ️  Device Information")
        print("=" * 40)
        
        # Get device details
        output = self.run_command(f"{self.simctl} list devices -j")
        data = json.loads(output)
        
        for runtime, devices in data['devices'].items():
            for device in devices:
                if device['udid'] == self.selected_udid:
                    print(f"Name: {device['name']}")
                    print(f"UDID: {device['udid']}")
                    print(f"State: {device['state']}")
                    print(f"Runtime: {runtime.split('.')[-1]}")
                    print(f"Available: {'Yes' if device.get('isAvailable', True) else 'No'}")
                    
                    # Get data path
                    data_path = Path.home() / f"Library/Developer/CoreSimulator/Devices/{device['udid']}"
                    if data_path.exists():
                        print(f"Data: {data_path}")
                    
                    return
    
    def exit_demo(self):
        """Exit the demo."""
        print("\n🚪 Exiting...")
        
        # Ask about shutdown
        if input("Shutdown simulator? (y/N): ").lower() == 'y':
            print("Shutting down simulator...")
            self.run_command(f"{self.simctl} shutdown {self.selected_udid}", ignore_errors=True)
            print("✅ Simulator shutdown")
        
        print("\n👋 Thanks for using the iOS Simulator Demo!")
        print(f"📁 Screenshots saved in: {self.demo_dir}")

def main():
    """Run the interactive demo."""
    demo = InteractiveSimulatorDemo()
    demo.run()

if __name__ == "__main__":
    main()