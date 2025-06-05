#!/usr/bin/env python3
"""
Utilities Manager Module
Handles miscellaneous utility operations including URL handling, permissions, and debugging.
"""

import re
import os
import json
from typing import List, Dict, Any, Optional
from ios_simulator_base import (
    UtilitiesInterface,
    DebugServerStatus,
    CommandExecutor,
    SimulatorNotBootedError
)

class UtilitiesManager(CommandExecutor, UtilitiesInterface):
    """Manages utility operations for iOS simulator."""
    
    def __init__(self):
        super().__init__()
        self.verify_idb_availability()
    
    def open_url(self, udid: str, url: str) -> None:
        """
        Open a URL in the simulator.
        
        Args:
            udid: Simulator UDID
            url: URL to open
            
        Raises:
            SimulatorNotBootedError: If simulator is not running
            ValueError: If URL format is invalid
        """
        self._verify_simulator_booted(udid)
        
        # Basic URL validation
        if not self._is_valid_url(url):
            raise ValueError(f"Invalid URL format: {url}")
        
        try:
            self.run_command(f"{self.idb_path} open --udid {udid} '{url}'")
            print(f"Opened URL: {url}")
        except Exception as e:
            raise Exception(f"Failed to open URL {url}: {str(e)}")
    
    def open_deep_link(self, udid: str, scheme: str, path: str = "", parameters: Optional[Dict[str, str]] = None) -> None:
        """
        Open a deep link with custom scheme.
        
        Args:
            udid: Simulator UDID
            scheme: URL scheme (e.g., 'myapp')
            path: Optional path component
            parameters: Optional query parameters
        """
        url = f"{scheme}://"
        if path:
            url += path
        
        if parameters:
            query_string = "&".join([f"{k}={v}" for k, v in parameters.items()])
            url += f"?{query_string}"
        
        self.open_url(udid, url)
    
    def clear_keychain(self, udid: str) -> None:
        """
        Clear the simulator's keychain.
        
        Args:
            udid: Simulator UDID
            
        Raises:
            SimulatorNotBootedError: If simulator is not running
        """
        self._verify_simulator_booted(udid)
        
        try:
            self.run_command(f"{self.idb_path} clear_keychain --udid {udid}")
            print("Keychain cleared successfully")
        except Exception as e:
            raise Exception(f"Failed to clear keychain: {str(e)}")
    
    def install_dylib(self, udid: str, dylib_path: str) -> None:
        """
        Install a dynamic library.
        
        Args:
            udid: Simulator UDID
            dylib_path: Path to the .dylib file
            
        Raises:
            SimulatorNotBootedError: If simulator is not running
            FileNotFoundError: If dylib file doesn't exist
        """
        self._verify_simulator_booted(udid)
        
        if not os.path.exists(dylib_path):
            raise FileNotFoundError(f"Dylib file not found: {dylib_path}")
        
        if not dylib_path.endswith('.dylib'):
            raise ValueError(f"File must be a .dylib file: {dylib_path}")
        
        try:
            self.run_command(f"{self.idb_path} dylib install --udid {udid} '{dylib_path}'")
            print(f"Successfully installed dylib: {os.path.basename(dylib_path)}")
        except Exception as e:
            raise Exception(f"Failed to install dylib {dylib_path}: {str(e)}")
    
    def approve_permissions(self, udid: str, bundle_id: str, permissions: List[str]) -> None:
        """
        Approve permissions for an app.
        
        Args:
            udid: Simulator UDID
            bundle_id: App bundle identifier
            permissions: List of permissions to approve
            
        Raises:
            SimulatorNotBootedError: If simulator is not running
        """
        self._verify_simulator_booted(udid)
        
        # Validate permissions
        valid_permissions = {
            'location', 'location-always', 'photos', 'camera', 'microphone',
            'contacts', 'calendar', 'reminders', 'notifications', 'health',
            'homekit', 'media-library', 'motion', 'speech-recognition',
            'siri', 'bluetooth', 'background-app-refresh'
        }
        
        invalid_permissions = [p for p in permissions if p not in valid_permissions]
        if invalid_permissions:
            print(f"Warning: Invalid permissions will be skipped: {invalid_permissions}")
            print(f"Valid permissions: {sorted(valid_permissions)}")
        
        valid_perms = [p for p in permissions if p in valid_permissions]
        if not valid_perms:
            raise ValueError("No valid permissions specified")
        
        try:
            permissions_str = ' '.join(valid_perms)
            self.run_command(f"{self.idb_path} approve --udid {udid} {bundle_id} {permissions_str}")
            print(f"Approved permissions for {bundle_id}: {', '.join(valid_perms)}")
        except Exception as e:
            raise Exception(f"Failed to approve permissions: {str(e)}")
    
    def deny_permissions(self, udid: str, bundle_id: str, permissions: List[str]) -> None:
        """
        Deny permissions for an app.
        
        Args:
            udid: Simulator UDID
            bundle_id: App bundle identifier
            permissions: List of permissions to deny
        """
        # This would require additional idb functionality
        # For now, we'll use a workaround through privacy database manipulation
        print(f"Note: Permission denial requires additional implementation")
        print(f"Requested to deny {', '.join(permissions)} for {bundle_id}")
    
    def update_contacts(self, udid: str, db_path: str) -> None:
        """
        Update contacts database.
        
        Args:
            udid: Simulator UDID
            db_path: Path to contacts database file
            
        Raises:
            SimulatorNotBootedError: If simulator is not running
            FileNotFoundError: If database file doesn't exist
        """
        self._verify_simulator_booted(udid)
        
        if not os.path.exists(db_path):
            raise FileNotFoundError(f"Database file not found: {db_path}")
        
        try:
            self.run_command(f"{self.idb_path} contacts update --udid {udid} '{db_path}'")
            print(f"Contacts database updated from: {db_path}")
        except Exception as e:
            raise Exception(f"Failed to update contacts: {str(e)}")
    
    def get_debug_server_status(self, udid: str) -> DebugServerStatus:
        """
        Get debug server status.
        
        Args:
            udid: Simulator UDID
            
        Returns:
            DebugServerStatus: Debug server status information
        """
        self._verify_simulator_booted(udid)
        
        try:
            result = self.run_command(f"{self.idb_path} debugserver status --udid {udid}")
            output = result.stdout
            
            if "No debug server running" in output:
                return DebugServerStatus(running=False)
            
            # Parse port and bundle ID from output
            port_match = re.search(r'port:\s*(\d+)', output)
            bundle_match = re.search(r'bundle_id:\s*([^\s]+)', output)
            
            return DebugServerStatus(
                running=True,
                port=int(port_match.group(1)) if port_match else None,
                bundle_id=bundle_match.group(1) if bundle_match else None
            )
        except Exception:
            return DebugServerStatus(running=False)
    
    def start_debug_server(self, udid: str, bundle_id: str, port: Optional[int] = None) -> DebugServerStatus:
        """
        Start debug server for an app.
        
        Args:
            udid: Simulator UDID
            bundle_id: App bundle identifier
            port: Optional specific port to use
            
        Returns:
            DebugServerStatus: Started debug server status
        """
        self._verify_simulator_booted(udid)
        
        try:
            command = f"{self.idb_path} debugserver start --udid {udid} {bundle_id}"
            if port:
                command += f" --port {port}"
            
            self.run_command(command)
            print(f"Debug server started for {bundle_id}")
            
            # Return the status
            return self.get_debug_server_status(udid)
        except Exception as e:
            raise Exception(f"Failed to start debug server: {str(e)}")
    
    def stop_debug_server(self, udid: str) -> None:
        """
        Stop the debug server.
        
        Args:
            udid: Simulator UDID
        """
        self._verify_simulator_booted(udid)
        
        try:
            self.run_command(f"{self.idb_path} debugserver stop --udid {udid}")
            print("Debug server stopped")
        except Exception as e:
            print(f"Note: Debug server may not have been running: {str(e)}")
    
    def focus_simulator(self, udid: str) -> None:
        """
        Focus the simulator window.
        
        Args:
            udid: Simulator UDID
            
        Raises:
            SimulatorNotBootedError: If simulator is not running
        """
        self._verify_simulator_booted(udid)
        
        try:
            self.run_command(f"{self.idb_path} focus --udid {udid}")
            print("Simulator window focused")
        except Exception as e:
            raise Exception(f"Failed to focus simulator: {str(e)}")
    
    def get_device_info(self, udid: str) -> Dict[str, Any]:
        """
        Get detailed device information.
        
        Args:
            udid: Simulator UDID
            
        Returns:
            Dict[str, Any]: Device information
        """
        self._verify_simulator_booted(udid)
        
        try:
            # Get basic device info
            result = self.run_command(f"{self.idb_path} describe --udid {udid} --json")
            device_info = json.loads(result.stdout)
            
            # Add additional information
            from simulator_manager import SimulatorManager
            sim_manager = SimulatorManager()
            simulator = sim_manager.get_simulator_by_udid(udid)
            
            if simulator:
                device_info.update({
                    'name': simulator.name,
                    'os': simulator.os,
                    'device_type': simulator.device_type,
                    'state': simulator.state
                })
            
            return device_info
        except Exception as e:
            # Fallback to basic info if describe command fails
            from simulator_manager import SimulatorManager
            sim_manager = SimulatorManager()
            simulator = sim_manager.get_simulator_by_udid(udid)
            
            if simulator:
                return {
                    'udid': udid,
                    'name': simulator.name,
                    'os': simulator.os,
                    'device_type': simulator.device_type,
                    'state': simulator.state,
                    'error': f"Failed to get detailed info: {str(e)}"
                }
            else:
                return {'error': f"Simulator not found: {udid}"}
    
    def reset_privacy_permissions(self, udid: str, bundle_id: Optional[str] = None) -> None:
        """
        Reset privacy permissions for an app or all apps.
        
        Args:
            udid: Simulator UDID
            bundle_id: Optional specific app bundle ID
        """
        self._verify_simulator_booted(udid)
        
        try:
            if bundle_id:
                # Reset for specific app using simctl
                self.run_command(f"{self.simctl_path} privacy {udid} reset all {bundle_id}")
                print(f"Reset privacy permissions for {bundle_id}")
            else:
                # Reset all privacy permissions
                self.run_command(f"{self.simctl_path} privacy {udid} reset all")
                print("Reset all privacy permissions")
        except Exception as e:
            raise Exception(f"Failed to reset privacy permissions: {str(e)}")
    
    def set_privacy_permission(self, udid: str, bundle_id: str, service: str, permission: str) -> None:
        """
        Set a specific privacy permission.
        
        Args:
            udid: Simulator UDID
            bundle_id: App bundle identifier
            service: Privacy service (e.g., 'photos', 'location', 'camera')
            permission: Permission level ('grant', 'deny', 'unset')
        """
        self._verify_simulator_booted(udid)
        
        valid_services = ['photos', 'camera', 'microphone', 'location', 'contacts', 'calendar', 'reminders']
        valid_permissions = ['grant', 'deny', 'unset']
        
        if service not in valid_services:
            raise ValueError(f"Invalid service: {service}. Valid: {valid_services}")
        if permission not in valid_permissions:
            raise ValueError(f"Invalid permission: {permission}. Valid: {valid_permissions}")
        
        try:
            self.run_command(f"{self.simctl_path} privacy {udid} {permission} {service} {bundle_id}")
            print(f"Set {service} permission to {permission} for {bundle_id}")
        except Exception as e:
            raise Exception(f"Failed to set privacy permission: {str(e)}")
    
    def create_contact_database(self, output_path: str, contacts: List[Dict[str, str]]) -> str:
        """
        Create a sample contacts database file.
        
        Args:
            output_path: Path for the output database file
            contacts: List of contact dictionaries
            
        Returns:
            str: Path to created database file
        """
        import sqlite3
        
        # Create contacts database
        conn = sqlite3.connect(output_path)
        cursor = conn.cursor()
        
        # Create contacts table (simplified structure)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS contacts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                first_name TEXT,
                last_name TEXT,
                phone_number TEXT,
                email TEXT
            )
        ''')
        
        # Insert contacts
        for contact in contacts:
            cursor.execute('''
                INSERT INTO contacts (first_name, last_name, phone_number, email)
                VALUES (?, ?, ?, ?)
            ''', (
                contact.get('first_name', ''),
                contact.get('last_name', ''),
                contact.get('phone_number', ''),
                contact.get('email', '')
            ))
        
        conn.commit()
        conn.close()
        
        print(f"Created contacts database with {len(contacts)} contacts: {output_path}")
        return output_path
    
    def _is_valid_url(self, url: str) -> bool:
        """Validate URL format."""
        # HTTP/HTTPS URL pattern
        url_pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:'  # start group
            r'(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain
            r'localhost|'  # localhost
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}'  # IP address
            r')'  # end group
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)?$',  # path
            re.IGNORECASE
        )
        
        # Custom scheme pattern for deep links
        custom_scheme_pattern = re.compile(r'^[a-zA-Z][a-zA-Z0-9+.-]*://')
        
        return bool(url_pattern.match(url) or custom_scheme_pattern.match(url))
    
    def _verify_simulator_booted(self, udid: str) -> None:
        """Verify that simulator is booted."""
        from simulator_manager import SimulatorManager
        sim_manager = SimulatorManager()
        if not sim_manager.is_simulator_booted(udid):
            raise SimulatorNotBootedError(f"Simulator {udid} is not booted")