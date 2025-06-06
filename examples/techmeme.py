#!/usr/bin/env python3
# examples/techmeme.py
"""
Techmeme News Screenshot Script

Opens Techmeme.com in Safari and captures screenshots of the latest tech news.
"""

import subprocess
import json
import time
from datetime import datetime
from pathlib import Path

class TechmemeNewsCapture:
    """Capture latest news from Techmeme in Safari."""
    
    def __init__(self):
        self.simctl = "xcrun simctl"
        self.output_dir = Path("techmeme_news")
        self.output_dir.mkdir(exist_ok=True)
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    def run_command(self, cmd, ignore_errors=False):
        """Execute a shell command."""
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=True)
            return result.stdout
        except subprocess.CalledProcessError as e:
            if not ignore_errors:
                print(f"❌ Command failed: {e.stderr}")
                raise
            return None
    
    def get_booted_simulator(self):
        """Find the currently booted simulator."""
        output = self.run_command(f"{self.simctl} list devices -j")
        data = json.loads(output)
        
        for runtime, devices in data['devices'].items():
            for device in devices:
                if device['state'] == 'Booted':
                    return device['udid'], device['name']
        
        return None, None
    
    def take_screenshot(self, udid, name, description):
        """Take a screenshot with timestamp."""
        filename = f"{self.timestamp}_{name}.png"
        path = self.output_dir / filename
        self.run_command(f"{self.simctl} io {udid} screenshot '{path}'")
        print(f"📸 Captured: {description} → {filename}")
        return path
    
    def capture_techmeme_news(self):
        """Main function to capture Techmeme news."""
        print("📰 Techmeme News Capture")
        print("=" * 50)
        
        # Find booted simulator
        udid, name = self.get_booted_simulator()
        if not udid:
            print("❌ No booted simulator found!")
            print("   Please boot a simulator first:")
            print("   uv run examples/interactive_demo.py")
            return
        
        print(f"✅ Using: {name}")
        print(f"📁 Saving to: {self.output_dir}")
        print()
        
        try:
            # Close any existing Safari instances
            print("🧹 Closing existing Safari instances...")
            self.run_command(f"{self.simctl} terminate {udid} com.apple.mobilesafari", ignore_errors=True)
            time.sleep(1)
            
            # Set demo status bar for clean screenshots
            print("📶 Setting clean status bar...")
            self.run_command(f"{self.simctl} status_bar {udid} override "
                           "--time '9:41' --batteryLevel 100 --cellularBars 4 --wifiBars 3")
            
            # Open Techmeme
            print("🌐 Opening Techmeme.com...")
            self.run_command(f"{self.simctl} openurl {udid} 'https://techmeme.com'")
            
            # Wait for page to load
            print("⏳ Waiting for page to load...")
            time.sleep(5)
            
            # Take initial screenshot
            self.take_screenshot(udid, "01_techmeme_home", "Techmeme homepage - top stories")
            
            # Wait a moment
            time.sleep(2)
            
            # Scroll down to capture more news
            print("📜 Scrolling to capture more stories...")
            
            # Note: Direct scrolling requires UI automation tools like idb
            # For now, we'll take multiple screenshots with manual scrolling prompts
            
            print("\n💡 Manual scrolling needed:")
            print("   1. Click on the simulator window")
            print("   2. Scroll down to see more stories")
            print("   3. Press Enter here when ready")
            
            input("\nPress Enter after scrolling to middle section...")
            self.take_screenshot(udid, "02_techmeme_middle", "Techmeme - middle section stories")
            
            input("\nPress Enter after scrolling to bottom section...")
            self.take_screenshot(udid, "03_techmeme_bottom", "Techmeme - bottom section stories")
            
            # Open a specific story
            print("\n💡 To capture a specific story:")
            print("   1. Click on any interesting headline")
            print("   2. Press Enter here when the article loads")
            
            input("\nPress Enter after opening an article...")
            self.take_screenshot(udid, "04_article_view", "Article detail view")
            
            # Return to Techmeme
            print("\n🔙 Returning to Techmeme...")
            print("   Click the back button or reload techmeme.com")
            
            input("\nPress Enter when back at Techmeme...")
            self.take_screenshot(udid, "05_techmeme_final", "Techmeme - final view")
            
            # Clear status bar
            print("\n🧹 Cleaning up...")
            self.run_command(f"{self.simctl} status_bar {udid} clear")
            
            # Summary
            print("\n✅ Capture complete!")
            print(f"📁 Screenshots saved to: {self.output_dir}")
            
            screenshots = list(self.output_dir.glob(f"{self.timestamp}_*.png"))
            print(f"📸 Total screenshots: {len(screenshots)}")
            
            print("\n📋 Captured files:")
            for screenshot in sorted(screenshots):
                print(f"   - {screenshot.name}")
            
            # Generate summary
            self.generate_summary()
            
        except KeyboardInterrupt:
            print("\n\n⚠️  Capture interrupted")
        except Exception as e:
            print(f"\n❌ Error: {e}")
    
    def generate_summary(self):
        """Generate a summary of the capture session."""
        summary_file = self.output_dir / f"{self.timestamp}_summary.txt"
        
        with open(summary_file, 'w') as f:
            f.write("Techmeme News Capture Summary\n")
            f.write("=" * 40 + "\n\n")
            f.write(f"Capture Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Website: https://techmeme.com\n\n")
            
            f.write("Screenshots captured:\n")
            screenshots = list(self.output_dir.glob(f"{self.timestamp}_*.png"))
            for screenshot in sorted(screenshots):
                f.write(f"- {screenshot.name}\n")
            
            f.write(f"\nTotal screenshots: {len(screenshots)}\n")
            f.write(f"Output directory: {self.output_dir.absolute()}\n")
        
        print(f"\n📄 Summary saved: {summary_file.name}")

def automated_capture():
    """Fully automated version (requires idb for scrolling)."""
    print("🤖 Automated Techmeme Capture")
    print("=" * 50)
    
    capture = TechmemeNewsCapture()
    
    # Find booted simulator
    udid, name = capture.get_booted_simulator()
    if not udid:
        print("❌ No booted simulator found!")
        return
    
    print(f"✅ Using: {name}")
    
    try:
        # Setup
        capture.run_command(f"{capture.simctl} terminate {udid} com.apple.mobilesafari", ignore_errors=True)
        time.sleep(1)
        
        capture.run_command(f"{capture.simctl} status_bar {udid} override "
                          "--time '9:41' --batteryLevel 100 --cellularBars 4 --wifiBars 3")
        
        # Open Techmeme
        print("🌐 Opening Techmeme.com...")
        capture.run_command(f"{capture.simctl} openurl {udid} 'https://techmeme.com'")
        
        # Wait for load
        print("⏳ Waiting for page load...")
        time.sleep(6)
        
        # Take screenshots at intervals
        screenshots = [
            ("01_initial", "Techmeme - Initial view", 0),
            ("02_after_wait", "Techmeme - After full load", 3),
            ("03_top_stories", "Techmeme - Top stories", 2),
        ]
        
        for name, desc, wait in screenshots:
            if wait > 0:
                time.sleep(wait)
            capture.take_screenshot(udid, name, desc)
        
        # Try to open mobile menu if available
        print("\n🔍 Attempting to capture mobile menu...")
        time.sleep(2)
        capture.take_screenshot(udid, "04_final_state", "Techmeme - Final state")
        
        # Cleanup
        capture.run_command(f"{capture.simctl} status_bar {udid} clear")
        
        print("\n✅ Automated capture complete!")
        print(f"📁 Screenshots saved to: {capture.output_dir}")
        
        # List files
        screenshots = list(capture.output_dir.glob("*.png"))
        print(f"\n📸 Captured {len(screenshots)} screenshots")
        
    except Exception as e:
        print(f"❌ Error: {e}")

def main():
    """Main entry point."""
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == '--auto':
        automated_capture()
    else:
        capture = TechmemeNewsCapture()
        capture.capture_techmeme_news()

if __name__ == "__main__":
    main()