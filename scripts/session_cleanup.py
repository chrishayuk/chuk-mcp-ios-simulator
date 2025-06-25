#!/usr/bin/env python3
"""
Session Cleanup Script for iOS MCP Tool

This script cleans up accumulated sessions and provides better session management.
"""

import asyncio
import shutil
from pathlib import Path
from datetime import datetime, timedelta

async def cleanup_sessions():
    """Clean up old and invalid sessions."""
    print("🧹 iOS Session Cleanup")
    print("=" * 50)
    
    # Session directory
    session_dir = Path.home() / ".ios-device-control" / "sessions"
    
    if not session_dir.exists():
        print("No session directory found")
        return
    
    # Count sessions
    session_files = list(session_dir.glob("*.json"))
    print(f"Found {len(session_files)} session files")
    
    # Option 1: Clear ALL sessions (nuclear option)
    print("\nOptions:")
    print("1. Clear ALL sessions (recommended for fresh start)")
    print("2. Clear sessions older than 24 hours")
    print("3. Keep only last 5 sessions")
    print("4. Cancel")
    
    choice = input("\nChoose option (1-4): ")
    
    if choice == "1":
        # Clear all sessions
        backup_dir = session_dir.parent / f"sessions_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        print(f"\nBacking up to: {backup_dir}")
        shutil.move(str(session_dir), str(backup_dir))
        session_dir.mkdir(parents=True, exist_ok=True)
        print("✅ All sessions cleared!")
        
    elif choice == "2":
        # Clear old sessions
        import json
        removed = 0
        cutoff_time = datetime.now() - timedelta(hours=24)
        
        for session_file in session_files:
            try:
                with open(session_file, 'r') as f:
                    data = json.load(f)
                created_at = datetime.fromisoformat(data['created_at'])
                if created_at < cutoff_time:
                    session_file.unlink()
                    removed += 1
            except Exception as e:
                print(f"Error processing {session_file.name}: {e}")
        
        print(f"✅ Removed {removed} old sessions")
        
    elif choice == "3":
        # Keep only recent sessions
        import json
        sessions_with_time = []
        
        for session_file in session_files:
            try:
                with open(session_file, 'r') as f:
                    data = json.load(f)
                created_at = datetime.fromisoformat(data['created_at'])
                sessions_with_time.append((created_at, session_file))
            except Exception as e:
                print(f"Error reading {session_file.name}: {e}")
                # Remove corrupted files
                session_file.unlink()
        
        # Sort by creation time and keep only the 5 most recent
        sessions_with_time.sort(key=lambda x: x[0], reverse=True)
        
        for i, (_, session_file) in enumerate(sessions_with_time):
            if i >= 5:  # Remove all but the 5 most recent
                session_file.unlink()
        
        removed = len(session_files) - min(5, len(session_files))
        print(f"✅ Removed {removed} old sessions, kept 5 most recent")
        
    else:
        print("Cancelled")
        return
    
    # Show remaining sessions
    remaining = list(session_dir.glob("*.json"))
    print(f"\nRemaining sessions: {len(remaining)}")
    
    if remaining and len(remaining) < 10:
        print("\nRemaining session files:")
        for f in remaining:
            print(f"  - {f.name}")

async def test_clean_session():
    """Test creating a session after cleanup."""
    print("\n🧪 Testing Clean Session Creation")
    print("=" * 40)
    
    try:
        from chuk_mcp_ios.mcp.tools import ios_create_automation_session, ios_open_url, ios_terminate_session
        
        # Create a fresh session
        print("Creating fresh session...")
        result = await ios_create_automation_session()
        
        if 'error' in result:
            print(f"❌ Failed: {result['error']}")
            return
        
        session_id = result['session_id']
        print(f"✅ Created: {session_id}")
        
        # Test it
        print("\nTesting session...")
        url_result = await ios_open_url(session_id, "https://www.apple.com")
        
        if url_result.get('success'):
            print("✅ Session works!")
        else:
            print(f"❌ Failed: {url_result.get('error')}")
        
        # Clean up
        print("\nCleaning up...")
        await ios_terminate_session(session_id)
        print("✅ Session terminated")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

async def main():
    """Main entry point."""
    await cleanup_sessions()
    
    # Ask if user wants to test
    test = input("\nTest session creation? (y/n): ")
    if test.lower() == 'y':
        await test_clean_session()
    
    print("\n✨ Done!")

if __name__ == "__main__":
    asyncio.run(main())