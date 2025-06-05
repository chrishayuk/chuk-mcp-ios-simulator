#!/usr/bin/env python3
# chuk_mcp/session_manager.py
"""
Session Manager Module
Handles creation, management, and cleanup of simulator sessions.
"""

import time
from typing import Dict, List, Optional
from ios_simulator_base import (
    SessionManagerInterface, 
    SessionConfig, 
    CommandExecutor, 
    SessionNotFoundError
)

class SessionManager(CommandExecutor, SessionManagerInterface):
    """Manages simulator sessions with automatic cleanup and state tracking."""
    
    def __init__(self):
        super().__init__()
        self.sessions: Dict[str, str] = {}  # sessionId -> udid
        self.session_counter = 0
        self.session_metadata: Dict[str, Dict] = {}  # Additional session info
    
    def _generate_session_id(self) -> str:
        """Generate a unique session ID."""
        session_id = f"session_{int(time.time())}_{self.session_counter}"
        self.session_counter += 1
        return session_id
    
    def create_session(self, config: Optional[SessionConfig] = None) -> str:
        """
        Create a new simulator session.
        
        Args:
            config: Optional session configuration
            
        Returns:
            str: The created session ID
            
        Raises:
            Exception: If no suitable simulator is found or session creation fails
        """
        from simulator_manager import SimulatorManager
        
        simulator_manager = SimulatorManager()
        
        if config and config.device_name:
            simulators = simulator_manager.list_available_simulators()
            simulator = next(
                (sim for sim in simulators 
                 if sim.name == config.device_name and 
                 (not config.platform_version or config.platform_version in sim.os)),
                None
            )
            if not simulator:
                raise Exception(f"No simulator found with name {config.device_name}")
            udid = simulator.udid
        else:
            simulators = simulator_manager.list_available_simulators()
            if not simulators:
                raise Exception("No available simulators found")
            udid = simulators[0].udid
        
        if not config or config.autoboot:
            simulator_manager.boot_simulator_by_udid(udid)
        
        session_id = self._generate_session_id()
        self.sessions[session_id] = udid
        
        # Store session metadata
        self.session_metadata[session_id] = {
            "created_at": time.time(),
            "config": config,
            "udid": udid,
            "autoboot": not config or config.autoboot
        }
        
        return session_id
    
    def terminate_session(self, session_id: str) -> None:
        """
        Terminate a simulator session.
        
        Args:
            session_id: The session ID to terminate
            
        Raises:
            SessionNotFoundError: If session ID is not found
        """
        if session_id not in self.sessions:
            raise SessionNotFoundError(f"Session not found: {session_id}")
        
        # Clean up session data
        del self.sessions[session_id]
        if session_id in self.session_metadata:
            del self.session_metadata[session_id]
    
    def list_sessions(self) -> List[str]:
        """
        List all active simulator sessions.
        
        Returns:
            List[str]: List of active session IDs
        """
        return list(self.sessions.keys())
    
    def get_udid_from_session(self, session_id: str) -> str:
        """
        Get UDID from session ID.
        
        Args:
            session_id: The session ID
            
        Returns:
            str: The simulator UDID
            
        Raises:
            SessionNotFoundError: If session ID is not found
        """
        if session_id not in self.sessions:
            raise SessionNotFoundError(f"Session not found: {session_id}")
        return self.sessions[session_id]
    
    def get_session_info(self, session_id: str) -> Dict:
        """
        Get detailed session information.
        
        Args:
            session_id: The session ID
            
        Returns:
            Dict: Session metadata and information
            
        Raises:
            SessionNotFoundError: If session ID is not found
        """
        if session_id not in self.sessions:
            raise SessionNotFoundError(f"Session not found: {session_id}")
        
        metadata = self.session_metadata.get(session_id, {})
        return {
            "session_id": session_id,
            "udid": self.sessions[session_id],
            "created_at": metadata.get("created_at"),
            "config": metadata.get("config"),
            "autoboot": metadata.get("autoboot", False)
        }
    
    def cleanup_inactive_sessions(self, max_age_hours: int = 24) -> List[str]:
        """
        Clean up sessions that have been inactive for too long.
        
        Args:
            max_age_hours: Maximum age in hours before cleanup
            
        Returns:
            List[str]: List of cleaned up session IDs
        """
        current_time = time.time()
        max_age_seconds = max_age_hours * 3600
        cleaned_sessions = []
        
        for session_id, metadata in list(self.session_metadata.items()):
            created_at = metadata.get("created_at", 0)
            if current_time - created_at > max_age_seconds:
                try:
                    self.terminate_session(session_id)
                    cleaned_sessions.append(session_id)
                except SessionNotFoundError:
                    pass  # Session already cleaned up
        
        return cleaned_sessions
    
    def validate_session(self, session_id: str) -> bool:
        """
        Validate that a session exists and is active.
        
        Args:
            session_id: The session ID to validate
            
        Returns:
            bool: True if session is valid and active
        """
        if session_id not in self.sessions:
            return False
        
        # Check if simulator is still available
        try:
            from simulator_manager import SimulatorManager
            simulator_manager = SimulatorManager()
            udid = self.sessions[session_id]
            simulators = simulator_manager.list_available_simulators()
            return any(sim.udid == udid for sim in simulators)
        except:
            return False
    
    def get_sessions_by_udid(self, udid: str) -> List[str]:
        """
        Get all session IDs for a specific simulator UDID.
        
        Args:
            udid: The simulator UDID
            
        Returns:
            List[str]: List of session IDs for the UDID
        """
        return [session_id for session_id, session_udid in self.sessions.items() 
                if session_udid == udid]
    
    def terminate_sessions_by_udid(self, udid: str) -> List[str]:
        """
        Terminate all sessions for a specific simulator UDID.
        
        Args:
            udid: The simulator UDID
            
        Returns:
            List[str]: List of terminated session IDs
        """
        session_ids = self.get_sessions_by_udid(udid)
        for session_id in session_ids:
            self.terminate_session(session_id)
        return session_ids