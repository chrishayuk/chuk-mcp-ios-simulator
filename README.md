# iOS Device Control (chuk-mcp-ios)

> Comprehensive iOS device control system supporting both simulators and real devices. Available as both a standalone CLI tool and MCP (Model Context Protocol) server for AI assistant integration.

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![MCP Compatible](https://img.shields.io/badge/MCP-Compatible-green.svg)](https://modelcontextprotocol.io/)

## 🚀 Features

- **🎯 Unified Device Management**: Control iOS simulators and real devices through a single interface
- **📋 Session Management**: Create and manage device sessions for organized automation workflows
- **📱 App Lifecycle**: Install, launch, terminate, and manage iOS applications
- **🎮 UI Automation**: Tap, swipe, type, and interact with device interfaces
- **📸 Media & Location**: Add photos/videos, simulate GPS locations and routes
- **🔍 Debugging**: Access logs, crash reports, and debugging information
- **🤖 MCP Server**: Integration with Claude and other AI assistants
- **⚡ CLI Tool**: Standalone command-line interface for direct control

## 📋 Requirements

### For iOS Simulators (Primary)
- **macOS** with Xcode installed
- **Xcode Command Line Tools**: `xcode-select --install`
- At least one iOS Simulator runtime

### For Real Devices (Optional)
- iOS device with **Developer Mode** enabled
- Valid **Apple Developer** account (for app installation)
- One or more of these tools:
  - `idb` (Facebook's iOS Development Bridge) - Recommended
  - `devicectl` (Xcode 15+)
  - `instruments` (Legacy Xcode tool)

## 🔧 Installation

### Option 1: Using uv (Recommended)
```bash
# Install with uv
uv add chuk-mcp-ios

# Run directly
uvx chuk-mcp-ios cli status
```

### Option 2: Using pip
```bash
# Install from source
git clone https://github.com/yourusername/chuk-mcp-ios.git
cd chuk-mcp-ios
pip install -e .

# Or install from PyPI (when published)
pip install chuk-mcp-ios
```

### Verify Installation
```bash
# Check system status
chuk-mcp-ios cli status

# Should show available tools and devices
```

## ⚠️ Current Status & Recommendations

### CLI Issues Detected
Based on testing, the CLI has several bugs that need fixing:

1. **Session Resolution**: Sessions show active but commands fail to find devices
2. **Import Errors**: Missing `time` import causing crashes
3. **Device Resolution**: Direct UDID usage also failing

### Recommended Usage Order

**1. Direct simctl (Most Reliable)**
```bash
# Use native simulator tools directly
xcrun simctl list devices
xcrun simctl boot "iPhone 15" 
xcrun simctl io booted screenshot screenshot.png
xcrun simctl launch booted com.apple.Preferences
```

**2. Python API (Full Features)**
```bash
# Use the Python API directly for full functionality
python3 -c "
import asyncio
from chuk_mcp_ios.mcp.tools import ios_create_session, ios_screenshot
session = asyncio.run(ios_create_session())
print(f'Session: {session}')
"
```

**3. MCP Server (AI Integration)**
```bash
# Use MCP server for AI assistant integration
uvx chuk-mcp-ios mcp
# Then connect via Claude or other AI assistants
```

**4. CLI (Limited, Has Bugs)**
```bash
# CLI currently has issues but basic commands work:
uvx chuk-mcp-ios cli status        # ✅ Works
uvx chuk-mcp-ios cli device list   # ✅ Works  
uvx chuk-mcp-ios cli session list  # ✅ Works
uvx chuk-mcp-ios cli ui screenshot # ❌ Broken
uvx chuk-mcp-ios cli app list      # ❌ Broken
```

### Step-by-Step Working Example

Here's a complete sequence that actually works:

```bash
# 1. Check your system status
uvx chuk-mcp-ios cli status

# 2. List available devices to see what's available
uvx chuk-mcp-ios cli device list

# 3. Create a new session (this gives you a fresh session ID)
uvx chuk-mcp-ios cli session create --device "iPhone 15"
# Note: Copy the session ID from the output, e.g., session_1749425214_4b7f748f

# 4. List active sessions to verify
uvx chuk-mcp-ios cli session list

# 5. Use the actual session ID from step 3 for commands:
# Replace YOUR_SESSION_ID with the actual ID from step 3
uvx chuk-mcp-ios cli ui screenshot YOUR_SESSION_ID -o screenshot.png

# 6. Launch Settings app
uvx chuk-mcp-ios cli app launch YOUR_SESSION_ID com.apple.Preferences

# 7. Take another screenshot to see Settings
uvx chuk-mcp-ios cli ui screenshot YOUR_SESSION_ID -o settings.png

# 8. List installed apps
uvx chuk-mcp-ios cli app list YOUR_SESSION_ID

# 9. Clean up when done
uvx chuk-mcp-ios cli session terminate YOUR_SESSION_ID
```

### Working Example (With Workarounds)

```bash
# Method 1: Try session ID first, fallback to UDID
SESSION_ID="session_1749425214_4b7f748f"
UDID="D5ABE678-7395-4EF6-880B-E649F4FEDEE5"

# Try session ID
uvx chuk-mcp-ios cli ui screenshot $SESSION_ID -o screenshot.png

# If that fails, try UDID directly
if [ $? -ne 0 ]; then
    echo "Session failed, trying UDID..."
    uvx chuk-mcp-ios cli ui screenshot $UDID -o screenshot.png
fi

# Method 2: Direct device approach (most reliable)
# Get UDID from device list
uvx chuk-mcp-ios cli device list
# Copy the UDID and use it directly
uvx chuk-mcp-ios cli ui screenshot D5ABE678-7395-4EF6-880B-E649F4FEDEE5 -o screenshot.png

# Method 3: Fresh session approach
# Clean slate approach if sessions are buggy
uvx chuk-mcp-ios cli session terminate session_1749425214_4b7f748f
uvx chuk-mcp-ios cli session terminate automation_1749424425_58872b30
NEW_SESSION=$(uvx chuk-mcp-ios cli quick-start | grep -o 'session_[a-zA-Z0-9_]*')
uvx chuk-mcp-ios cli ui screenshot $NEW_SESSION -o screenshot.png
```

### Immediate Fix for Your Situation

```bash
# Based on your current sessions, try these in order:

# 1. Try direct UDID (most likely to work)
uvx chuk-mcp-ios cli ui screenshot D5ABE678-7395-4EF6-880B-E649F4FEDEE5 -o screenshot.png

# 2. If UDID doesn't work, test direct simctl
xcrun simctl io D5ABE678-7395-4EF6-880B-E649F4FEDEE5 screenshot test.png

# 3. If simctl works but CLI doesn't, it's a CLI bug
# Use Python API as workaround:
python3 -c "
import asyncio
from chuk_mcp_ios.mcp.tools import ios_screenshot
result = asyncio.run(ios_screenshot('D5ABE678-7395-4EF6-880B-E649F4FEDEE5', 'screenshot.png'))
print('Success!' if result.get('success') else f'Error: {result.get(\"error\")}')
"
```

### Alternative: Use Quick Start
```bash
# Auto-setup with best available device
uvx chuk-mcp-ios cli quick-start

# This creates a session and tells you the ID to use
# Then use that ID for subsequent commands
```

## 📚 CLI Examples

**First, check what commands are actually available:**
```bash
# Check main commands
chuk-mcp-ios cli --help

# Check UI subcommands
chuk-mcp-ios cli ui --help

# Check device subcommands  
chuk-mcp-ios cli device --help

# Check session subcommands
chuk-mcp-ios cli session --help

# Check app subcommands
chuk-mcp-ios cli app --help
```

### Device Management
```bash
# List all available devices (simulators + real devices)
chuk-mcp-ios cli device list

# List only simulators
chuk-mcp-ios cli device list --type simulator

# Show device details
chuk-mcp-ios cli device info DEVICE_UDID

# Boot a specific simulator
chuk-mcp-ios cli device boot DEVICE_UDID

# Shutdown simulator
chuk-mcp-ios cli device shutdown DEVICE_UDID
```

### Session Management
```bash
# Create session with auto-selected device
chuk-mcp-ios cli session create

# Create session with specific device name
chuk-mcp-ios cli session create --device "iPhone 15"

# Create session with specific UDID
chuk-mcp-ios cli session create --udid ABCD-1234-EFGH-5678

# List active sessions
chuk-mcp-ios cli session list

# Terminate session
chuk-mcp-ios cli session terminate session_123
```

### App Management
```bash
# List installed apps
chuk-mcp-ios cli app list session_123

# List only user apps (exclude system apps)
chuk-mcp-ios cli app list session_123 --user-only

# Install app from .app bundle
chuk-mcp-ios cli app install session_123 /path/to/MyApp.app

# Launch app by bundle ID
chuk-mcp-ios cli app launch session_123 com.example.myapp

# Terminate running app
chuk-mcp-ios cli app terminate session_123 com.example.myapp

# Uninstall app
chuk-mcp-ios cli app uninstall session_123 com.example.myapp
```

### UI Automation
```bash
# Take screenshot
chuk-mcp-ios cli ui screenshot session_123 -o /path/to/screenshot.png

# Tap at coordinates
chuk-mcp-ios cli ui tap session_123 100 200

# Type text (available commands based on your CLI implementation)
chuk-mcp-ios cli ui type session_123 "Hello World"

# Check available UI commands
chuk-mcp-ios cli ui --help
```

**Note**: The exact UI commands available depend on your CLI implementation. Check `chuk-mcp-ios cli ui --help` for the complete list.

### Media & Location
```bash
# Note: Check available commands with --help first
chuk-mcp-ios cli --help

# Location and media commands may be available under different subcommands
# Check for location commands:
chuk-mcp-ios cli location --help  # if location subcommand exists
chuk-mcp-ios cli media --help     # if media subcommand exists

# If not available via CLI, use Python API:
python3 -c "
from chuk_mcp_ios.core.media_manager import UnifiedMediaManager
media = UnifiedMediaManager()
media.set_location_by_name('your_session_id', 'San Francisco')
"
```

### Finding Available Commands

**The CLI structure may differ from this documentation. Always check available commands:**

```bash
# Discover main command structure
chuk-mcp-ios cli --help

# Check subcommands for each area
chuk-mcp-ios cli device --help
chuk-mcp-ios cli session --help  
chuk-mcp-ios cli app --help
chuk-mcp-ios cli ui --help

# If certain commands aren't available in CLI, they may be:
# 1. Available only via MCP tools
# 2. Available only via Python API
# 3. Named differently than documented

# Example: Check what UI commands actually exist
chuk-mcp-ios cli ui --help
# Output might show: tap, screenshot, type (but not press, swipe, etc.)
```

**Command Alternatives:**
```bash
# If CLI command doesn't exist, try Python API:
python3 -c "
import asyncio
from chuk_mcp_ios.mcp.tools import ios_press_button
result = asyncio.run(ios_press_button('session_123', 'home'))
print(result)
"

# Or check if it's an MCP-only feature
chuk-mcp-ios mcp  # Start MCP server and use via AI assistant
```

## 🤖 MCP Server Usage

### Starting the MCP Server
```bash
# Start MCP server (stdio mode)
chuk-mcp-ios mcp

# Start with specific configuration
chuk-mcp-ios mcp --host localhost --port 8080

# With debug logging
chuk-mcp-ios mcp --log-level DEBUG
```

### Claude Desktop Integration

Add to your Claude Desktop configuration (`~/Library/Application Support/Claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "ios-control": {
      "command": "uvx",
      "args": ["chuk-mcp-ios", "mcp"],
      "env": {
        "LOG_LEVEL": "INFO"
      }
    }
  }
}
```

### MCP Natural Language Examples

Once connected to Claude, you can use natural language:

```
🧑 "Take a screenshot of the current iOS simulator"
🤖 I'll take a screenshot for you...
   ✅ Screenshot saved to screenshot_20231215_143022.png

🧑 "Launch the Settings app and navigate to WiFi settings"
🤖 I'll launch Settings and help you navigate...
   ✅ Settings app launched
   ✅ Tapped on WiFi settings

🧑 "Set the device location to Tokyo and open Maps"
🤖 Setting location to Tokyo and opening Maps...
   ✅ Location set to Tokyo, Japan (35.6762, 139.6503)
   ✅ Maps app launched

🧑 "Install the app at /Users/me/MyApp.app and launch it"
🤖 I'll install and launch the app for you...
   ✅ App MyApp installed successfully
   ✅ App launched: com.example.myapp

🧑 "Simulate a user scrolling through a photo gallery"
🤖 I'll simulate scrolling through photos...
   ✅ Photos app launched
   ✅ Performed swipe gestures to scroll through gallery
```

### Available MCP Tools

The MCP server provides these tools:

```javascript
// Session Management
ios_create_session()
ios_list_sessions()
ios_terminate_session()

// Device Control  
ios_list_devices()
ios_boot_device()
ios_shutdown_device()

// App Management
ios_install_app()
ios_launch_app()
ios_terminate_app()
ios_uninstall_app()
ios_list_apps()

// UI Automation
ios_tap()
ios_double_tap()
ios_long_press()
ios_swipe()
ios_swipe_direction()
ios_input_text()
ios_press_button()
ios_screenshot()
ios_record_video()
ios_get_screen_info()

// Media & Location
ios_set_location()
ios_set_location_by_name()
ios_add_media()

// Utilities
ios_open_url()
ios_set_status_bar()
ios_set_appearance()
ios_clear_keychain()
ios_get_logs()
ios_set_permission()
ios_focus_simulator()
```

## 🐍 Python API Usage

### Basic Usage
```python
from chuk_mcp_ios.core.device_manager import UnifiedDeviceManager
from chuk_mcp_ios.core.session_manager import UnifiedSessionManager
from chuk_mcp_ios.core.ui_controller import UnifiedUIController

# Initialize managers
device_manager = UnifiedDeviceManager()
session_manager = UnifiedSessionManager()
ui_controller = UnifiedUIController()

# Set up session manager for UI controller
ui_controller.set_session_manager(session_manager)

# Create automation session
session_id = session_manager.create_automation_session()
print(f"Created session: {session_id}")

# Take screenshot
screenshot_path = ui_controller.take_screenshot(session_id, "test.png")
print(f"Screenshot saved: {screenshot_path}")

# Interact with UI
ui_controller.tap(session_id, 100, 200)
ui_controller.swipe_up(session_id)
ui_controller.input_text(session_id, "Hello World")

# Clean up
session_manager.terminate_session(session_id)
```

### Advanced Automation Example
```python
from chuk_mcp_ios.core import *
import time

async def automate_app_testing():
    """Example: Automated app testing workflow."""
    
    # Initialize managers
    device_mgr = UnifiedDeviceManager()
    session_mgr = UnifiedSessionManager()
    app_mgr = UnifiedAppManager()
    ui_ctrl = UnifiedUIController()
    
    # Link managers
    app_mgr.set_session_manager(session_mgr)
    ui_ctrl.set_session_manager(session_mgr)
    
    try:
        # Create session with iPhone simulator
        session_id = session_mgr.create_automation_session({
            'device_name': 'iPhone 15'
        })
        
        # Install test app
        app_info = app_mgr.install_app(
            session_id, 
            '/path/to/TestApp.app',
            AppInstallConfig(launch_after_install=True)
        )
        
        # Wait for app to load
        time.sleep(3)
        
        # Take screenshot of app launch
        ui_ctrl.take_screenshot(session_id, 'app_launch.png')
        
        # Perform test interactions
        ui_ctrl.tap(session_id, 200, 300)  # Tap login button
        ui_ctrl.input_text(session_id, 'test@example.com')
        ui_ctrl.tap(session_id, 200, 400)  # Tap password field
        ui_ctrl.input_text(session_id, 'password123')
        ui_ctrl.tap(session_id, 200, 500)  # Tap submit
        
        # Wait and verify
        time.sleep(2)
        ui_ctrl.take_screenshot(session_id, 'after_login.png')
        
        # Get app logs
        logs = logger_mgr.get_app_logs(session_id, app_info.bundle_id)
        print(f"Found {len(logs)} log entries")
        
    finally:
        # Clean up
        if 'session_id' in locals():
            session_mgr.terminate_session(session_id)

# Run the automation
import asyncio
asyncio.run(automate_app_testing())
```

## 📱 Real Device Setup

### Prerequisites
1. **Enable Developer Mode** (iOS 16+):
   - Connect device to Mac with Xcode
   - Settings → Privacy & Security → Developer Mode
   - Toggle ON and restart device

2. **Install idb** (Recommended):
   ```bash
   # Using Homebrew
   brew install idb-companion
   
   # Using pip
   pip install fb-idb
   ```

3. **Trust Computer**:
   - Connect device via USB
   - Tap "Trust" when prompted on device

### Real Device Examples
```bash
# List real devices
chuk-mcp-ios cli device list --type real

# Create session with real iPhone
chuk-mcp-ios cli session create --device "Chris's iPhone"

# Install app (requires developer certificate)
chuk-mcp-ios cli app install session_123 MyApp.ipa

# Same UI automation works on real devices
chuk-mcp-ios cli ui screenshot session_123 -o real_device.png
```

## 🔧 Configuration

### Environment Variables
```bash
# Tool paths (if not in PATH)
export IOS_CONTROL_SIMCTL_PATH="/usr/bin/xcrun simctl"
export IOS_CONTROL_IDB_PATH="/usr/local/bin/idb"
export IOS_CONTROL_DEVICECTL_PATH="/usr/bin/xcrun devicectl"

# Timeouts
export IOS_CONTROL_DEFAULT_TIMEOUT=30
export IOS_CONTROL_BOOT_TIMEOUT=60

# Logging
export IOS_CONTROL_LOG_LEVEL=INFO
export IOS_CONTROL_LOG_DIR="$HOME/.ios-control/logs"
```

### Configuration File
Create `~/.ios-control/config.yaml`:
```yaml
defaults:
  timeout: 30
  screenshot_format: png
  
devices:
  preferred_simulator: "iPhone 15 Pro"
  auto_boot: true
  
logging:
  level: INFO
  file_logging: true
  
mcp:
  host: localhost
  port: 8080
```

## 📊 Examples & Demos

### Run Built-in Demos
```bash
# Interactive demo (menu-driven)
python -m chuk_mcp_ios.examples.interactive_demo

# Automated end-to-end demo
python -m chuk_mcp_ios.examples.automated_demo

# MCP server demonstration
python -m chuk_mcp_ios.examples.e2e_mcp_demo

# Web scraping demo (Techmeme)
python -m chuk_mcp_ios.examples.techmeme --auto
```

### Custom Automation Scripts
```python
# examples/custom_automation.py
from chuk_mcp_ios import *

def test_settings_navigation():
    """Test navigating through iOS Settings."""
    with AutomationSession() as session:
        # Launch Settings
        session.launch_app('com.apple.Preferences')
        session.screenshot('settings_main.png')
        
        # Navigate to WiFi
        session.tap_text('Wi-Fi')
        session.screenshot('wifi_settings.png')
        
        # Navigate back
        session.tap_back_button()
        session.screenshot('settings_back.png')

if __name__ == "__main__":
    test_settings_navigation()
```

## 🏗️ Architecture

```
chuk-mcp-ios/
├── core/                   # Core functionality (device-agnostic)
│   ├── base.py            # Base classes and interfaces
│   ├── device_manager.py  # Unified device management
│   ├── session_manager.py # Session lifecycle management
│   ├── app_manager.py     # App installation and control
│   ├── ui_controller.py   # UI automation and gestures
│   ├── media_manager.py   # Photos, videos, and location
│   ├── logger_manager.py  # Logging and crash reports
│   └── utilities_manager.py # Misc utilities and settings
├── devices/               # Device-specific implementations
│   ├── simulator.py       # iOS Simulator support
│   ├── real_device.py     # Real device support
│   └── detector.py        # Device discovery and detection
├── mcp/                   # MCP server implementation
│   ├── tools.py          # MCP tool definitions
│   ├── models.py         # Pydantic models for validation
│   └── main.py           # MCP server entry point
├── cli/                   # Command-line interface
│   └── main.py           # CLI entry point and commands
└── examples/              # Usage examples and demos
    ├── interactive_demo.py
    ├── automated_demo.py
    ├── e2e_mcp_demo.py
    └── techmeme.py
```

## 🧪 Development

### Setup Development Environment
```bash
# Clone repository
git clone https://github.com/yourusername/chuk-mcp-ios.git
cd chuk-mcp-ios

# Install in development mode with dev dependencies
pip install -e ".[dev]"

# Or with uv
uv sync --dev
```

### Running Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=chuk_mcp_ios

# Run specific test file
pytest tests/test_device_manager.py

# Run integration tests (requires simulators)
pytest tests/integration/ -m "not slow"
```

### Code Quality
```bash
# Format code
black src/ tests/

# Sort imports
isort src/ tests/

# Type checking
mypy src/

# Lint
flake8 src/
```

### Adding New Features

1. **Add interfaces** to `core/base.py`
2. **Implement functionality** in appropriate core module
3. **Add MCP tool** in `mcp/tools.py` with proper validation
4. **Add CLI command** in `cli/main.py`
5. **Write tests** in `tests/`
6. **Add examples** in `examples/`
7. **Update documentation**

## 🐛 Troubleshooting

### Current Known Issues

**Multiple CLI Issues Identified:**

1. **Session Resolution Bug**: Sessions show active but can't be used
2. **Missing Import Error**: `name 'time' is not defined` 
3. **Device Resolution Bug**: UUIDs not working either

```bash
# These errors indicate code-level issues:
uvx chuk-mcp-ios cli app list session_1749426020_9ff9470b
# ❌ Failed: Device not found: session_1749426020_9ff9470b

uvx chuk-mcp-ios cli app list 45007866-72A3-4ACD-AD98-7EC58A726372  
# ❌ Failed: name 'time' is not defined
```

### Immediate Workarounds

**Option 1: Use Direct simctl Commands**
```bash
# Bypass the CLI entirely and use simctl directly
UDID="45007866-72A3-4ACD-AD98-7EC58A726372"

# Take screenshot
xcrun simctl io $UDID screenshot screenshot.png

# Launch app
xcrun simctl launch $UDID com.apple.Preferences

# List installed apps (basic)
xcrun simctl listapps $UDID

# Boot device if needed
xcrun simctl boot $UDID
```

**Option 2: Use Python API Directly**
```bash
# Create a simple Python script to bypass CLI issues
cat << 'EOF' > ios_test.py
#!/usr/bin/env python3
import asyncio
import sys
import os
sys.path.insert(0, '.')

async def main():
    from chuk_mcp_ios.mcp.tools import (
        ios_list_devices, 
        ios_create_session, 
        ios_screenshot,
        ios_list_apps
    )
    
    # List devices
    print("=== Devices ===")
    devices = await ios_list_devices()
    print(devices)
    
    # Create session
    print("\n=== Creating Session ===")
    session = await ios_create_session(device_name="iPhone 15")
    if 'error' in session:
        print(f"Error: {session['error']}")
        return
    
    session_id = session['session_id']
    print(f"Session: {session_id}")
    
    # Take screenshot
    print("\n=== Screenshot ===")
    screenshot = await ios_screenshot(session_id, "test.png")
    print(screenshot)
    
    # List apps
    print("\n=== Apps ===")
    apps = await ios_list_apps(session_id)
    print(f"Found {len(apps.get('apps', []))} apps")

if __name__ == "__main__":
    asyncio.run(main())
EOF

python3 ios_test.py
```

**Option 3: MCP Server Usage (Most Reliable)**
```bash
# Start MCP server in one terminal
uvx chuk-mcp-ios mcp

# In another terminal or via AI assistant, use MCP tools
# This bypasses the CLI entirely and uses the core MCP functions
```

### Manual Device Operations

**Direct Simulator Control (Always Works):**
```bash
# List all simulators
xcrun simctl list devices

# Boot a specific simulator
xcrun simctl boot "iPhone 15"

# Take screenshot
xcrun simctl io booted screenshot screenshot.png

# Launch Settings
xcrun simctl launch booted com.apple.Preferences

# Add media
xcrun simctl addmedia booted ~/Desktop/*.jpg

# Set location
xcrun simctl location booted set 37.7749,-122.4194
```

### Debugging the CLI Issues

**To help identify the problems:**
```bash
# 1. Check if core imports work
python3 -c "
try:
    from chuk_mcp_ios.core.device_manager import UnifiedDeviceManager
    print('✅ Core imports work')
except Exception as e:
    print(f'❌ Import error: {e}')
"

# 2. Check if time import is missing somewhere
python3 -c "
import chuk_mcp_ios.core.app_manager
print('✅ App manager imports work')
"

# 3. Minimal device test
python3 -c "
from chuk_mcp_ios.core.device_manager import UnifiedDeviceManager
dm = UnifiedDeviceManager()
devices = dm.discover_all_devices()
print(f'Found {len(devices)} devices')
for d in devices:
    print(f'  {d.name}: {d.udid}')
"
```

### Known Issues and Workarounds

**Session ID Resolution Problem:**
If sessions show as active but commands fail, this might be a bug in session-to-device resolution:

```bash
# Workaround 1: Use device UDID directly (bypass sessions)
# Get UDID from session list, then use it directly
UDID="D5ABE678-7395-4EF6-880B-E649F4FEDEE5"  # From session list
uvx chuk-mcp-ios cli ui screenshot $UDID -o screenshot.png

# Workaround 2: Use quick-start for guaranteed working session
uvx chuk-mcp-ios cli quick-start
# Use the session ID that quick-start returns

# Workaround 3: Python API bypass (if CLI has issues)
python3 -c "
import asyncio
from chuk_mcp_ios.mcp.tools import ios_screenshot
result = asyncio.run(ios_screenshot('session_1749425214_4b7f748f', 'screenshot.png'))
print(result)
"
```

### Verified Working Commands

**These commands should definitely work:**
```bash
# 1. System check (always works)
uvx chuk-mcp-ios cli status

# 2. Device listing (always works)
uvx chuk-mcp-ios cli device list

# 3. Direct device operations (bypass sessions)
# Use UDID from device list directly
uvx chuk-mcp-ios cli device info DEVICE_UDID

# 4. Session management (metadata operations)
uvx chuk-mcp-ios cli session list
uvx chuk-mcp-ios cli session create --device "iPhone 15"
uvx chuk-mcp-ios cli session terminate SESSION_ID
```

### Troubleshooting Steps

```bash
# Step 1: Verify simulator is actually running
xcrun simctl list devices | grep Booted

# Step 2: Test direct simctl access
xcrun simctl io D5ABE678-7395-4EF6-880B-E649F4FEDEE5 screenshot direct_test.png

# Step 3: If direct simctl works but CLI doesn't, it's a session resolution bug
# Report this as an issue and use direct UDID as workaround

# Step 4: Clean restart if needed
uvx chuk-mcp-ios cli session terminate --all  # if available
# Or manually terminate each session
uvx chuk-mcp-ios cli session terminate session_1749425214_4b7f748f
uvx chuk-mcp-ios cli session terminate automation_1749424425_58872b30
```

**Device Not Found:**
```bash
# Problem: No devices available
# Solution: Check simulators and boot one

# List available devices
uvx chuk-mcp-ios cli device list

# Boot a simulator if none are running
uvx chuk-mcp-ios cli device boot DEVICE_UDID_FROM_LIST

# Then create session
uvx chuk-mcp-ios cli session create --udid DEVICE_UDID_FROM_LIST
```

**Command Not Found:**
```bash
# Problem: Command like 'press' doesn't exist
# Solution: Check available commands

uvx chuk-mcp-ios cli ui --help  # See actual UI commands
uvx chuk-mcp-ios cli --help     # See all available commands

# Many advanced features are MCP-only or Python API-only
```

### Getting Help

1. **Check system status**: `chuk-mcp-ios cli status`
2. **Review logs**: `~/.ios-control/logs/`
3. **Run diagnostics**: `chuk-mcp-ios cli diagnose`
4. **Check GitHub issues**: [Issues page](https://github.com/yourusername/chuk-mcp-ios/issues)

## 🤝 Contributing

We welcome contributions! Here's how to get started:

1. **Fork** the repository
2. **Create** feature branch (`git checkout -b feature/amazing-feature`)
3. **Make** your changes with tests
4. **Format** code (`black`, `isort`)
5. **Test** thoroughly (`pytest`)
6. **Commit** changes (`git commit -m 'Add amazing feature'`)
7. **Push** branch (`git push origin feature/amazing-feature`)
8. **Open** Pull Request

### Contribution Guidelines
- Add tests for new features
- Update documentation
- Follow existing code style
- Add examples for complex features
- Update changelog

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details

## 🙏 Acknowledgments

- **Apple** for iOS Simulator and development tools
- **Facebook** for idb (iOS Development Bridge)
- **Anthropic** for MCP (Model Context Protocol)
- **Open source community** for tools and libraries used

## 📞 Support

- **Documentation**: [Full docs](https://github.com/yourusername/chuk-mcp-ios/wiki)
- **Issues**: [GitHub Issues](https://github.com/yourusername/chuk-mcp-ios/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/chuk-mcp-ios/discussions)
- **MCP Community**: [MCP Discord](https://discord.gg/mcp)

---

**Made with ❤️ for iOS automation and AI integration**