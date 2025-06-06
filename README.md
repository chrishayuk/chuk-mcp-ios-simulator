# iOS Device Control (chuk-mcp-ios)

Comprehensive iOS device control system supporting both simulators and real devices. Available as both a standalone CLI tool and MCP (Model Context Protocol) server.

## Features

- **Unified Device Management**: Control both iOS simulators and real devices through a single interface
- **Session Management**: Create and manage device sessions for organized automation
- **App Management**: Install, launch, and manage iOS applications
- **UI Automation**: Tap, swipe, type, and interact with device UI
- **Media & Location**: Add photos/videos, simulate GPS locations
- **Debugging**: Access logs, crash reports, and debugging tools
- **MCP Server**: Use with AI assistants via Model Context Protocol
- **CLI Tool**: Standalone command-line interface for direct control

## Requirements

### For Simulators
- macOS with Xcode installed
- Xcode Command Line Tools (`xcode-select --install`)

### For Real Devices (Optional)
- iOS device with developer mode enabled
- Valid Apple Developer account (for app installation)
- One or more of:
  - `idb` (Facebook's iOS Development Bridge)
  - `devicectl` (Xcode 15+)
  - `instruments` (Legacy Xcode tool)

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/chuk-mcp-ios.git
cd chuk-mcp-ios

# Install in development mode
pip install -e .

# Or install from PyPI (when published)
pip install chuk-mcp-ios
```

## Quick Start

### CLI Usage

```bash
# Check system status
ios-control status

# List available devices
ios-control device list

# Quick start with auto-setup
ios-control quick-start

# Create a session
ios-control session create --device "iPhone 15"

# Take a screenshot
ios-control ui screenshot SESSION_ID -o screenshot.png

# Launch an app
ios-control app launch SESSION_ID com.apple.Preferences
```

### MCP Server Usage

1. Start the MCP server:
```bash
ios-mcp-server
```

2. Configure your AI assistant to connect to the MCP server

3. Use natural language commands:
- "Take a screenshot of the current screen"
- "Launch the Settings app"
- "Set location to San Francisco"

### Python API Usage

```python
from chuk_mcp_ios.core.device_manager import UnifiedDeviceManager
from chuk_mcp_ios.core.session_manager import UnifiedSessionManager
from chuk_mcp_ios.core.ui_controller import UnifiedUIController

# Initialize managers
device_manager = UnifiedDeviceManager()
session_manager = UnifiedSessionManager()
ui_controller = UnifiedUIController()

# Create a session
session_id = session_manager.create_automation_session()

# Take a screenshot
ui_controller.take_screenshot(session_id, "screenshot.png")

# Tap at coordinates
ui_controller.tap(session_id, 100, 200)

# Clean up
session_manager.terminate_session(session_id)
```

## Examples

### Run Quick Demo
```bash
# Basic demo
python -m chuk_mcp_ios.examples.quick_demo

# Interactive demo
python -m chuk_mcp_ios.examples.quick_demo --interactive
```

### Automation Example
```python
from chuk_mcp_ios.examples.automation_demo import AutomationDemo

demo = AutomationDemo()
demo.run_test_scenario()
```

## Architecture

```
├── core/               # Core functionality (device-agnostic)
├── devices/            # Device-specific implementations
├── mcp/                # MCP server implementation
├── cli/                # Command-line interface
└── examples/           # Usage examples
```

## Supported Operations

### Device Management
- List devices (simulators and real devices)
- Boot/shutdown simulators
- Connect/disconnect real devices
- Get device information and capabilities

### App Management
- Install apps (.app bundles or .ipa files)
- Launch and terminate apps
- List installed apps
- Manage app permissions

### UI Automation
- Tap, swipe, pinch, zoom gestures
- Type text
- Press hardware buttons
- Take screenshots and record videos

### Media & Location
- Add photos and videos to device
- Set GPS location
- Simulate location routes

### Debugging
- View system and app logs
- Access crash reports
- Manage debug server

## Development

### Setup Development Environment
```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black src/

# Type checking
mypy src/
```

### Adding New Features

1. Add interfaces to `core/base.py`
2. Implement in appropriate module
3. Add MCP tool in `mcp/tools.py`
4. Add CLI command in `cli/commands/`
5. Add tests and examples

## Troubleshooting

### Simulator Issues
- Ensure Xcode is installed: `xcode-select -p`
- Reset simulators: `xcrun simctl erase all`

### Real Device Issues
- Enable developer mode on device
- Trust computer when prompted
- Check USB/WiFi connection

### Tool Detection
Run `ios-control status` to see which tools are available

## Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## License

MIT License - see LICENSE file for details

## Acknowledgments

- Apple for iOS Simulator and development tools
- Facebook for idb
- MCP community for protocol standards