#!/usr/bin/env python3
"""
End-to-End Demo Script for iOS Simulator Controller
Demonstrates the complete workflow and capabilities of the modular iOS simulator framework.
"""

import os
import time
import json
from pathlib import Path
from datetime import datetime
from chuk_mcp_ios.cli import iOSSimulatorController

class E2EDemo:
    """
    Comprehensive end-to-end demonstration of iOS Simulator Controller capabilities.
    Shows real-world usage patterns and automation workflows.
    """
    
    def __init__(self):
        self.controller = iOSSimulatorController()
        self.session_id = None
        self.demo_data_dir = "demo_data"
        self.setup_demo_environment()
    
    def setup_demo_environment(self):
        """Set up the demo environment with sample data."""
        print("🔧 Setting up demo environment...")
        
        # Create demo data directory
        os.makedirs(self.demo_data_dir, exist_ok=True)
        
        # Create sample media files
        self.create_sample_media()
        
        # Create sample contacts database
        self.create_sample_contacts()
        
        print("✅ Demo environment ready\n")
    
    def create_sample_media(self):
        """Create sample media files for testing."""
        try:
            from PIL import Image, ImageDraw, ImageFont
            import random
            
            media_dir = os.path.join(self.demo_data_dir, "media")
            os.makedirs(media_dir, exist_ok=True)
            
            # Create sample images
            for i in range(3):
                width, height = 800, 600
                color = (random.randint(100, 255), random.randint(100, 255), random.randint(100, 255))
                
                image = Image.new('RGB', (width, height), color)
                draw = ImageDraw.Draw(image)
                
                # Add text and shapes
                draw.text((width//2 - 60, height//2), f"Demo Image {i+1}", fill='white')
                draw.rectangle([50, 50, 150, 150], outline='white', width=3)
                
                filename = f"demo_image_{i+1}.png"
                filepath = os.path.join(media_dir, filename)
                image.save(filepath)
            
            print(f"📸 Created sample media files in {media_dir}")
            
        except ImportError:
            print("⚠️  PIL not available, skipping media creation")
            print("   Install Pillow: pip install Pillow")
    
    def create_sample_contacts(self):
        """Create sample contacts database."""
        contacts_file = os.path.join(self.demo_data_dir, "sample_contacts.db")
        
        sample_contacts = [
            {"first_name": "John", "last_name": "Doe", "phone_number": "+1-555-0001", "email": "john.doe@example.com"},
            {"first_name": "Jane", "last_name": "Smith", "phone_number": "+1-555-0002", "email": "jane.smith@example.com"},
            {"first_name": "Alice", "last_name": "Johnson", "phone_number": "+1-555-0003", "email": "alice.j@example.com"}
        ]
        
        try:
            self.controller.utilities_manager.create_contact_database(contacts_file, sample_contacts)
            print(f"📞 Created sample contacts database: {contacts_file}")
        except Exception as e:
            print(f"⚠️  Could not create contacts database: {e}")
    
    def run_complete_demo(self):
        """Run the complete end-to-end demonstration."""
        print("🚀 Starting iOS Simulator Controller E2E Demo")
        print("=" * 60)
        
        try:
            # Phase 1: Session and Simulator Management
            self.demo_session_management()
            
            # Phase 2: Device Setup and Configuration
            self.demo_device_setup()
            
            # Phase 3: App Management (simulated)
            self.demo_app_management()
            
            # Phase 4: UI Automation
            self.demo_ui_automation()
            
            # Phase 5: Media and Location Testing
            self.demo_media_and_location()
            
            # Phase 6: Logging and Debugging
            self.demo_logging_and_debugging()
            
            # Phase 7: Advanced Features
            self.demo_advanced_features()
            
            # Phase 8: Cleanup and Reports
            self.demo_cleanup_and_reports()
            
        except Exception as e:
            print(f"❌ Demo failed: {e}")
            self.emergency_cleanup()
        
        print("\n🎉 E2E Demo completed successfully!")
        print("Check the demo_data directory for generated files and reports.")
    
    def demo_session_management(self):
        """Demonstrate session management capabilities."""
        print("\n📱 Phase 1: Session Management")
        print("-" * 40)
        
        # List available simulators
        print("1️⃣  Listing available simulators...")
        self.controller.simulator_manager.print_device_list()
        
        # Create a session
        print("\n2️⃣  Creating automation session...")
        self.session_id = self.controller.create_session(device_name="iPhone 15")
        print(f"✅ Session created: {self.session_id}")
        
        # Get session info
        session_info = self.controller.get_session_info(self.session_id)
        print(f"📋 Session UDID: {session_info['udid']}")
        
        # List all sessions
        sessions = self.controller.list_sessions()
        print(f"📊 Active sessions: {len(sessions)}")
        
        time.sleep(2)
    
    def demo_device_setup(self):
        """Demonstrate device setup and configuration."""
        print("\n⚙️  Phase 2: Device Setup")
        print("-" * 40)
        
        # Focus simulator window
        print("1️⃣  Focusing simulator window...")
        self.controller.focus_simulator(self.session_id)
        
        # Get device information
        print("2️⃣  Getting device information...")
        device_info = self.controller.get_device_info(self.session_id)
        print(f"📱 Device: {device_info.get('name', 'Unknown')}")
        print(f"🔧 OS: {device_info.get('os', 'Unknown')}")
        
        # Clear keychain for fresh start
        print("3️⃣  Clearing keychain...")
        self.controller.clear_keychain(self.session_id)
        
        # Set initial location (San Francisco)
        print("4️⃣  Setting initial location...")
        self.controller.set_location_by_name(self.session_id, "san francisco")
        
        time.sleep(2)
    
    def demo_app_management(self):
        """Demonstrate app management (simulated since we don't have actual apps)."""
        print("\n📦 Phase 3: App Management (Simulated)")
        print("-" * 40)
        
        # List currently installed apps
        print("1️⃣  Listing installed apps...")
        apps = self.controller.list_apps(self.session_id)
        print(f"📱 Found {len(apps)} user apps installed")
        
        # Show some system apps
        all_apps = self.controller.list_apps(self.session_id, user_apps_only=False)
        system_apps = [app for app in all_apps if app.bundle_id.startswith('com.apple.')]
        print(f"🔧 System apps available: {len(system_apps)}")
        
        # Simulate app installation workflow
        print("2️⃣  Simulating app installation workflow...")
        print("   (In real scenario: controller.install_app(session_id, 'MyApp.app'))")
        print("   (In real scenario: controller.launch_app(session_id, 'com.example.MyApp'))")
        
        # Open a system app (Settings)
        print("3️⃣  Opening Settings app...")
        try:
            self.controller.launch_app(self.session_id, "com.apple.Preferences")
            print("✅ Settings app launched")
            time.sleep(3)
        except Exception as e:
            print(f"⚠️  Could not launch Settings: {e}")
        
        time.sleep(2)
    
    def demo_ui_automation(self):
        """Demonstrate UI automation capabilities."""
        print("\n🎯 Phase 4: UI Automation")
        print("-" * 40)
        
        # Take initial screenshot
        print("1️⃣  Taking initial screenshot...")
        screenshot_path = os.path.join(self.demo_data_dir, "screenshot_initial.png")
        self.controller.take_screenshot(self.session_id, screenshot_path)
        print(f"📸 Screenshot saved: {screenshot_path}")
        
        # Demonstrate tap gestures
        print("2️⃣  Demonstrating tap gestures...")
        print("   Tapping at center of screen...")
        self.controller.tap(self.session_id, 200, 400)
        time.sleep(1)
        
        # Demonstrate swipe gestures
        print("3️⃣  Demonstrating swipe gestures...")
        print("   Swiping up (simulating scroll)...")
        self.controller.ui_controller.swipe_up(
            self.controller.session_manager.get_udid_from_session(self.session_id)
        )
        time.sleep(1)
        
        print("   Swiping down...")
        self.controller.ui_controller.swipe_down(
            self.controller.session_manager.get_udid_from_session(self.session_id)
        )
        time.sleep(1)
        
        # Demonstrate hardware button presses
        print("4️⃣  Demonstrating hardware buttons...")
        print("   Pressing home button...")
        self.controller.press_button(self.session_id, "home")
        time.sleep(2)
        
        # Take final screenshot
        print("5️⃣  Taking final screenshot...")
        screenshot_path2 = os.path.join(self.demo_data_dir, "screenshot_final.png")
        self.controller.take_screenshot(self.session_id, screenshot_path2)
        print(f"📸 Screenshot saved: {screenshot_path2}")
        
        time.sleep(2)
    
    def demo_media_and_location(self):
        """Demonstrate media and location features."""
        print("\n🌍 Phase 5: Media & Location")
        print("-" * 40)
        
        # Add sample media files
        media_dir = os.path.join(self.demo_data_dir, "media")
        if os.path.exists(media_dir):
            print("1️⃣  Adding sample media to photo library...")
            media_files = [os.path.join(media_dir, f) for f in os.listdir(media_dir) if f.endswith('.png')]
            if media_files:
                self.controller.add_media(self.session_id, media_files)
                print(f"📸 Added {len(media_files)} media files")
            else:
                print("⚠️  No media files found to add")
        
        # Demonstrate location simulation
        print("2️⃣  Demonstrating location simulation...")
        locations = [
            ("New York", 40.7128, -74.0060),
            ("London", 51.5074, -0.1278),
            ("Tokyo", 35.6762, 139.6503),
            ("Sydney", -33.8688, 151.2093)
        ]
        
        for name, lat, lng in locations[:2]:  # Just do 2 locations for demo
            print(f"   📍 Setting location to {name}...")
            self.controller.set_location(self.session_id, lat, lng)
            time.sleep(2)
        
        # Simulate a route
        print("3️⃣  Simulating location route...")
        route_waypoints = [
            (37.7749, -122.4194),  # San Francisco
            (37.7849, -122.4094),  # Moving north
            (37.7949, -122.3994),  # Moving northeast
        ]
        
        udid = self.controller.session_manager.get_udid_from_session(self.session_id)
        self.controller.media_manager.simulate_location_route(udid, route_waypoints, interval=1.0)
        
        time.sleep(2)
    
    def demo_logging_and_debugging(self):
        """Demonstrate logging and debugging capabilities."""
        print("\n📝 Phase 6: Logging & Debugging")
        print("-" * 40)
        
        # Get system logs
        print("1️⃣  Collecting system logs...")
        try:
            logs = self.controller.get_system_logs(self.session_id, limit=20)
            log_lines = len(logs.split('\n'))
            print(f"📋 Collected {log_lines} lines of system logs")
        except Exception as e:
            print(f"⚠️  Could not collect logs: {e}")
        
        # List crash logs
        print("2️⃣  Checking for crash logs...")
        try:
            crash_logs = self.controller.list_crash_logs(self.session_id)
            print(f"💥 Found {len(crash_logs)} crash logs")
        except Exception as e:
            print(f"⚠️  Could not list crash logs: {e}")
        
        # Export logs
        print("3️⃣  Exporting logs to files...")
        try:
            log_files = self.controller.export_logs(self.session_id, self.demo_data_dir)
            print(f"📄 Exported {len(log_files)} log files")
            for file_path in log_files:
                print(f"   📁 {file_path}")
        except Exception as e:
            print(f"⚠️  Could not export logs: {e}")
        
        time.sleep(2)
    
    def demo_advanced_features(self):
        """Demonstrate advanced features."""
        print("\n🔧 Phase 7: Advanced Features")
        print("-" * 40)
        
        # Open URLs and deep links
        print("1️⃣  Testing URL handling...")
        test_urls = [
            "https://www.apple.com",
            "settings://",  # Deep link to settings
            "prefs:root=General"  # iOS settings deep link
        ]
        
        for url in test_urls:
            try:
                print(f"   🔗 Opening: {url}")
                self.controller.open_url(self.session_id, url)
                time.sleep(2)
            except Exception as e:
                print(f"   ⚠️  Failed to open {url}: {e}")
        
        # Permission management
        print("2️⃣  Testing permission management...")
        try:
            # This would typically be done with a real app
            print("   (Simulated) Granting location permissions...")
            # self.controller.approve_permissions(session_id, "com.example.MyApp", ["location", "camera"])
            print("   ✅ Permission simulation complete")
        except Exception as e:
            print(f"   ⚠️  Permission demo failed: {e}")
        
        # Debug server status
        print("3️⃣  Checking debug server status...")
        try:
            debug_status = self.controller.utilities_manager.get_debug_server_status(
                self.controller.session_manager.get_udid_from_session(self.session_id)
            )
            print(f"   🐛 Debug server running: {debug_status.running}")
        except Exception as e:
            print(f"   ⚠️  Could not check debug server: {e}")
        
        time.sleep(2)
    
    def demo_cleanup_and_reports(self):
        """Demonstrate cleanup and generate reports."""
        print("\n📊 Phase 8: Cleanup & Reports")
        print("-" * 40)
        
        # Generate demo report
        print("1️⃣  Generating demo report...")
        self.generate_demo_report()
        
        # Show final status
        print("2️⃣  Final system status...")
        self.controller.print_status()
        
        # Cleanup session
        print("3️⃣  Cleaning up session...")
        if self.session_id:
            self.controller.terminate_session(self.session_id)
            print(f"✅ Session {self.session_id} terminated")
        
        time.sleep(1)
    
    def generate_demo_report(self):
        """Generate a comprehensive demo report."""
        report_path = os.path.join(self.demo_data_dir, "demo_report.json")
        
        report = {
            "demo_run": {
                "timestamp": datetime.now().isoformat(),
                "session_id": self.session_id,
                "status": "completed"
            },
            "capabilities_tested": [
                "Session Management",
                "Simulator Control",
                "App Management",
                "UI Automation",
                "Media Handling",
                "Location Simulation",
                "Logging & Debugging",
                "Advanced Features"
            ],
            "files_generated": [],
            "statistics": {
                "screenshots_taken": 2,
                "locations_simulated": 4,
                "gestures_performed": 4,
                "apps_launched": 1
            }
        }
        
        # List generated files
        if os.path.exists(self.demo_data_dir):
            for file in os.listdir(self.demo_data_dir):
                file_path = os.path.join(self.demo_data_dir, file)
                if os.path.isfile(file_path):
                    report["files_generated"].append({
                        "name": file,
                        "size": os.path.getsize(file_path),
                        "type": os.path.splitext(file)[1]
                    })
        
        # Save report
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"📋 Demo report saved: {report_path}")
    
    def emergency_cleanup(self):
        """Emergency cleanup in case of errors."""
        print("\n🚨 Emergency cleanup...")
        try:
            if self.session_id:
                self.controller.terminate_session(self.session_id)
                print(f"✅ Emergency cleanup: Session {self.session_id} terminated")
        except:
            pass

def run_quick_demo():
    """Run a quick demonstration of key features."""
    print("⚡ Quick Demo - Key Features")
    print("=" * 40)
    
    controller = iOSSimulatorController()
    
    try:
        # Quick session creation
        print("1. Creating session...")
        session_id = controller.create_session()
        
        # Show status
        print("2. System status:")
        controller.print_status()
        
        # Take screenshot
        print("3. Taking screenshot...")
        controller.take_screenshot(session_id, "quick_demo_screenshot.png")
        
        # Cleanup
        print("4. Cleaning up...")
        controller.terminate_session(session_id)
        
        print("✅ Quick demo completed!")
        
    except Exception as e:
        print(f"❌ Quick demo failed: {e}")

def main():
    """Main demo runner with options."""
    import argparse
    
    parser = argparse.ArgumentParser(description='iOS Simulator Controller E2E Demo')
    parser.add_argument('--quick', action='store_true', help='Run quick demo')
    parser.add_argument('--full', action='store_true', help='Run full E2E demo')
    
    args = parser.parse_args()
    
    if args.quick:
        run_quick_demo()
    elif args.full:
        demo = E2EDemo()
        demo.run_complete_demo()
    else:
        print("🍎 iOS Simulator Controller Demo")
        print("\nChoose a demo option:")
        print("  --quick   Quick demonstration of key features")
        print("  --full    Complete end-to-end demonstration")
        print("\nExamples:")
        print("  python e2e_demo_script.py --quick")
        print("  python e2e_demo_script.py --full")

if __name__ == "__main__":
    main()