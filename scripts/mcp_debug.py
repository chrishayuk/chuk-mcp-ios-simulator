#!/usr/bin/env python3
"""
MCP Runtime Session Debug Script - Updated for Singleton Manager

This script helps debug session validation issues in the MCP runtime environment,
specifically for the scenario where sessions are created but then reported as invalid.

Usage: python mcp_session_debug.py
"""

import asyncio
import time
import sys
from pathlib import Path

# Add the project path
sys.path.insert(0, str(Path(__file__).parent.parent))

async def debug_mcp_session_issue():
    """Debug the MCP session validation issue."""
    print("🔬 Debugging MCP Session Validation Issue - Singleton Manager")
    print("=" * 60)
    
    try:
        # Import the tools (updated imports)
        from chuk_mcp_ios.mcp.tools import (
            ios_create_automation_session, ios_open_url, ios_session_status,
            ios_debug_session_validation, ios_open_url_debug,
            simple_session_validation, get_unified_session_manager,
            _ios_session_registry
        )
        
        print("✅ Tools imported successfully")
        
        # Step 1: Create automation session
        print("\n1️⃣ Creating automation session...")
        result = await ios_create_automation_session()
        
        if 'error' in result:
            print(f"❌ Session creation failed: {result['error']}")
            return False
        
        session_id = result['session_id']
        print(f"✅ Session created: {session_id}")
        print(f"   Device: {result['device_name']}")
        print(f"   State: {result['state']}")
        
        # Step 2: Check singleton manager state
        print(f"\n2️⃣ Checking singleton manager state...")
        unified_manager = get_unified_session_manager()
        print(f"📋 Singleton manager ID: {id(unified_manager)}")
        
        try:
            all_sessions = unified_manager.sessions if hasattr(unified_manager, 'sessions') else {}
            print(f"📋 Sessions in singleton: {list(all_sessions.keys())}")
            print(f"📋 Target session in singleton: {session_id in all_sessions}")
        except Exception as e:
            print(f"❌ Error checking singleton sessions: {e}")
        
        # Step 3: Test simple validation
        print(f"\n3️⃣ Testing simple session validation...")
        is_valid_simple = await simple_session_validation(session_id)
        print(f"✅ Simple validation result: {is_valid_simple}")
        
        # Step 4: Deep debug with new debug tool
        print(f"\n4️⃣ Deep session debugging...")
        debug_result = await ios_debug_session_validation(session_id)
        print(f"Debug results:")
        for key, value in debug_result.items():
            if key != 'validations':
                print(f"   {key}: {value}")
        
        if 'validations' in debug_result:
            print("   Validation methods:")
            for method, result in debug_result['validations'].items():
                print(f"     {method}: {result}")
        
        # Step 5: Test the regular ios_open_url (expected to fail)
        print(f"\n5️⃣ Testing regular ios_open_url (expected to fail)...")
        try:
            url_result = await ios_open_url(session_id, "https://www.boots.com")
            
            if url_result.get('success', False):
                print("✅ ios_open_url succeeded!")
            else:
                print(f"❌ ios_open_url failed: {url_result.get('error', 'Unknown error')}")
                
        except Exception as e:
            print(f"❌ Exception in ios_open_url: {e}")
        
        # Step 6: Test the debug version (bypasses validation)
        print(f"\n6️⃣ Testing debug ios_open_url (bypasses validation)...")
        try:
            debug_url_result = await ios_open_url_debug(session_id, "https://www.boots.com")
            
            if debug_url_result.get('success', False):
                print("✅ ios_open_url_debug succeeded!")
            else:
                print(f"❌ ios_open_url_debug failed: {debug_url_result.get('error', 'Unknown error')}")
                
        except Exception as e:
            print(f"❌ Exception in ios_open_url_debug: {e}")
            import traceback
            traceback.print_exc()
        
        # Step 7: Check CHUK registry state
        print(f"\n7️⃣ Checking CHUK registry state...")
        print(f"📋 Sessions in CHUK registry: {list(_ios_session_registry.keys())}")
        print(f"📋 Target session in registry: {session_id in _ios_session_registry}")
        
        # Step 8: Test session status
        print(f"\n8️⃣ Testing session status...")
        status = await ios_session_status(session_id)
        print(f"Session Status:")
        print(f"   Overall valid: {status.get('overall_valid', 'unknown')}")
        print(f"   In unified manager: {status.get('in_unified_manager', 'unknown')}")
        print(f"   CHUK available: {status.get('chuk_sessions_available', 'unknown')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Debug script failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_session_persistence():
    """Test session persistence with singleton manager."""
    print("\n🔄 Testing Session Persistence with Singleton Manager")
    print("=" * 50)
    
    try:
        from chuk_mcp_ios.mcp.tools import (
            ios_create_automation_session, simple_session_validation,
            ios_session_status, get_unified_session_manager
        )
        
        # Create session
        result = await ios_create_automation_session()
        if 'error' in result:
            print(f"❌ Session creation failed: {result['error']}")
            return False
        
        session_id = result['session_id']
        print(f"✅ Created session: {session_id}")
        
        # Get singleton manager for checking
        unified_manager = get_unified_session_manager()
        print(f"📋 Singleton manager ID: {id(unified_manager)}")
        
        # Test multiple validation calls with delays
        for i in range(5):
            print(f"\nValidation attempt {i+1}:")
            
            # Wait a bit
            if i > 0:
                await asyncio.sleep(1)
            
            # Check singleton manager directly
            try:
                in_singleton = session_id in unified_manager.sessions
                print(f"   In singleton manager: {in_singleton}")
            except Exception as e:
                print(f"   Singleton check error: {e}")
            
            # Check simple validation
            is_valid = await simple_session_validation(session_id)
            print(f"   simple_session_validation: {is_valid}")
            
            # Check status
            status = await ios_session_status(session_id)
            print(f"   overall_valid: {status.get('overall_valid', 'unknown')}")
            print(f"   in_unified_manager: {status.get('in_unified_manager', 'unknown')}")
            
            if not is_valid:
                print(f"❌ Session became invalid at attempt {i+1}")
                break
        
        return True
        
    except Exception as e:
        print(f"❌ Persistence test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_direct_manager_interaction():
    """Test direct interaction with the singleton manager."""
    print("\n🔧 Testing Direct Singleton Manager Interaction")
    print("=" * 45)
    
    try:
        from chuk_mcp_ios.mcp.tools import get_unified_session_manager, run_sync
        
        # Get the singleton manager
        unified_manager = get_unified_session_manager()
        print(f"📋 Got singleton manager: {id(unified_manager)}")
        
        # List all sessions
        try:
            all_sessions = await run_sync(unified_manager.list_sessions)
            print(f"📋 All sessions in manager: {all_sessions}")
        except Exception as e:
            print(f"❌ Error listing sessions: {e}")
        
        # Check sessions attribute directly
        try:
            if hasattr(unified_manager, 'sessions'):
                direct_sessions = unified_manager.sessions
                print(f"📋 Direct sessions access: {list(direct_sessions.keys()) if direct_sessions else 'Empty'}")
            else:
                print("❌ Manager has no sessions attribute")
        except Exception as e:
            print(f"❌ Error accessing sessions directly: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Direct manager test failed: {e}")
        return False

async def main():
    """Main diagnostic entry point."""
    print("🚀 Starting Enhanced MCP Session Debug...")
    
    success1 = await debug_mcp_session_issue()
    success2 = await test_session_persistence()
    success3 = await test_direct_manager_interaction()
    
    if success1 and success2 and success3:
        print("\n✅ Debug completed successfully!")
        print("\n💡 ANALYSIS:")
        print("   - Sessions are being created and managed by singleton")
        print("   - Check if MCP runtime is doing its own validation")
        print("   - Look for validation happening before our tools are called")
        print("   - Check if there's a mismatch between runtime and tool validation")
        return 0
    else:
        print("\n❌ Debug found issues!")
        print("\n🔍 TROUBLESHOOTING:")
        print("   1. Check if MCP runtime validates sessions before calling tools")
        print("   2. Verify the singleton manager is working correctly")
        print("   3. Look for session ID format or timing issues")
        print("   4. Consider if the error is from runtime, not our validation")
        return 1

if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(result)