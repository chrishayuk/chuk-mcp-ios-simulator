#!/usr/bin/env python3
"""
End-to-End Session Debug Script - UPDATED for Fixed CHUK Sessions Integration

This script thoroughly tests and debugs the iOS session management system
with the corrected CHUK Sessions integration.

Usage: python session_debug.py
"""

import asyncio
import time
import traceback
import sys
from pathlib import Path
from typing import Dict, Any, Optional

# Add the project path
sys.path.insert(0, str(Path(__file__).parent.parent))

class SessionDebugger:
    """Comprehensive session debugging tool with enhanced CHUK Sessions testing."""
    
    def __init__(self):
        self.debug_log = []
        self.session_id = None
        self.session_manager = None
        self.start_time = time.time()
        self.test_sessions = []  # Track all created sessions for cleanup
    
    def log(self, message: str, level: str = "INFO"):
        """Log debug messages with timestamp."""
        timestamp = time.strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {level}: {message}"
        print(log_entry)
        self.debug_log.append(log_entry)
    
    def log_error(self, message: str, exception: Exception = None):
        """Log error with full traceback."""
        self.log(f"❌ {message}", "ERROR")
        if exception:
            tb = traceback.format_exc()
            self.log(f"Exception details:\n{tb}", "ERROR")
    
    def log_success(self, message: str):
        """Log success message."""
        self.log(f"✅ {message}", "SUCCESS")
    
    def log_warning(self, message: str):
        """Log warning message."""
        self.log(f"⚠️ {message}", "WARNING")
    
    async def run_sync(self, func, *args, **kwargs):
        """Run sync function in thread pool with error handling."""
        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, func, *args, **kwargs)
            return result
        except Exception as e:
            self.log_error(f"run_sync failed for {func.__name__}", e)
            raise
    
    async def test_1_imports(self):
        """Test 1: Import all required modules."""
        self.log("\n🧪 TEST 1: Testing imports...", "INFO")
        
        try:
            # Test core imports
            from chuk_mcp_ios.core.device_manager import UnifiedDeviceManager
            from chuk_mcp_ios.core.session_manager import UnifiedSessionManager, SessionConfig
            from chuk_mcp_ios.core.utilities_manager import UnifiedUtilitiesManager
            from chuk_mcp_ios.core.base import DeviceType
            self.log_success("All core modules imported successfully")
            
            # Test CHUK Sessions import
            from chuk_sessions import SessionManager
            self.log_success("CHUK Sessions imported successfully")
            
            # Test updated MCP tools imports
            from chuk_mcp_ios.mcp.tools import (
                ios_create_session, ios_open_url, ios_list_sessions,
                ios_terminate_session, ios_session_status, ios_debug_sessions,
                get_unified_session_manager, run_sync, 
                is_ios_session_valid, get_manager_for_session
            )
            self.log_success("All updated MCP tools imported successfully")
            
            return True
            
        except Exception as e:
            self.log_error("Import failed", e)
            return False
    
    async def test_2_device_discovery(self):
        """Test 2: Device discovery and availability."""
        self.log("\n🧪 TEST 2: Testing device discovery...", "INFO")
        
        try:
            from chuk_mcp_ios.core.device_manager import UnifiedDeviceManager
            
            device_manager = UnifiedDeviceManager()
            devices = await self.run_sync(device_manager.discover_all_devices)
            
            self.log(f"Found {len(devices)} total devices", "INFO")
            
            # Find iPhone simulators
            iphone_sims = [d for d in devices if 'iPhone' in d.name and d.device_type.value == 'simulator']
            self.log(f"Found {len(iphone_sims)} iPhone simulators", "INFO")
            
            if not iphone_sims:
                self.log_error("No iPhone simulators found!")
                return False
            
            # Check for working simulators
            working_sims = [d for d in iphone_sims if d.is_available or d.state.value in ['shutdown', 'booted']]
            self.log(f"Found {len(working_sims)} potentially working simulators", "INFO")
            
            for sim in working_sims[:3]:  # Show first 3
                self.log(f"  - {sim.name} ({sim.state.value}) - Available: {sim.is_available}", "INFO")
            
            return len(working_sims) > 0
            
        except Exception as e:
            self.log_error("Device discovery failed", e)
            return False
    
    async def test_3_chuk_sessions_availability(self):
        """Test 3: CHUK Sessions availability and functionality."""
        self.log("\n🧪 TEST 3: Testing CHUK Sessions availability...", "INFO")
        
        try:
            # Test CHUK Sessions basic functionality
            from chuk_sessions import SessionManager
            
            # Create a test CHUK Sessions manager
            test_manager = SessionManager(
                sandbox_id="test-debug",
                default_ttl_hours=1
            )
            
            # Test basic operations
            test_session_id = await test_manager.allocate_session(
                user_id="debug_test",
                ttl_hours=1,
                custom_metadata={"test": "debug"}
            )
            
            self.log_success(f"CHUK Sessions working - created session: {test_session_id}")
            
            # Test validation
            is_valid = await test_manager.validate_session(test_session_id)
            self.log_success(f"Session validation: {is_valid}")
            
            # Test deletion (the corrected method)
            await test_manager.delete_session(test_session_id)
            self.log_success("Session deletion works with delete_session()")
            
            # Verify deletion
            is_valid_after = await test_manager.validate_session(test_session_id)
            self.log_success(f"Session invalid after deletion: {not is_valid_after}")
            
            return True
            
        except Exception as e:
            self.log_error("CHUK Sessions test failed", e)
            return False
    
    async def test_4_session_manager_creation(self):
        """Test 4: Session manager creation and basic functionality."""
        self.log("\n🧪 TEST 4: Testing session manager creation...", "INFO")
        
        try:
            from chuk_mcp_ios.core.session_manager import UnifiedSessionManager, SessionConfig
            from chuk_mcp_ios.core.base import DeviceType
            
            # Create session manager
            self.session_manager = UnifiedSessionManager()
            self.log_success("UnifiedSessionManager created")
            
            # Test basic methods
            sessions = await self.run_sync(self.session_manager.list_sessions)
            self.log(f"Current sessions: {len(sessions)}", "INFO")
            
            # Create session config
            config = SessionConfig(
                device_name="iPhone 16 Pro",
                autoboot=True,
                prefer_available=True
            )
            self.log_success("SessionConfig created")
            
            return True
            
        except Exception as e:
            self.log_error("Session manager creation failed", e)
            return False
    
    async def test_5_mcp_session_creation(self):
        """Test 5: Test session creation via updated MCP tools."""
        self.log("\n🧪 TEST 5: Testing MCP session creation with CHUK integration...", "INFO")
        
        try:
            from chuk_mcp_ios.mcp.tools import ios_create_session
            
            # Create session via MCP tools
            self.log("Creating session via ios_create_session...", "INFO")
            result = await ios_create_session(
                device_name="iPhone 16 Pro",
                autoboot=True,
                session_name="debug_session_mcp"
            )
            
            if 'error' in result:
                self.log_error(f"MCP session creation failed: {result['error']}")
                return False
            
            self.session_id = result['session_id']
            self.test_sessions.append(self.session_id)  # Track for cleanup
            
            self.log_success(f"MCP session created: {self.session_id}")
            self.log(f"Device: {result['device_name']}", "INFO")
            self.log(f"State: {result['state']}", "INFO")
            self.log(f"CHUK registered: {result.get('registered_with_chuk', False)}", "INFO")
            self.log(f"CHUK available: {result.get('chuk_available', False)}", "INFO")
            
            return True
            
        except Exception as e:
            self.log_error("MCP session creation failed", e)
            return False
    
    async def test_6_session_status_validation(self):
        """Test 6: Test comprehensive session status validation."""
        self.log("\n🧪 TEST 6: Testing session status validation...", "INFO")
        
        try:
            if not self.session_id:
                self.log_error("No session available from previous test")
                return False
            
            from chuk_mcp_ios.mcp.tools import ios_session_status, is_ios_session_valid
            
            # Test comprehensive status
            self.log("6.1: Testing comprehensive session status...", "INFO")
            status = await ios_session_status(self.session_id)
            
            self.log_success(f"Session status retrieved:")
            self.log(f"   In registry: {status.get('in_registry', False)}", "INFO")
            self.log(f"   CHUK valid: {status.get('chuk_valid', False)}", "INFO")
            self.log(f"   In unified manager: {status.get('in_unified_manager', False)}", "INFO")
            self.log(f"   CHUK available: {status.get('chuk_sessions_available', False)}", "INFO")
            self.log(f"   Overall valid: {status.get('overall_valid', False)}", "INFO")
            
            # Test simple validation
            self.log("6.2: Testing simple session validation...", "INFO")
            is_valid = await is_ios_session_valid(self.session_id)
            self.log_success(f"Session validation result: {is_valid}")
            
            return status.get('overall_valid', False)
            
        except Exception as e:
            self.log_error("Session status validation failed", e)
            return False
    
    async def test_7_debug_sessions_tool(self):
        """Test 7: Test the debug sessions tool."""
        self.log("\n🧪 TEST 7: Testing debug sessions tool...", "INFO")
        
        try:
            from chuk_mcp_ios.mcp.tools import ios_debug_sessions
            
            debug_info = await ios_debug_sessions()
            
            self.log_success("Debug sessions info retrieved:")
            self.log(f"   CHUK available: {debug_info.get('chuk_sessions_available', False)}", "INFO")
            self.log(f"   Registry sessions: {debug_info.get('registry_count', 0)}", "INFO")
            self.log(f"   Unified sessions: {debug_info.get('unified_count', 0)}", "INFO")
            
            registry_sessions = debug_info.get('registry_sessions', [])
            unified_sessions = debug_info.get('unified_sessions', [])
            
            self.log(f"   Registry session IDs: {registry_sessions}", "INFO")
            self.log(f"   Unified session IDs: {unified_sessions}", "INFO")
            
            if 'session_validity' in debug_info:
                validity = debug_info['session_validity']
                self.log(f"   Session validity: {validity}", "INFO")
            
            if 'chuk_stats' in debug_info:
                stats = debug_info['chuk_stats']
                self.log(f"   CHUK stats: {stats}", "INFO")
            
            return True
            
        except Exception as e:
            self.log_error("Debug sessions test failed", e)
            return False
    
    async def test_8_session_based_operations(self):
        """Test 8: Test session-based operations."""
        self.log("\n🧪 TEST 8: Testing session-based operations...", "INFO")
        
        try:
            if not self.session_id:
                self.log_error("No session available")
                return False
            
            from chuk_mcp_ios.mcp.tools import ios_open_url, ios_list_sessions
            
            # Test ios_open_url
            self.log("8.1: Testing ios_open_url...", "INFO")
            url_result = await ios_open_url(self.session_id, "https://www.apple.com")
            
            if url_result.get('success', False):
                self.log_success("ios_open_url succeeded")
            else:
                self.log_error(f"ios_open_url failed: {url_result.get('error', 'Unknown error')}")
                return False
            
            # Test session listing
            self.log("8.2: Testing session listing...", "INFO")
            sessions_result = await ios_list_sessions()
            
            sessions = sessions_result.get('sessions', [])
            self.log_success(f"Found {len(sessions)} sessions in listing")
            
            # Check if our session is in the list
            our_session = None
            for session in sessions:
                if session['session_id'] == self.session_id:
                    our_session = session
                    break
            
            if our_session:
                self.log_success(f"Our session found in listing: {our_session['device_name']}")
                self.log(f"   Available: {our_session['is_available']}", "INFO")
                self.log(f"   State: {our_session['state']}", "INFO")
            else:
                self.log_warning("Our session not found in listing")
            
            return True
            
        except Exception as e:
            self.log_error("Session-based operations test failed", e)
            return False
    
    async def test_9_multiple_sessions(self):
        """Test 9: Test multiple session creation and management."""
        self.log("\n🧪 TEST 9: Testing multiple sessions...", "INFO")
        
        try:
            from chuk_mcp_ios.mcp.tools import ios_create_session, ios_debug_sessions
            
            # Create additional test sessions
            additional_sessions = []
            
            for i in range(2):
                self.log(f"Creating additional session {i+1}...", "INFO")
                result = await ios_create_session(
                    device_name="iPhone 16 Pro",
                    autoboot=True,
                    session_name=f"debug_multi_{i+1}"
                )
                
                if 'error' not in result:
                    session_id = result['session_id']
                    additional_sessions.append(session_id)
                    self.test_sessions.append(session_id)
                    self.log_success(f"Additional session created: {session_id}")
                else:
                    self.log_warning(f"Failed to create additional session: {result['error']}")
            
            # Check debug info with multiple sessions
            self.log("Checking debug info with multiple sessions...", "INFO")
            debug_info = await ios_debug_sessions()
            
            total_registry = debug_info.get('registry_count', 0)
            total_unified = debug_info.get('unified_count', 0)
            
            self.log_success(f"Multiple sessions test completed:")
            self.log(f"   Created additional sessions: {len(additional_sessions)}", "INFO")
            self.log(f"   Total registry sessions: {total_registry}", "INFO")
            self.log(f"   Total unified sessions: {total_unified}", "INFO")
            
            return len(additional_sessions) > 0
            
        except Exception as e:
            self.log_error("Multiple sessions test failed", e)
            return False
    
    async def test_10_cleanup_and_termination(self):
        """Test 10: Test session cleanup and termination."""
        self.log("\n🧪 TEST 10: Testing cleanup and termination...", "INFO")
        
        try:
            from chuk_mcp_ios.mcp.tools import ios_terminate_session, ios_session_status
            
            terminated_count = 0
            
            # Terminate all test sessions
            for session_id in self.test_sessions:
                self.log(f"Terminating session: {session_id}", "INFO")
                
                try:
                    result = await ios_terminate_session(session_id)
                    
                    if result.get('success', False):
                        self.log_success(f"Session terminated: {session_id}")
                        self.log(f"   CHUK cleanup: {result.get('chuk_cleanup', False)}", "INFO")
                        terminated_count += 1
                        
                        # Verify termination
                        status = await ios_session_status(session_id)
                        self.log(f"   Post-termination status: overall_valid={status.get('overall_valid', 'unknown')}", "INFO")
                        
                    else:
                        self.log_error(f"Failed to terminate session: {result.get('error', 'Unknown error')}")
                
                except Exception as e:
                    self.log_error(f"Exception terminating session {session_id}", e)
            
            self.log_success(f"Terminated {terminated_count}/{len(self.test_sessions)} sessions")
            
            # Clean up the original session manager session if it exists
            if self.session_manager and hasattr(self, 'direct_session_id'):
                try:
                    await self.run_sync(self.session_manager.terminate_session, self.direct_session_id)
                    self.log_success("Direct session manager session terminated")
                except Exception as e:
                    self.log_warning(f"Failed to terminate direct session: {e}")
            
            return terminated_count > 0
            
        except Exception as e:
            self.log_error("Cleanup test failed", e)
            return False
    
    async def test_11_final_verification(self):
        """Test 11: Final verification of cleanup."""
        self.log("\n🧪 TEST 11: Final verification...", "INFO")
        
        try:
            from chuk_mcp_ios.mcp.tools import ios_debug_sessions, ios_list_sessions
            
            # Check final state
            debug_info = await ios_debug_sessions()
            sessions_list = await ios_list_sessions()
            
            final_registry = debug_info.get('registry_count', 0)
            final_unified = debug_info.get('unified_count', 0)
            final_listed = len(sessions_list.get('sessions', []))
            
            self.log_success("Final verification completed:")
            self.log(f"   Registry sessions remaining: {final_registry}", "INFO")
            self.log(f"   Unified sessions remaining: {final_unified}", "INFO")
            self.log(f"   Listed sessions remaining: {final_listed}", "INFO")
            
            # Check if any of our test sessions still exist
            remaining_test_sessions = []
            for session in sessions_list.get('sessions', []):
                if session['session_id'] in self.test_sessions:
                    remaining_test_sessions.append(session['session_id'])
            
            if remaining_test_sessions:
                self.log_warning(f"Test sessions still exist: {remaining_test_sessions}")
            else:
                self.log_success("All test sessions cleaned up successfully")
            
            return True
            
        except Exception as e:
            self.log_error("Final verification failed", e)
            return False
    
    async def run_full_debug(self):
        """Run the complete debug sequence."""
        self.log("🔬 Starting End-to-End Session Debug - Updated for Fixed CHUK Integration", "INFO")
        self.log("=" * 80, "INFO")
        
        tests = [
            ("Import Test", self.test_1_imports),
            ("Device Discovery", self.test_2_device_discovery),
            ("CHUK Sessions Availability", self.test_3_chuk_sessions_availability),
            ("Session Manager Creation", self.test_4_session_manager_creation),
            ("MCP Session Creation", self.test_5_mcp_session_creation),
            ("Session Status Validation", self.test_6_session_status_validation),
            ("Debug Sessions Tool", self.test_7_debug_sessions_tool),
            ("Session-Based Operations", self.test_8_session_based_operations),
            ("Multiple Sessions", self.test_9_multiple_sessions),
            ("Cleanup and Termination", self.test_10_cleanup_and_termination),
            ("Final Verification", self.test_11_final_verification)
        ]
        
        passed = 0
        failed = 0
        results = {}
        
        for test_name, test_func in tests:
            self.log(f"\n{'='*20} {test_name} {'='*20}", "INFO")
            try:
                result = await test_func()
                if result:
                    passed += 1
                    results[test_name] = "PASS"
                    self.log_success(f"{test_name} PASSED")
                else:
                    failed += 1
                    results[test_name] = "FAIL"
                    self.log_error(f"{test_name} FAILED")
            except Exception as e:
                failed += 1
                results[test_name] = "ERROR"
                self.log_error(f"{test_name} CRASHED", e)
        
        # Final summary
        duration = time.time() - self.start_time
        self.log(f"\n📊 COMPREHENSIVE DEBUG SUMMARY", "INFO")
        self.log("=" * 50, "INFO")
        self.log(f"Total tests: {len(tests)}", "INFO")
        self.log(f"Passed: {passed}", "SUCCESS" if passed > 0 else "INFO")
        self.log(f"Failed: {failed}", "ERROR" if failed > 0 else "INFO")
        self.log(f"Duration: {duration:.2f} seconds", "INFO")
        
        # Detailed results
        self.log(f"\nDetailed Results:", "INFO")
        for test_name, result in results.items():
            icon = "✅" if result == "PASS" else "❌" if result == "FAIL" else "💥"
            self.log(f"  {icon} {test_name}: {result}", "INFO")
        
        if failed == 0:
            self.log("🎉 All tests passed! CHUK Sessions integration is working perfectly.", "SUCCESS")
            self.log("🔗 The updated integration provides:", "INFO")
            self.log("   - Proper CHUK Sessions lifecycle management", "INFO")
            self.log("   - Correct session validation and cleanup", "INFO")
            self.log("   - Enhanced debugging and status reporting", "INFO")
            self.log("   - Robust error handling and fallback", "INFO")
        else:
            self.log("🔍 Issues found. See debug log above for details.", "WARNING")
            self.log("💡 Check the individual test results for specific problems.", "INFO")
        
        return failed == 0
    
    def save_debug_log(self, filename: str = "session_debug_updated.log"):
        """Save debug log to file."""
        try:
            with open(filename, 'w') as f:
                f.write("iOS Session Debug Log - Updated CHUK Sessions Integration\n")
                f.write("=" * 60 + "\n\n")
                f.write(f"Debug run completed at: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Total test sessions created: {len(self.test_sessions)}\n")
                f.write(f"Test session IDs: {self.test_sessions}\n\n")
                
                for entry in self.debug_log:
                    f.write(entry + "\n")
            self.log(f"Debug log saved to: {filename}", "INFO")
        except Exception as e:
            self.log_error(f"Failed to save debug log: {e}")

async def main():
    """Main debug script entry point."""
    debugger = SessionDebugger()
    
    try:
        success = await debugger.run_full_debug()
        debugger.save_debug_log()
        
        if not success:
            print(f"\n💡 TROUBLESHOOTING RECOMMENDATIONS:")
            print(f"1. Verify the updated tools.py is deployed correctly")
            print(f"2. Check CHUK Sessions installation and configuration")
            print(f"3. Ensure iOS simulators are available and functional")
            print(f"4. Review the debug log: session_debug_updated.log")
            print(f"5. Run individual MCP tools manually to isolate issues")
            print(f"6. Check that delete_session() method is available in CHUK Sessions")
        
        return success
        
    except Exception as e:
        debugger.log_error("Debug script crashed", e)
        debugger.save_debug_log()
        return False

if __name__ == "__main__":
    print("🚀 Starting Updated iOS Session Debug Script...")
    print("🔧 Testing Fixed CHUK Sessions Integration")
    print("=" * 60)
    
    success = asyncio.run(main())
    
    if success:
        print("\n✅ Debug completed successfully!")
        print("🎉 CHUK Sessions integration is working properly!")
        sys.exit(0)
    else:
        print("\n❌ Debug found issues. Check the output above.")
        print("📄 Review session_debug_updated.log for detailed information")
        sys.exit(1)