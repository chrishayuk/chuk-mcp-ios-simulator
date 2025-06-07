#!/usr/bin/env python3
# examples/test_simulator.py
"""
Simple test script to verify simulator control is working
"""

import subprocess
import sys

def test_simctl():
    """Test if simctl is available"""
    print("Testing iOS Simulator control...")
    print("-" * 40)
    
    try:
        # Test 1: Check if simctl exists
        print("1. Checking simctl availability...")
        result = subprocess.run(
            ["xcrun", "simctl", "help"], 
            capture_output=True, 
            text=True,
            check=True
        )
        print("✅ simctl is available")
        
        # Test 2: List devices
        print("\n2. Listing simulators...")
        result = subprocess.run(
            ["xcrun", "simctl", "list", "devices", "-j"],
            capture_output=True,
            text=True,
            check=True
        )
        
        import json
        devices_data = json.loads(result.stdout)
        
        device_count = 0
        for runtime, devices in devices_data['devices'].items():
            if 'iOS' in runtime:
                for device in devices:
                    if device.get('isAvailable', True):
                        device_count += 1
                        print(f"   Found: {device['name']} ({device['state']})")
                        if device_count >= 3:  # Just show first 3
                            break
                if device_count >= 3:
                    break
        
        if device_count > 3:
            print(f"   ... and {device_count - 3} more")
        
        print(f"\n✅ Found {device_count} iOS simulators")
        
        # Test 3: Check Simulator app
        print("\n3. Checking Simulator app...")
        sim_path = "/Applications/Xcode.app/Contents/Developer/Applications/Simulator.app"
        import os
        if os.path.exists(sim_path):
            print("✅ Simulator.app found")
        else:
            print("⚠️  Simulator.app not in default location")
        
        print("\n✅ All tests passed! Simulator control should work.")
        print("\nYou can run the demos with:")
        print("  python3 examples/interactive_demo.py --interactive")
        print("  python3 examples/automated_demo.py")
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Command failed: {e}")
        print(f"Error output: {e.stderr}")
        print("\nMake sure Xcode Command Line Tools are installed:")
        print("  xcode-select --install")
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\nSomething went wrong. Check your Xcode installation.")

if __name__ == "__main__":
    test_simctl()