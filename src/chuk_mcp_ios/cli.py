#!/usr/bin/env python3
"""
Main iOS Simulator Controller
A comprehensive modular framework for controlling iOS Simulator with idb integration.
"""

import sys
import argparse
from typing import Optional, List, Dict, Any
from ios_simulator_base import SessionConfig
from session_manager import SessionManager
from simulator_manager import SimulatorManager
from app_manager import AppManager
from ui_controller import UIController
from media_manager import MediaManager
from logger_manager import LoggerManager
from utilities_manager import UtilitiesManager

class iOSSimulatorController:
    """
    Main controller that orchestrates all iOS simulator operations.
    Provides a unified interface to all simulator management capabilities.
    """
    
    def __init__(self):
        # Initialize all managers
        self.session_manager = SessionManager()
        self.simulator_manager = SimulatorManager()
        self.app_manager = AppManager()
        self.ui_controller = UIController()
        self.media_manager = MediaManager()
        self.logger_manager = LoggerManager()
        self.utilities_manager = UtilitiesManager()
    
    # Session Management
    def create_session(self, device_name: Optional[str] = None, 
                      platform_version: Optional[str] = None, autoboot: bool = True) -> str:
        """Create a new simulator session."""
        config = SessionConfig(device_name=device_name, platform_version=platform_version, autoboot=autoboot)
        return self.session_manager.create_session(config)
    
    def terminate_session(self, session_id: str) -> None:
        """Terminate a simulator session."""
        return self.session_manager.terminate_session(session_id)
    
    def list_sessions(self) -> List[str]:
        """List all active sessions."""
        return self.session_manager.list_sessions()
    
    def get_session_info(self, session_id: str) -> Dict[str, Any]:
        """Get detailed session information."""
        return self.session_manager.get_session_info(session_id)
    
    # Simulator Management
    def list_simulators(self, refresh_cache: bool = False) -> List:
        """List all available simulators."""
        return self.simulator_manager.list_available_simulators(refresh_cache)
    
    def list_booted_simulators(self) -> List:
        """List currently booted simulators."""
        return self.simulator_manager.list_booted_simulators()
    
    def boot_simulator(self, udid: str, timeout: int = 30) -> None:
        """Boot a simulator by UDID."""
        return self.simulator_manager.boot_simulator_by_udid(udid, timeout)
    
    def shutdown_simulator(self, session_id: str) -> None:
        """Shutdown simulator by session ID."""
        udid = self.session_manager.get_udid_from_session(session_id)
        return self.simulator_manager.shutdown_simulator_by_udid(udid)
    
    def shutdown_simulator_by_udid(self, udid: str) -> None:
        """Shutdown simulator by UDID."""
        return self.simulator_manager.shutdown_simulator_by_udid(udid)
    
    def erase_simulator(self, udid: str) -> None:
        """Erase simulator data."""
        return self.simulator_manager.erase_simulator(udid)
    
    # App Management
    def install_app(self, session_id: str, app_path: str):
        """Install an app."""
        udid = self.session_manager.get_udid_from_session(session_id)
        return self.app_manager.install_app(udid, app_path)
    
    def uninstall_app(self, session_id: str, bundle_id: str) -> None:
        """Uninstall an app."""
        udid = self.session_manager.get_udid_from_session(session_id)
        return self.app_manager.uninstall_app(udid, bundle_id)
    
    def launch_app(self, session_id: str, bundle_id: str, arguments: Optional[List[str]] = None) -> None:
        """Launch an app."""
        udid = self.session_manager.get_udid_from_session(session_id)
        return self.app_manager.launch_app(udid, bundle_id, arguments)
    
    def terminate_app(self, session_id: str, bundle_id: str) -> None:
        """Terminate an app."""
        udid = self.session_manager.get_udid_from_session(session_id)
        return self.app_manager.terminate_app(udid, bundle_id)
    
    def list_apps(self, session_id: str, user_apps_only: bool = True) -> List:
        """List installed apps."""
        udid = self.session_manager.get_udid_from_session(session_id)
        return self.app_manager.list_apps(udid, user_apps_only)
    
    # UI Interactions
    def tap(self, session_id: str, x: int, y: int) -> None:
        """Tap at coordinates."""
        udid = self.session_manager.get_udid_from_session(session_id)
        return self.ui_controller.tap(udid, x, y)
    
    def swipe(self, session_id: str, start_x: int, start_y: int, end_x: int, end_y: int, duration: int = 100) -> None:
        """Perform swipe gesture."""
        udid = self.session_manager.get_udid_from_session(session_id)
        return self.ui_controller.swipe(udid, start_x, start_y, end_x, end_y, duration)
    
    def input_text(self, session_id: str, text: str) -> None:
        """Input text."""
        udid = self.session_manager.get_udid_from_session(session_id)
        return self.ui_controller.input_text(udid, text)
    
    def press_button(self, session_id: str, button: str, duration: Optional[int] = None) -> None:
        """Press hardware button."""
        udid = self.session_manager.get_udid_from_session(session_id)
        return self.ui_controller.press_button(udid, button, duration)
    
    def take_screenshot(self, session_id: str, output_path: Optional[str] = None):
        """Take screenshot."""
        udid = self.session_manager.get_udid_from_session(session_id)
        return self.ui_controller.take_screenshot(udid, output_path)
    
    # Media and Location
    def add_media(self, session_id: str, media_paths: List[str]) -> None:
        """Add media to photo library."""
        udid = self.session_manager.get_udid_from_session(session_id)
        return self.media_manager.add_media(udid, media_paths)
    
    def set_location(self, session_id: str, latitude: float, longitude: float) -> None:
        """Set simulator location."""
        udid = self.session_manager.get_udid_from_session(session_id)
        return self.media_manager.set_location(udid, latitude, longitude)
    
    def set_location_by_name(self, session_id: str, location_name: str) -> None:
        """Set location by place name."""
        udid = self.session_manager.get_udid_from_session(session_id)
        return self.media_manager.set_location_by_name(udid, location_name)
    
    # Logging and Debugging
    def get_system_logs(self, session_id: str, bundle_id: Optional[str] = None, limit: Optional[int] = None) -> str:
        """Get system logs."""
        udid = self.session_manager.get_udid_from_session(session_id)
        return self.logger_manager.get_system_logs(udid, bundle=bundle_id, limit=limit)
    
    def get_app_logs(self, session_id: str, bundle_id: str) -> str:
        """Get app-specific logs."""
        udid = self.session_manager.get_udid_from_session(session_id)
        return self.logger_manager.get_app_logs(udid, bundle_id)
    
    def list_crash_logs(self, session_id: str, bundle_id: Optional[str] = None) -> List:
        """List crash logs."""
        udid = self.session_manager.get_udid_from_session(session_id)
        return self.logger_manager.list_crash_logs(udid, bundle_id=bundle_id)
    
    def export_logs(self, session_id: str, output_dir: str, bundle_id: Optional[str] = None) -> List[str]:
        """Export logs to files."""
        udid = self.session_manager.get_udid_from_session(session_id)
        return self.logger_manager.export_logs(udid, output_dir, bundle_id=bundle_id)
    
    # Utilities
    def open_url(self, session_id: str, url: str) -> None:
        """Open URL in simulator."""
        udid = self.session_manager.get_udid_from_session(session_id)
        return self.utilities_manager.open_url(udid, url)
    
    def clear_keychain(self, session_id: str) -> None:
        """Clear simulator keychain."""
        udid = self.session_manager.get_udid_from_session(session_id)
        return self.utilities_manager.clear_keychain(udid)
    
    def approve_permissions(self, session_id: str, bundle_id: str, permissions: List[str]) -> None:
        """Approve app permissions."""
        udid = self.session_manager.get_udid_from_session(session_id)
        return self.utilities_manager.approve_permissions(udid, bundle_id, permissions)
    
    def focus_simulator(self, session_id: str) -> None:
        """Focus simulator window."""
        udid = self.session_manager.get_udid_from_session(session_id)
        return self.utilities_manager.focus_simulator(udid)
    
    def get_device_info(self, session_id: str) -> Dict[str, Any]:
        """Get detailed device information."""
        udid = self.session_manager.get_udid_from_session(session_id)
        return self.utilities_manager.get_device_info(udid)
    
    # Convenience Methods
    def quick_setup(self, device_name: str = "iPhone 15") -> str:
        """Quick setup: create session and boot simulator."""
        session_id = self.create_session(device_name=device_name)
        print(f"✅ Created session: {session_id}")
        return session_id
    
    def install_and_launch(self, session_id: str, app_path: str, launch_immediately: bool = True):
        """Install an app and optionally launch it."""
        app_info = self.install_app(session_id, app_path)
        print(f"✅ Installed: {app_info.name}")
        
        if launch_immediately:
            self.launch_app(session_id, app_info.bundle_id)
            print(f"✅ Launched: {app_info.name}")
        
        return app_info
    
    def automation_session(self, device_name: str = "iPhone 15") -> Dict[str, Any]:
        """Create a session optimized for automation."""
        session_id = self.create_session(device_name=device_name)
        udid = self.session_manager.get_udid_from_session(session_id)
        
        # Focus the simulator
        self.focus_simulator(session_id)
        
        # Clear keychain for fresh state
        self.clear_keychain(session_id)
        
        return {
            "session_id": session_id,
            "udid": udid,
            "device_name": device_name,
            "ready_for_automation": True
        }
    
    def cleanup_all_sessions(self) -> None:
        """Clean up all active sessions."""
        sessions = self.list_sessions()
        for session_id in sessions:
            try:
                self.terminate_session(session_id)
                print(f"✅ Terminated session: {session_id}")
            except Exception as e:
                print(f"❌ Failed to terminate {session_id}: {e}")
    
    def print_status(self) -> None:
        """Print current status of simulators and sessions."""
        print("\n📱 iOS Simulator Controller Status")
        print("=" * 50)
        
        # Sessions
        sessions = self.list_sessions()
        print(f"\nActive Sessions: {len(sessions)}")
        for session_id in sessions:
            try:
                info = self.get_session_info(session_id)
                print(f"  🔧 {session_id}")
                print(f"     UDID: {info.get('udid', 'Unknown')}")
                print(f"     Created: {info.get('created_at', 'Unknown')}")
            except Exception as e:
                print(f"  ❌ {session_id} (Error: {e})")
        
        # Simulators
        booted_sims = self.list_booted_simulators()
        print(f"\nBooted Simulators: {len(booted_sims)}")
        for sim in booted_sims:
            print(f"  🟢 {sim.name}")
            print(f"     UDID: {sim.udid}")
            print(f"     OS: {sim.os}")

def create_cli_parser():
    """Create command line interface parser."""
    parser = argparse.ArgumentParser(description='iOS Simulator Controller')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Session commands
    session_parser = subparsers.add_parser('session', help='Session management')
    session_subparsers = session_parser.add_subparsers(dest='session_command')
    
    create_session_parser = session_subparsers.add_parser('create', help='Create session')
    create_session_parser.add_argument('--device', help='Device name')
    create_session_parser.add_argument('--os', help='OS version')
    
    session_subparsers.add_parser('list', help='List sessions')
    
    terminate_session_parser = session_subparsers.add_parser('terminate', help='Terminate session')
    terminate_session_parser.add_argument('session_id', help='Session ID')
    
    # Simulator commands
    sim_parser = subparsers.add_parser('simulator', help='Simulator management')
    sim_subparsers = sim_parser.add_subparsers(dest='sim_command')
    
    sim_subparsers.add_parser('list', help='List simulators')
    sim_subparsers.add_parser('list-booted', help='List booted simulators')
    
    boot_parser = sim_subparsers.add_parser('boot', help='Boot simulator')
    boot_parser.add_argument('udid', help='Simulator UDID')
    
    shutdown_parser = sim_subparsers.add_parser('shutdown', help='Shutdown simulator')
    shutdown_parser.add_argument('udid', help='Simulator UDID')
    
    # App commands
    app_parser = subparsers.add_parser('app', help='App management')
    app_subparsers = app_parser.add_subparsers(dest='app_command')
    
    install_parser = app_subparsers.add_parser('install', help='Install app')
    install_parser.add_argument('session_id', help='Session ID')
    install_parser.add_argument('app_path', help='Path to app bundle')
    
    launch_parser = app_subparsers.add_parser('launch', help='Launch app')
    launch_parser.add_argument('session_id', help='Session ID')
    launch_parser.add_argument('bundle_id', help='App bundle ID')
    
    list_apps_parser = app_subparsers.add_parser('list', help='List apps')
    list_apps_parser.add_argument('session_id', help='Session ID')
    
    # UI commands
    ui_parser = subparsers.add_parser('ui', help='UI interactions')
    ui_subparsers = ui_parser.add_subparsers(dest='ui_command')
    
    tap_parser = ui_subparsers.add_parser('tap', help='Tap at coordinates')
    tap_parser.add_argument('session_id', help='Session ID')
    tap_parser.add_argument('x', type=int, help='X coordinate')
    tap_parser.add_argument('y', type=int, help='Y coordinate')
    
    swipe_parser = ui_subparsers.add_parser('swipe', help='Swipe gesture')
    swipe_parser.add_argument('session_id', help='Session ID')
    swipe_parser.add_argument('x1', type=int, help='Start X')
    swipe_parser.add_argument('y1', type=int, help='Start Y')
    swipe_parser.add_argument('x2', type=int, help='End X')
    swipe_parser.add_argument('y2', type=int, help='End Y')
    
    type_parser = ui_subparsers.add_parser('type', help='Type text')
    type_parser.add_argument('session_id', help='Session ID')
    type_parser.add_argument('text', help='Text to type')
    
    screenshot_parser = ui_subparsers.add_parser('screenshot', help='Take screenshot')
    screenshot_parser.add_argument('session_id', help='Session ID')
    screenshot_parser.add_argument('--output', help='Output file path')
    
    # Media commands
    media_parser = subparsers.add_parser('media', help='Media operations')
    media_subparsers = media_parser.add_subparsers(dest='media_command')
    
    add_media_parser = media_subparsers.add_parser('add', help='Add media files')
    add_media_parser.add_argument('session_id', help='Session ID')
    add_media_parser.add_argument('files', nargs='+', help='Media file paths')
    
    location_parser = media_subparsers.add_parser('location', help='Set location')
    location_parser.add_argument('session_id', help='Session ID')
    location_parser.add_argument('latitude', type=float, help='Latitude')
    location_parser.add_argument('longitude', type=float, help='Longitude')
    
    # Utility commands
    util_parser = subparsers.add_parser('util', help='Utility operations')
    util_subparsers = util_parser.add_subparsers(dest='util_command')
    
    url_parser = util_subparsers.add_parser('open-url', help='Open URL')
    url_parser.add_argument('session_id', help='Session ID')
    url_parser.add_argument('url', help='URL to open')
    
    focus_parser = util_subparsers.add_parser('focus', help='Focus simulator')
    focus_parser.add_argument('session_id', help='Session ID')
    
    # Status command
    subparsers.add_parser('status', help='Show status')
    
    return parser

def main():
    """Main CLI entry point."""
    controller = iOSSimulatorController()
    
    if len(sys.argv) == 1:
        print_usage()
        return
    
    parser = create_cli_parser()
    args = parser.parse_args()
    
    try:
        if args.command == 'session':
            handle_session_commands(controller, args)
        elif args.command == 'simulator':
            handle_simulator_commands(controller, args)
        elif args.command == 'app':
            handle_app_commands(controller, args)
        elif args.command == 'ui':
            handle_ui_commands(controller, args)
        elif args.command == 'media':
            handle_media_commands(controller, args)
        elif args.command == 'util':
            handle_util_commands(controller, args)
        elif args.command == 'status':
            controller.print_status()
        else:
            parser.print_help()
            
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

def handle_session_commands(controller, args):
    """Handle session-related commands."""
    if args.session_command == 'create':
        session_id = controller.create_session(
            device_name=args.device,
            platform_version=args.os
        )
        print(f"✅ Created session: {session_id}")
        
    elif args.session_command == 'list':
        sessions = controller.list_sessions()
        if sessions:
            print("Active sessions:")
            for session_id in sessions:
                info = controller.get_session_info(session_id)
                print(f"  📱 {session_id}")
                print(f"     UDID: {info.get('udid', 'Unknown')}")
        else:
            print("No active sessions")
            
    elif args.session_command == 'terminate':
        controller.terminate_session(args.session_id)
        print(f"✅ Terminated session: {args.session_id}")

def handle_simulator_commands(controller, args):
    """Handle simulator-related commands."""
    if args.sim_command == 'list':
        controller.simulator_manager.print_device_list()
        
    elif args.sim_command == 'list-booted':
        sims = controller.list_booted_simulators()
        if sims:
            print("Booted simulators:")
            for sim in sims:
                print(f"  🟢 {sim.name} ({sim.udid[:8]}...)")
        else:
            print("No booted simulators")
            
    elif args.sim_command == 'boot':
        controller.boot_simulator(args.udid)
        print(f"✅ Booted simulator: {args.udid}")
        
    elif args.sim_command == 'shutdown':
        controller.shutdown_simulator_by_udid(args.udid)
        print(f"✅ Shutdown simulator: {args.udid}")

def handle_app_commands(controller, args):
    """Handle app-related commands."""
    if args.app_command == 'install':
        app_info = controller.install_app(args.session_id, args.app_path)
        print(f"✅ Installed: {app_info.name} ({app_info.bundle_id})")
        
    elif args.app_command == 'launch':
        controller.launch_app(args.session_id, args.bundle_id)
        print(f"✅ Launched: {args.bundle_id}")
        
    elif args.app_command == 'list':
        apps = controller.list_apps(args.session_id)
        if apps:
            print("Installed apps:")
            for app in apps:
                print(f"  📱 {app.name} ({app.bundle_id})")
        else:
            print("No user apps installed")

def handle_ui_commands(controller, args):
    """Handle UI interaction commands."""
    if args.ui_command == 'tap':
        controller.tap(args.session_id, args.x, args.y)
        print(f"✅ Tapped at ({args.x}, {args.y})")
        
    elif args.ui_command == 'swipe':
        controller.swipe(args.session_id, args.x1, args.y1, args.x2, args.y2)
        print(f"✅ Swiped from ({args.x1}, {args.y1}) to ({args.x2}, {args.y2})")
        
    elif args.ui_command == 'type':
        controller.input_text(args.session_id, args.text)
        print(f"✅ Typed: {args.text}")
        
    elif args.ui_command == 'screenshot':
        path = controller.take_screenshot(args.session_id, args.output)
        print(f"✅ Screenshot saved: {path}")

def handle_media_commands(controller, args):
    """Handle media-related commands."""
    if args.media_command == 'add':
        controller.add_media(args.session_id, args.files)
        print(f"✅ Added {len(args.files)} media files")
        
    elif args.media_command == 'location':
        controller.set_location(args.session_id, args.latitude, args.longitude)
        print(f"✅ Location set to: {args.latitude}, {args.longitude}")

def handle_util_commands(controller, args):
    """Handle utility commands."""
    if args.util_command == 'open-url':
        controller.open_url(args.session_id, args.url)
        print(f"✅ Opened URL: {args.url}")
        
    elif args.util_command == 'focus':
        controller.focus_simulator(args.session_id)
        print("✅ Simulator focused")

def print_usage():
    """Print usage information."""
    print("""
🍎 iOS Simulator Controller - Modular Framework

QUICK START:
  python ios_simulator_main.py session create --device "iPhone 15"
  python ios_simulator_main.py status

SESSION MANAGEMENT:
  session create [--device NAME] [--os VERSION]    Create new session
  session list                                     List active sessions
  session terminate <session_id>                  Terminate session

SIMULATOR MANAGEMENT:
  simulator list                                   List all simulators
  simulator list-booted                           List booted simulators
  simulator boot <udid>                           Boot simulator
  simulator shutdown <udid>                       Shutdown simulator

APP MANAGEMENT:
  app install <session_id> <app_path>             Install app
  app launch <session_id> <bundle_id>             Launch app
  app list <session_id>                           List installed apps

UI INTERACTIONS:
  ui tap <session_id> <x> <y>                     Tap at coordinates
  ui swipe <session_id> <x1> <y1> <x2> <y2>       Swipe gesture
  ui type <session_id> <text>                     Type text
  ui screenshot <session_id> [--output PATH]      Take screenshot

MEDIA & LOCATION:
  media add <session_id> <file1> [file2...]       Add media files
  media location <session_id> <lat> <lng>         Set location

UTILITIES:
  util open-url <session_id> <url>                Open URL
  util focus <session_id>                         Focus simulator

STATUS:
  status                                           Show current status

EXAMPLES:
  # Quick automation setup
  python ios_simulator_main.py session create --device "iPhone 15"
  
  # Install and test an app
  python ios_simulator_main.py app install session_123 MyApp.app
  python ios_simulator_main.py app launch session_123 com.example.MyApp
  
  # UI automation
  python ios_simulator_main.py ui tap session_123 200 400
  python ios_simulator_main.py ui type session_123 "Hello World"
  python ios_simulator_main.py ui screenshot session_123 --output test.png

For detailed help on any command:
  python ios_simulator_main.py <command> --help
""")

if __name__ == "__main__":
    main()