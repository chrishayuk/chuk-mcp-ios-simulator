#!/usr/bin/env python3
# scripts/debug_idb.py - Debug IDB detection
import subprocess
import shutil

def debug_idb_detection():
    print("🔍 Debugging IDB Detection")
    print("=" * 40)
    
    # Check if idb command exists in PATH
    idb_path = shutil.which('idb')
    print(f"IDB in PATH: {idb_path}")
    
    if idb_path:
        print(f"IDB found at: {idb_path}")
        
        try:
            result = subprocess.run(
                ["idb", "list-targets"],
                capture_output=True,
                text=True,
                timeout=5,
                check=True
            )
            print(f"IDB version output: {result.stdout.strip()}")
            print("✅ IDB detection should work")
        except subprocess.CalledProcessError as e:
            print(f"❌ IDB version failed: {e.stderr}")
        except subprocess.TimeoutExpired:
            print("❌ IDB version timed out")
        except FileNotFoundError:
            print("❌ IDB command not found")
    else:
        print("❌ IDB not found in PATH")
        
        # Check common installation locations
        possible_paths = [
            "/usr/local/bin/idb",
            "/opt/homebrew/bin/idb",
            "~/.local/bin/idb",
            "/usr/bin/idb"
        ]
        
        print("\nChecking common locations:")
        for path in possible_paths:
            expanded_path = os.path.expanduser(path)
            if os.path.exists(expanded_path):
                print(f"  ✅ Found: {expanded_path}")
            else:
                print(f"  ❌ Not found: {expanded_path}")
    
    # Check idb-companion
    companion_path = shutil.which('idb_companion')
    print(f"\nIDB Companion in PATH: {companion_path}")
    
    # Check what brew installed
    try:
        result = subprocess.run(
            ["brew", "list", "idb-companion"],
            capture_output=True,
            text=True,
            check=True
        )
        print(f"\nBrew idb-companion files:")
        for line in result.stdout.split('\n')[:10]:  # First 10 lines
            if line.strip():
                print(f"  {line}")
    except:
        print("Could not list brew idb-companion files")
    
    print(f"\n💡 Solutions:")
    print("1. Install idb client: pip install fb-idb")
    print("2. Or use conda: conda install -c conda-forge fb-idb") 
    print("3. Or check PATH: echo $PATH")
    print("4. Or restart terminal after install")

if __name__ == "__main__":
    import os
    debug_idb_detection()