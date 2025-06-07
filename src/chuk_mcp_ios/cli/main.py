#!/usr/bin/env python3
# chuk_mcp_ios/cli/main.py
"""
iOS Device Control CLI

Command-line interface for controlling iOS simulators and real devices.
Works independently of MCP server.
"""

import click
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from chuk_mcp_ios.core.base import check_ios_development_setup
from chuk_mcp_ios.core.device_manager import UnifiedDeviceManager
from chuk_mcp_ios.core.session_manager import UnifiedSessionManager
from chuk_mcp_ios.core.app_manager import UnifiedAppManager
from chuk_mcp_ios.core.ui_controller import UnifiedUIController

# Global managers (initialized on demand)
device_manager = None
session_manager = None
app_manager = None
ui_controller = None

def get_managers():
    """Initialize managers on demand."""
    global device_manager, session_manager, app_manager, ui_controller
    
    if device_manager is None:
        device_manager = UnifiedDeviceManager()
        session_manager = UnifiedSessionManager()
        app_manager = UnifiedAppManager()
        ui_controller = UnifiedUIController()
    
    return device_manager, session_manager, app_manager, ui_controller

@click.group()
@click.version_option(version="1.0.0")
def cli():
    """iOS Device Control CLI - Manage iOS simulators and real devices."""
    pass

# Device Commands
@cli.group()
def device():
    """Device management commands."""
    pass

@device.command()
@click.option('--type', 'device_type', type=click.Choice(['all', 'simulator', 'real']), default='all')
@click.option('--capabilities', is_flag=True, help='Show device capabilities')
def list(device_type, capabilities):
    """List available devices."""
    try:
        dm, _, _, _ = get_managers()
        dm.print_device_list(show_capabilities=capabilities)
    except Exception as e:
        click.echo(f"❌ Failed to list devices: {e}", err=True)
        sys.exit(1)

@device.command()
@click.argument('udid')
@click.option('--timeout', default=30, help='Boot timeout in seconds')
def boot(udid, timeout):
    """Boot/connect a device."""
    try:
        dm, _, _, _ = get_managers()
        dm.boot_device(udid, timeout)
        click.echo(f"✅ Device {udid[:8]}... booted/connected")
    except Exception as e:
        click.echo(f"❌ Failed: {e}", err=True)
        sys.exit(1)

@device.command()
@click.argument('udid')
def shutdown(udid):
    """Shutdown a device (simulators only)."""
    try:
        dm, _, _, _ = get_managers()
        dm.shutdown_device(udid)
        click.echo(f"✅ Device {udid[:8]}... shutdown")
    except Exception as e:
        click.echo(f"❌ Failed: {e}", err=True)
        sys.exit(1)

@device.command()
@click.argument('udid')
def info(udid):
    """Show device information."""
    try:
        dm, _, _, _ = get_managers()
        device = dm.get_device(udid)
        if device:
            click.echo(f"\n📱 Device Information:")
            click.echo(f"   Name: {device.name}")
            click.echo(f"   UDID: {device.udid}")
            click.echo(f"   Type: {device.device_type.value}")
            click.echo(f"   OS: {device.os_version}")
            click.echo(f"   Model: {device.model}")
            click.echo(f"   State: {device.state.value}")
            click.echo(f"   Connection: {device.connection_type}")
            
            caps = dm.get_device_capabilities(udid)
            enabled_caps = [k.replace('_', ' ') for k, v in caps.items() if v]
            click.echo(f"   Capabilities: {', '.join(enabled_caps)}")
        else:
            click.echo(f"❌ Device not found: {udid}", err=True)
            sys.exit(1)
    except Exception as e:
        click.echo(f"❌ Failed to get device info: {e}", err=True)
        sys.exit(1)

# Session Commands
@cli.group()
def session():
    """Session management commands."""
    pass

@session.command()
@click.option('--device', 'device_name', help='Device name')
@click.option('--udid', help='Device UDID')
@click.option('--type', 'device_type', type=click.Choice(['simulator', 'real']), help='Device type')
@click.option('--no-boot', is_flag=True, help='Don\'t auto-boot simulators')
def create(device_name, udid, device_type, no_boot):
    """Create a new device session."""
    try:
        from chuk_mcp_ios.core.base import DeviceType
        from chuk_mcp_ios.core.session_manager import SessionConfig
        
        config = SessionConfig(
            device_name=device_name,
            device_udid=udid,
            autoboot=not no_boot
        )
        
        if device_type:
            config.device_type = DeviceType(device_type)
        
        _, sm, _, _ = get_managers()
        session_id = sm.create_session(config)
        info = sm.get_session_info(session_id)
        
        click.echo(f"✅ Session created: {session_id}")
        click.echo(f"   Device: {info['device_name']}")
        click.echo(f"   Type: {info['device_type']}")
        click.echo(f"   UDID: {info['device_udid']}")
    except Exception as e:
        click.echo(f"❌ Failed: {e}", err=True)
        sys.exit(1)

@session.command()
def list():
    """List active sessions."""
    try:
        _, sm, _, _ = get_managers()
        sm.print_sessions_status()
    except Exception as e:
        click.echo(f"❌ Failed to list sessions: {e}", err=True)
        sys.exit(1)

@session.command()
@click.argument('session_id')
def terminate(session_id):
    """Terminate a session."""
    try:
        _, sm, _, _ = get_managers()
        sm.terminate_session(session_id)
        click.echo(f"✅ Session terminated: {session_id}")
    except Exception as e:
        click.echo(f"❌ Failed: {e}", err=True)
        sys.exit(1)

# App Commands
@cli.group()
def app():
    """App management commands."""
    pass

@app.command()
@click.argument('session_id')
@click.argument('app_path')
def install(session_id, app_path):
    """Install an app."""
    try:
        _, _, am, _ = get_managers()
        app_info = am.install_app(session_id, app_path)
        click.echo(f"✅ Installed: {app_info.name} ({app_info.bundle_id})")
    except Exception as e:
        click.echo(f"❌ Failed: {e}", err=True)
        sys.exit(1)

@app.command()
@click.argument('session_id')
@click.argument('bundle_id')
def launch(session_id, bundle_id):
    """Launch an app."""
    try:
        _, _, am, _ = get_managers()
        am.launch_app(session_id, bundle_id)
        click.echo(f"✅ Launched: {bundle_id}")
    except Exception as e:
        click.echo(f"❌ Failed: {e}", err=True)
        sys.exit(1)

@app.command(name='list')  # Avoid conflict with Python's list builtin
@click.argument('session_id')
@click.option('--user-only', is_flag=True, help='Show only user apps')
def list_apps(session_id, user_only):
    """List installed apps."""
    try:
        _, _, am, _ = get_managers()
        apps = am.list_apps(session_id, user_apps_only=user_only)
        
        click.echo(f"\n📱 Installed Apps ({len(apps)}):")
        for app in apps:
            click.echo(f"   {app.name}")
            click.echo(f"      Bundle ID: {app.bundle_id}")
            if app.version:
                click.echo(f"      Version: {app.version}")
    except Exception as e:
        click.echo(f"❌ Failed: {e}", err=True)
        sys.exit(1)

# UI Commands
@cli.group()
def ui():
    """UI automation commands."""
    pass

@ui.command()
@click.argument('session_id')
@click.argument('x', type=int)
@click.argument('y', type=int)
def tap(session_id, x, y):
    """Tap at coordinates."""
    try:
        _, _, _, uc = get_managers()
        uc.tap(session_id, x, y)
        click.echo(f"✅ Tapped at ({x}, {y})")
    except Exception as e:
        click.echo(f"❌ Failed: {e}", err=True)
        sys.exit(1)

@ui.command()
@click.argument('session_id')
@click.argument('text')
def type(session_id, text):
    """Type text."""
    try:
        _, _, _, uc = get_managers()
        uc.input_text(session_id, text)
        click.echo(f"✅ Typed: {text}")
    except Exception as e:
        click.echo(f"❌ Failed: {e}", err=True)
        sys.exit(1)

@ui.command()
@click.argument('session_id')
@click.option('--output', '-o', help='Output file path')
def screenshot(session_id, output):
    """Take a screenshot."""
    try:
        _, _, _, uc = get_managers()
        path = uc.take_screenshot(session_id, output)
        click.echo(f"✅ Screenshot saved: {path}")
    except Exception as e:
        click.echo(f"❌ Failed: {e}", err=True)
        sys.exit(1)

# Quick Actions
@cli.command()
@click.option('--device', help='Device name or UDID')
def quick_start(device):
    """Quick start with automatic setup."""
    try:
        # Check setup first
        setup_info = check_ios_development_setup()
        if not setup_info['command_line_tools']:
            click.echo("❌ Xcode Command Line Tools not installed")
            click.echo("   Run: xcode-select --install")
            sys.exit(1)
        
        if not setup_info['simulators_available']:
            click.echo("❌ No iOS simulators available")
            click.echo("   Install simulators via Xcode > Settings > Platforms")
            sys.exit(1)
        
        # Create session
        _, sm, _, _ = get_managers()
        config = {'device_name': device} if device else {}
        session_id = sm.create_automation_session(config)
        
        click.echo(f"✅ Quick start session: {session_id}")
        click.echo("\nYou can now use this session ID with other commands.")
        click.echo(f"Example: ios-control ui tap {session_id} 100 200")
        click.echo(f"Example: ios-control ui screenshot {session_id} -o screenshot.png")
    except Exception as e:
        click.echo(f"❌ Failed: {e}", err=True)
        sys.exit(1)

@cli.command()
def status():
    """Show system status and setup information."""
    click.echo("\n📱 iOS Device Control Status")
    click.echo("=" * 40)
    
    # Check iOS development setup
    setup_info = check_ios_development_setup()
    
    # Basic setup
    click.echo("\n🔧 iOS Development Setup:")
    status_icon = "✅" if setup_info['command_line_tools'] else "❌"
    click.echo(f"  {status_icon} Xcode Command Line Tools")
    
    status_icon = "✅" if setup_info['xcode_installed'] else "⚠️ "
    click.echo(f"  {status_icon} Full Xcode Installation")
    
    status_icon = "✅" if setup_info['simulator_app_found'] else "❌"
    click.echo(f"  {status_icon} Simulator.app")
    
    # Available tools
    click.echo("\n🛠️  Available Tools:")
    tools = setup_info['available_tools']
    for tool, available in tools.items():
        status_icon = "✅" if available else "❌"
        description = {
            'simctl': 'iOS Simulator control (required)',
            'idb': 'Real device support (optional)', 
            'devicectl': 'Xcode 15+ device control (optional)',
            'instruments': 'Legacy device tools (optional)'
        }.get(tool, tool)
        
        click.echo(f"  {status_icon} {tool} - {description}")
    
    # Try to get device stats (only if simctl is available)
    if tools['simctl']:
        try:
            dm, sm, _, _ = get_managers()
            stats = dm.get_statistics()
            
            click.echo(f"\n📊 Device Statistics:")
            click.echo(f"  Total devices: {stats['total_devices']}")
            click.echo(f"    Simulators: {stats['simulators']}")
            click.echo(f"    Real devices: {stats['real_devices']}")
            click.echo(f"    Available: {stats['available_devices']}")
            
            if setup_info.get('simulator_count', 0) > 0:
                click.echo(f"  iOS Simulators: {setup_info['simulator_count']} available")
                
            # Active sessions
            sessions = sm.list_sessions()
            click.echo(f"\n📊 Active sessions: {len(sessions)}")
            
            if sessions:
                click.echo("  Sessions:")
                for session_id in sessions[:3]:  # Show first 3
                    try:
                        info = sm.get_session_info(session_id)
                        status_icon = "🟢" if info['is_available'] else "🔴"
                        click.echo(f"    {status_icon} {session_id} - {info['device_name']}")
                    except:
                        click.echo(f"    ❓ {session_id} - Status unknown")
                
                if len(sessions) > 3:
                    click.echo(f"    ... and {len(sessions) - 3} more")
                    
        except Exception as e:
            click.echo(f"\n⚠️  Could not get device statistics: {e}")
    else:
        click.echo(f"\n❌ simctl not available - cannot check devices")
    
    # Recommendations
    if setup_info['recommendations']:
        click.echo(f"\n💡 Recommendations:")
        for rec in setup_info['recommendations']:
            click.echo(f"  • {rec}")
    
    # Overall status
    click.echo(f"\n🎯 Overall Status:")
    if setup_info['command_line_tools'] and setup_info['simulators_available']:
        click.echo("  ✅ Ready for iOS Simulator automation")
        click.echo("  💡 Try: ios-control quick-start")
    elif setup_info['command_line_tools']:
        click.echo("  ⚠️  Basic tools available, but no simulators found")
        click.echo("  💡 Install simulators via Xcode > Settings > Platforms")
    else:
        click.echo("  ❌ Setup incomplete - see recommendations above")
    
    if tools.get('idb') or tools.get('devicectl'):
        click.echo("  ✅ Real device support available")
    else:
        click.echo("  ⚠️  No real device tools found (optional)")

def main():
    """Main CLI entry point."""
    try:
        cli()
    except KeyboardInterrupt:
        click.echo("\n\n👋 Interrupted by user")
        sys.exit(130)
    except Exception as e:
        click.echo(f"\n❌ Unexpected error: {e}", err=True)
        sys.exit(1)

if __name__ == "__main__":
    main()