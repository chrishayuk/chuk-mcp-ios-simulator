#!/usr/bin/env python3
# src/chuk_mcp_ios/main.py
"""
Main dispatcher for chuk-mcp-ios

Provides unified entry point with subcommands:
- chuk-mcp-ios cli [args]   -> CLI interface
- chuk-mcp-ios mcp [args]   -> MCP server
- chuk-mcp-ios --help       -> Show help

This allows clean uvx usage:
  uvx chuk-mcp-ios cli status
  uvx chuk-mcp-ios mcp
"""

import sys
import argparse
from pathlib import Path

def show_banner():
    """Show application banner."""
    print("🍎 iOS Device Control")
    print("=" * 40)
    print("Comprehensive iOS automation and device control")
    print()

def show_main_help():
    """Show main help message."""
    print("Usage: chuk-mcp-ios <command> [args...]")
    print()
    print("Commands:")
    print("  cli    - Interactive command-line interface")
    print("  mcp    - Start MCP (Model Context Protocol) server")
    print("  help   - Show this help message")
    print()
    print("Examples:")
    print("  chuk-mcp-ios cli status")
    print("  chuk-mcp-ios cli device list")
    print("  chuk-mcp-ios cli quick-start")
    print("  chuk-mcp-ios mcp")
    print()
    print("Quick Start:")
    print("  uvx chuk-mcp-ios cli status      # Check system")
    print("  uvx chuk-mcp-ios cli quick-start # Interactive setup")
    print("  uvx chuk-mcp-ios mcp             # Start MCP server")
    print()
    print("For command-specific help:")
    print("  chuk-mcp-ios cli --help")
    print("  chuk-mcp-ios mcp --help")

def main():
    """Main entry point with command dispatching."""
    # Handle no arguments
    if len(sys.argv) < 2:
        show_banner()
        show_main_help()
        return
    
    command = sys.argv[1]
    
    # Handle help
    if command in ['help', '--help', '-h']:
        show_banner()
        show_main_help()
        return
    
    # Handle version
    if command in ['--version', '-v']:
        try:
            from importlib.metadata import version
            print(f"chuk-mcp-ios {version('chuk-mcp-ios')}")
        except:
            print("chuk-mcp-ios (development version)")
        return
    
    # Remove the command from sys.argv for subcommand processing
    sys.argv = [sys.argv[0]] + sys.argv[2:]
    
    # Dispatch to appropriate module
    if command == 'cli':
        from .cli.main import main as cli_main
        cli_main()
    elif command == 'mcp':
        from .mcp.main import main as mcp_main
        mcp_main()
    else:
        print(f"❌ Unknown command: {command}")
        print()
        print("Available commands: cli, mcp")
        print("Run 'chuk-mcp-ios help' for more information")
        sys.exit(1)

if __name__ == "__main__":
    main()