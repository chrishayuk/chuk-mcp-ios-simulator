#!/usr/bin/env python3
"""
CHUK Sessions API Diagnostic and Fix

This script will help us understand the correct CHUK Sessions API usage
and fix the integration issues.
"""

import asyncio
import os
from chuk_sessions import SessionManager

async def diagnose_chuk_sessions_api():
    """Diagnose the CHUK Sessions API to understand correct usage."""
    
    print("🔍 CHUK Sessions API Diagnostic")
    print("=" * 50)
    
    # Initialize session manager
    session_manager = SessionManager(
        sandbox_id="test-diagnostic",
        default_ttl_hours=1
    )
    
    # Check available methods
    print("\n📋 Available SessionManager methods:")
    methods = [method for method in dir(session_manager) if not method.startswith('_')]
    for method in sorted(methods):
        print(f"  - {method}")
    
    # Test session lifecycle
    print("\n🧪 Testing session lifecycle...")
    
    try:
        # 1. Create session
        print("\n1️⃣ Creating session...")
        session_id = await session_manager.allocate_session(
            user_id="test_user_123",
            ttl_hours=1,
            custom_metadata={
                'test': 'diagnostic',
                'device_type': 'simulator'
            }
        )
        print(f"✅ Session created: {session_id}")
        
        # 2. Validate session
        print("\n2️⃣ Validating session...")
        is_valid = await session_manager.validate_session(session_id)
        print(f"✅ Session valid: {is_valid}")
        
        # 3. Get session info
        print("\n3️⃣ Getting session info...")
        try:
            info = await session_manager.get_session_info(session_id)
            print(f"✅ Session info: {info}")
        except Exception as e:
            print(f"❌ Failed to get session info: {e}")
        
        # 4. Update session metadata
        print("\n4️⃣ Updating session metadata...")
        try:
            await session_manager.update_session_metadata(session_id, {
                'test': 'updated',
                'last_activity': 'now'
            })
            print(f"✅ Metadata updated")
        except Exception as e:
            print(f"❌ Failed to update metadata: {e}")
        
        # 5. Test different termination methods
        print("\n5️⃣ Testing session termination methods...")
        
        termination_methods = [
            'end_session',
            'destroy_session', 
            'delete_session',
            'remove_session',
            'invalidate_session',
            'terminate_session',
            'close_session'
        ]
        
        for method_name in termination_methods:
            if hasattr(session_manager, method_name):
                print(f"✅ Found method: {method_name}")
                try:
                    method = getattr(session_manager, method_name)
                    # Don't actually call it yet - just confirm it exists
                    print(f"   Method signature: {method}")
                except Exception as e:
                    print(f"   Error accessing method: {e}")
            else:
                print(f"❌ Method not found: {method_name}")
        
        # 6. Actually terminate the session
        print("\n6️⃣ Terminating session...")
        
        # Try the most likely candidates
        if hasattr(session_manager, 'destroy_session'):
            try:
                await session_manager.destroy_session(session_id)
                print("✅ Successfully terminated with destroy_session")
            except Exception as e:
                print(f"❌ destroy_session failed: {e}")
        elif hasattr(session_manager, 'end_session'):
            try:
                await session_manager.end_session(session_id)
                print("✅ Successfully terminated with end_session")
            except Exception as e:
                print(f"❌ end_session failed: {e}")
        else:
            print("❌ No termination method found")
        
        # 7. Verify termination
        print("\n7️⃣ Verifying termination...")
        is_valid_after = await session_manager.validate_session(session_id)
        print(f"Session valid after termination: {is_valid_after}")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

# Fixed CHUK Sessions integration for tools.py
CHUK_SESSIONS_INTEGRATION_FIX = '''
# ═══════════════════════════════════════════════════════════════════════════
# FIXED CHUK SESSIONS INTEGRATION
# ═══════════════════════════════════════════════════════════════════════════

import os
from chuk_sessions import SessionManager

# Initialize CHUK Sessions manager with memory provider for testing
os.environ.setdefault('SESSION_PROVIDER', 'memory')

ios_session_manager = SessionManager(
    sandbox_id="ios-device-control",
    default_ttl_hours=24
)

async def register_ios_session(session_id: str, device_info: Dict[str, Any], ios_session_manager_instance):
    """Register an iOS session using CHUK Sessions for persistence."""
    try:
        # Use session_id as user_id in CHUK Sessions
        allocated_session_id = await ios_session_manager.allocate_session(
            user_id=session_id,  # This creates the session with the ID we want
            ttl_hours=24,
            custom_metadata={
                'device_udid': device_info.get('device_udid', ''),
                'device_name': device_info.get('device_name', ''),
                'device_type': device_info.get('device_type', ''),
                'platform_version': device_info.get('os_version', ''),
                'state': device_info.get('current_state', ''),
                'manager_id': str(id(ios_session_manager_instance)),
                'created_at': datetime.now().isoformat(),
                'session_type': 'ios_device'
            }
        )
        
        print(f"🔐 iOS session registered with CHUK Sessions: {session_id}")
        print(f"   CHUK session ID: {allocated_session_id}")
        return True
    except Exception as e:
        print(f"❌ Failed to register session {session_id}: {e}")
        import traceback
        traceback.print_exc()
        return False

async def is_ios_session_valid(session_id: str) -> bool:
    """Check if iOS session is valid using CHUK Sessions."""
    try:
        # CHUK Sessions might use the allocated session ID, not our session ID
        # Try both approaches
        
        # Approach 1: Check if session_id is the user_id
        is_valid = await ios_session_manager.validate_session(session_id)
        if is_valid:
            return True
        
        # Approach 2: Debug what sessions exist
        print(f"🔍 Debug: Checking session {session_id}")
        
        # If validation fails, let's see what we can learn
        try:
            info = await ios_session_manager.get_session_info(session_id)
            print(f"🔍 Found session info: {info}")
            return True
        except Exception as e:
            print(f"🔍 No session info found: {e}")
        
        return False
    except Exception as e:
        print(f"❌ Error validating session {session_id}: {e}")
        return False

async def unregister_ios_session(session_id: str):
    """Unregister iOS session from CHUK Sessions."""
    try:
        # Try multiple termination methods
        methods_to_try = ['destroy_session', 'end_session', 'delete_session']
        
        for method_name in methods_to_try:
            if hasattr(ios_session_manager, method_name):
                try:
                    method = getattr(ios_session_manager, method_name)
                    await method(session_id)
                    print(f"🗑️ iOS session unregistered from CHUK Sessions using {method_name}: {session_id}")
                    return
                except Exception as e:
                    print(f"❌ {method_name} failed: {e}")
        
        print(f"❌ Could not unregister session {session_id} - no working termination method found")
        
    except Exception as e:
        print(f"❌ Failed to unregister session {session_id}: {e}")
'''

if __name__ == "__main__":
    print("🚀 Running CHUK Sessions API Diagnostic...")
    asyncio.run(diagnose_chuk_sessions_api())
    
    print("\n" + "="*60)
    print("💡 INTEGRATION FIX:")
    print("Replace the CHUK Sessions functions in your tools.py with:")
    print(CHUK_SESSIONS_INTEGRATION_FIX)