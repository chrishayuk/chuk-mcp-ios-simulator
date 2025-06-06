#!/usr/bin/env python3
# chuk_mcp_ios/cli/__init__.py
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

from chuk_mcp_ios.core.device_manager import UnifiedDeviceManager
from chuk_mcp_ios.core.session_manager import UnifiedSessionManager
from chuk_mcp_ios.core.app_manager import UnifiedAppManager
from chuk_mcp_ios.core.ui_controller import UnifiedUIController

# Global managers
device_manager = UnifiedDeviceManager()
session_manager = UnifiedSessionManager()
app_manager = UnifiedAppManager()
ui_controller = UnifiedUIController()

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
    device_manager.print_device_list(show_capabilities=capabilities)

@device.command()
@click.argument('udid')
@click.option('--timeout', default=30, help='Boot timeout in seconds')
def boot(udid, timeout):
    """Boot/connect a device."""
    try:
        device_manager.boot_device(udid, timeout)
        click.echo(f"✅ Device {udid[:8]}... booted/connected")
    except Exception as e:
        click.echo(f"❌ Failed: {e}", err=True)
        sys.exit(1)

@device.command()
@click.argument('udid')
def shutdown(udid):
    """Shutdown a device (simulators only)."""
    try:
        device_manager.shutdown_device(udid)
        click.echo(f"✅ Device {udid[:8]}... shutdown")
    except Exception as e:
        click.echo(f"❌ Failed: {e}", err=True)
        sys.exit(1)

@device.command()
@click.argument('udid')
def info(udid):
    """Show device information."""
    device = device_manager.get_device(udid)
    if device:
        click.echo(f"\n📱 Device Information:")
        click.echo(f"   Name: {device.name}")
        click.echo(f"   UDID: {device.udid}")
        click.echo(f"   Type: {device.device_type.value}")
        click.echo(f"   OS: {device.os_version}")
        click.echo(f"   Model: {device.model}")
        click.echo(f"   State: {device.state.value}")
        click.echo(f"   Connection: {device.connection_type}")
        
        caps = device_manager.get_device_capabilities(udid)
        enabled_caps = [k.replace('_', ' ') for k, v in caps.items() if v]
        click.echo(f"   Capabilities: {', '.join(enabled_caps)}")
    else:
        click.echo(f"❌ Device not found: {udid}", err=True)
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
    from chuk_mcp_ios.core.base import DeviceType
    
    config = {
        'device_name': device_name,
        'device_udid': udid,
        'autoboot': not no_boot
    }
    
    if device_type:
        config['device_type'] = DeviceType(device_type)
    
    try:
        session_id = session_manager.create_session(config)
        info = session_manager.get_session_info(session_id)
        
        click.echo(f"✅ Session created: {session_id}")
        click.echo(f"   Device: {info['device_name']}")
        click.echo(f"   Type: {info['device_type']}")
        click.echo(f"   UDID: {info['udid']}")
    except Exception as e:
        click.echo(f"❌ Failed: {e}", err=True)
        sys.exit(1)

@session.command()
def list():
    """List active sessions."""
    session_manager.print_sessions_status()

@session.command()
@click.argument('session_id')
def terminate(session_id):
    """Terminate a session."""
    try:
        session_manager.terminate_session(session_id)
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
        app_info = app_manager.install_app(session_id, app_path)
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
        app_manager.launch_app(session_id, bundle_id)
        click.echo(f"✅ Launched: {bundle_id}")
    except Exception as e:
        click.echo(f"❌ Failed: {e}", err=True)
        sys.exit(1)

@app.command()
@click.argument('session_id')
@click.option('--user-only', is_flag=True, help='Show only user apps')
def list(session_id, user_only):
    """List installed apps."""
    try:
        apps = app_manager.list_apps(session_id, user_apps_only=user_only)
        
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
        ui_controller.tap(session_id, x, y)
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
        ui_controller.input_text(session_id, text)
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
        path = ui_controller.take_screenshot(session_id, output)
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
        # Create session
        config = {'device_name': device} if device else {}
        session_id = session_manager.create_automation_session(config)
        
        click.echo(f"✅ Quick start session: {session_id}")
        click.echo("\nYou can now use this session ID with other commands.")
        click.echo(f"Example: ios-control ui tap {session_id} 100 200")
    except Exception as e:
        click.echo(f"❌ Failed: {e}", err=True)
        sys.exit(1)

@cli.command()
def status():
    """Show system status."""
    stats = device_manager.get_statistics()
    
    click.echo("\n📱 iOS Device Control Status")
    click.echo("=" * 40)
    click.echo(f"Total devices: {stats['total_devices']}")
    click.echo(f"  Simulators: {stats['simulators']}")
    click.echo(f"  Real devices: {stats['real_devices']}")
    click.echo(f"  Available: {stats['available_devices']}")
    
    click.echo("\n🔧 Available tools:")
    for tool, available in stats['tools_available'].items():
        status = "✅" if available else "❌"
        click.echo(f"  {status} {tool}")
    
    sessions = session_manager.list_sessions()
    click.echo(f"\n📊 Active sessions: {len(sessions)}")

def main():
    """Main CLI entry point."""
    cli()

if __name__ == "__main__":
    main()