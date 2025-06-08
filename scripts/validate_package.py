#!/usr/bin/env python3
"""
Package validation script for chuk-mcp-ios
Checks the built package structure and entry points.
"""

import os
import sys
import tarfile
import zipfile
from pathlib import Path

def validate_package():
    """Validate the built package."""
    dist_dir = Path("dist")
    
    if not dist_dir.exists():
        print("❌ No dist directory found")
        return False
    
    # Find distribution files
    tar_files = list(dist_dir.glob("*.tar.gz"))
    whl_files = list(dist_dir.glob("*.whl"))
    
    print("📦 Built distributions:")
    for f in tar_files + whl_files:
        size = f.stat().st_size / 1024  # KB
        print(f"   📄 {f.name} ({size:.1f} KB)")
    
    success = True
    
    # Validate source distribution
    if tar_files:
        print("\n📋 Validating source distribution...")
        try:
            with tarfile.open(tar_files[0]) as tf:
                names = tf.getnames()
                
                has_src = any('src/' in n for n in names)
                has_pyproject = any('pyproject.toml' in n for n in names)
                has_readme = any('README' in n for n in names)
                has_py_files = any(n.endswith('.py') for n in names)
                
                print(f"   ✅ Source layout: {'src/' if has_src else 'flat'}")
                print(f"   ✅ pyproject.toml: {'found' if has_pyproject else 'missing'}")
                print(f"   ✅ README: {'found' if has_readme else 'missing'}")
                print(f"   ✅ Python files: {'found' if has_py_files else 'missing'}")
                print(f"   📊 Total files: {len(names)}")
                
                if not has_pyproject:
                    print("   ⚠️  Missing pyproject.toml")
                    success = False
                    
        except Exception as e:
            print(f"   ❌ Error reading source distribution: {e}")
            success = False
    else:
        print("❌ No source distribution (.tar.gz) found")
        success = False
    
    # Validate wheel
    if whl_files:
        print("\n🎯 Validating wheel distribution...")
        try:
            with zipfile.ZipFile(whl_files[0]) as zf:
                files = zf.namelist()
                
                # Look for entry points
                entry_points_files = [f for f in files if f.endswith('entry_points.txt')]
                if entry_points_files:
                    ep_content = zf.read(entry_points_files[0]).decode()
                    print("   📋 Entry points found:")
                    
                    current_section = None
                    for line in ep_content.split('\n'):
                        line = line.strip()
                        if not line:
                            continue
                        if line.startswith('[') and line.endswith(']'):
                            current_section = line
                            print(f"   {line}")
                        elif '=' in line and current_section == '[console_scripts]':
                            print(f"      {line}")
                else:
                    print("   ⚠️  No entry points found")
                
                # Check for Python package files
                py_files = [f for f in files if f.endswith('.py')]
                print(f"   📊 Python files in wheel: {len(py_files)}")
                
        except Exception as e:
            print(f"   ❌ Error reading wheel: {e}")
            success = False
    else:
        print("❌ No wheel distribution (.whl) found")
        success = False
    
    return success

def main():
    """Main validation function."""
    print("🔍 Package Validation")
    print("=" * 40)
    
    success = validate_package()
    
    print("\n" + "=" * 40)
    if success:
        print("✅ Package validation successful!")
        print("\n📤 Ready for publishing:")
        print("   make publish-test    # Test on test PyPI")
        print("   make publish         # Publish to PyPI")
        print("\n🎉 After publishing, users can run:")
        print("   uvx chuk-mcp-ios cli status")
        print("   uvx chuk-mcp-ios mcp")
        return 0
    else:
        print("❌ Package validation failed!")
        print("   Fix the issues above before publishing")
        return 1

if __name__ == "__main__":
    sys.exit(main())