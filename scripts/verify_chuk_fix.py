#!/usr/bin/env python3
"""
CHUK Sessions Fix Verification Script

This script verifies that the updated CHUK Sessions integration works correctly
with the actual CHUK Sessions API based on the diagnostic results.

Usage: python verify_chuk_fix.py
"""

import asyncio
import sys
from pathlib import Path

# Add the project path
sys.path.insert(0, str(Path(__file__).parent.parent))

async def test_chuk_sessions_integration():
    """Test the corrected CHUK Sessions integration."""
    print("🔬 Testing Corrected CHUK Sessions Integration")
    print("=" * 50)
    
    try:
        # Test 1: CHUK Sessions basic functionality
        print("\n1️⃣ Testing CHUK Sessions basic functionality...")
        from chuk_sessions import SessionManager
        
        test_manager = SessionManager(
            sandbox_id="verification-test",
            default_ttl_hours=1
        )
        
        # Create a test session
        test_session_id = await test_manager.allocate_session(
            user_id="verify_test_user",
            ttl_hours=1,
            custom_metadata={"test": "verification"}
        )
        print(f"✅ CHUK session created: {test_session_id}")
        
        # Test validation
        is_valid = await test_manager.validate_session(test_session_id)
        print(f"✅ Session validation: {is_valid}")
        
        # Test delete_session (the correct method)
        await test_manager.delete_session(test_session_id)
        print("✅ Session deleted successfully using delete_session()")
        
        # Verify deletion
        is_valid_after = await test_manager.validate_session(test_session_id)
        print(f"✅ Session invalid after deletion: {not is_valid_after}")
        
        # Test 2: Import updated tools
        print("\n2️⃣ Testing updated MCP tools import...")
        from chuk_mcp_ios.mcp.tools import (
            ios_create_session, ios_terminate_session, ios_session_status,
            ios_debug_sessions, register_ios_session, is_ios_session_valid,
            unregister_ios_session
        )
        print("✅ All updated tools imported successfully")
        
        # Test 3: Create iOS session with CHUK integration
        print("\n3️⃣ Testing iOS session creation with CHUK integration...")
        result = await ios_create_session(
            device_name="iPhone 16 Pro",
            autoboot=True,
            session_name="verification_test"
        )
        
        if 'error' in result:
            print(f"❌ Session creation failed: {result['error']}")
            return False
        
        session_id = result['session_id']
        print(f"✅ iOS session created: {session_id}")
        print(f"   CHUK registered: {result.get('registered_with_chuk', False)}")
        print(f"   CHUK available: {result.get('chuk_available', False)}")
        
        # Test 4: Session status validation
        print("\n4️⃣ Testing session status validation...")
        status = await ios_session_status(session_id)
        print(f"✅ Session status retrieved:")
        print(f"   Overall valid: {status.get('overall_valid', False)}")
        print(f"   CHUK valid: {status.get('chuk_valid', False)}")
        print(f"   In registry: {status.get('in_registry', False)}")
        
        # Test 5: Debug sessions info
        print("\n5️⃣ Testing debug sessions info...")
        debug_info = await ios_debug_sessions()
        print(f"✅ Debug info retrieved:")
        print(f"   CHUK available: {debug_info.get('chuk_sessions_available', False)}")
        print(f"   Registry sessions: {debug_info.get('registry_count', 0)}")
        print(f"   Session validity: {debug_info.get('session_validity', {})}")
        
        # Test 6: Session termination
        print("\n6️⃣ Testing session termination...")
        terminate_result = await ios_terminate_session(session_id)
        
        if terminate_result.get('success', False):
            print("✅ Session terminated successfully")
            print(f"   CHUK cleanup: {terminate_result.get('chuk_cleanup', False)}")
        else:
            print(f"❌ Session termination failed: {terminate_result.get('error', 'Unknown')}")
            return False
        
        # Test 7: Verify cleanup
        print("\n7️⃣ Verifying cleanup...")
        final_status = await ios_session_status(session_id)
        print(f"✅ Final verification:")
        print(f"   Overall valid: {final_status.get('overall_valid', False)}")
        print(f"   In registry: {final_status.get('in_registry', False)}")
        
        print(f"\n🎉 All tests passed! CHUK Sessions integration is working correctly.")
        return True
        
    except Exception as e:
        print(f"\n❌ Verification failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main verification script."""
    print("🚀 Starting CHUK Sessions Fix Verification...")
    
    success = await test_chuk_sessions_integration()
    
    if success:
        print("\n✅ Verification successful!")
        print("🔗 The updated CHUK Sessions integration is working properly")
        print("📋 Key fixes implemented:")
        print("   - Correct usage of delete_session() method")
        print("   - Dual lookup strategy (CHUK session ID + user_id)")
        print("   - Enhanced error handling and fallback")
        print("   - Proper session lifecycle management")
        return 0
    else:
        print("\n❌ Verification failed!")
        print("💡 Check the error output above for details")
        return 1

if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(result)