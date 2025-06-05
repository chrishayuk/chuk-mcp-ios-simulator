#!/usr/bin/env python3
#src/chuk_mcp_ios/logger_manager.py
"""
Logger Manager Module
Handles logging, crash reports, and debugging information.
"""

import re
import json
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from ios_simulator_base import (
    LoggerInterface,
    CrashLogInfo,
    CommandExecutor,
    SimulatorNotBootedError
)

class LoggerManager(CommandExecutor, LoggerInterface):
    """Manages logging and crash reporting for iOS simulator."""
    
    def __init__(self):
        super().__init__()
        self.verify_idb_availability()
    
    def get_system_logs(self, udid: str, bundle: Optional[str] = None, 
                       since: Optional[datetime] = None, limit: Optional[int] = None) -> str:
        """
        Get system logs from the simulator.
        
        Args:
            udid: Simulator UDID
            bundle: Optional bundle ID to filter logs
            since: Optional datetime to filter logs since
            limit: Optional limit on number of log entries
            
        Returns:
            str: System logs
            
        Raises:
            SimulatorNotBootedError: If simulator is not running
        """
        self._verify_simulator_booted(udid)
        
        try:
            command = f"{self.idb_path} log --udid {udid}"
            
            if bundle:
                command += f" --bundle {bundle}"
            if limit:
                command += f" --limit {limit}"
            
            # Add timeout to prevent hanging
            command += " --timeout 10"
            
            result = self.run_command(command, timeout=15)
            logs = result.stdout
            
            # Filter by timestamp if since is provided
            if since:
                logs = self._filter_logs_by_time(logs, since)
            
            return logs
            
        except Exception as e:
            raise Exception(f"Failed to get system logs: {str(e)}")
    
    def get_app_logs(self, udid: str, bundle_id: str, since: Optional[datetime] = None, 
                     limit: Optional[int] = None) -> str:
        """
        Get logs for a specific app.
        
        Args:
            udid: Simulator UDID
            bundle_id: App bundle identifier
            since: Optional datetime to filter logs since
            limit: Optional limit on number of log entries
            
        Returns:
            str: App-specific logs
        """
        return self.get_system_logs(udid, bundle=bundle_id, since=since, limit=limit)
    
    def get_crash_logs(self, udid: str, bundle_id: Optional[str] = None) -> str:
        """
        Get crash logs from the simulator.
        
        Args:
            udid: Simulator UDID
            bundle_id: Optional bundle ID to filter crash logs
            
        Returns:
            str: Crash logs
        """
        try:
            command = f"{self.idb_path} crash list --udid {udid}"
            if bundle_id:
                command += f" --bundle-id {bundle_id}"
            
            result = self.run_command(command)
            return result.stdout
            
        except Exception as e:
            raise Exception(f"Failed to get crash logs: {str(e)}")
    
    def list_crash_logs(self, udid: str, bundle_id: Optional[str] = None,
                       before: Optional[datetime] = None, since: Optional[datetime] = None) -> List[CrashLogInfo]:
        """
        List crash logs with detailed information.
        
        Args:
            udid: Simulator UDID
            bundle_id: Optional bundle ID filter
            before: Optional datetime filter (logs before this time)
            since: Optional datetime filter (logs since this time)
            
        Returns:
            List[CrashLogInfo]: List of crash log information
        """
        self._verify_simulator_booted(udid)
        
        try:
            command = f"{self.idb_path} crash list --udid {udid}"
            if bundle_id:
                command += f" --bundle-id {bundle_id}"
            if before:
                command += f" --before {before.isoformat()}"
            if since:
                command += f" --since {since.isoformat()}"
            
            result = self.run_command(command)
            return self._parse_crash_log_list(result.stdout)
            
        except Exception as e:
            raise Exception(f"Failed to list crash logs: {str(e)}")
    
    def get_crash_log(self, udid: str, crash_name: str) -> str:
        """
        Get the content of a specific crash log.
        
        Args:
            udid: Simulator UDID
            crash_name: Name of the crash log
            
        Returns:
            str: Crash log content
        """
        self._verify_simulator_booted(udid)
        
        try:
            result = self.run_command(f"{self.idb_path} crash show --udid {udid} {crash_name}")
            return result.stdout
            
        except Exception as e:
            raise Exception(f"Failed to get crash log {crash_name}: {str(e)}")
    
    def delete_crash_logs(self, udid: str, crash_names: Optional[List[str]] = None,
                         bundle_id: Optional[str] = None, before: Optional[datetime] = None,
                         since: Optional[datetime] = None, all_crashes: bool = False) -> None:
        """
        Delete crash logs based on various criteria.
        
        Args:
            udid: Simulator UDID
            crash_names: Optional list of specific crash log names to delete
            bundle_id: Optional bundle ID filter
            before: Optional datetime filter (delete logs before this time)
            since: Optional datetime filter (delete logs since this time)
            all_crashes: If True, delete all crash logs
        """
        self._verify_simulator_booted(udid)
        
        try:
            if all_crashes:
                self.run_command(f"{self.idb_path} crash delete --udid {udid} --all")
                print("Deleted all crash logs")
                return
            
            if crash_names:
                for crash_name in crash_names:
                    self.run_command(f"{self.idb_path} crash delete --udid {udid} {crash_name}")
                    print(f"Deleted crash log: {crash_name}")
                return
            
            command = f"{self.idb_path} crash delete --udid {udid}"
            if bundle_id:
                command += f" --bundle-id {bundle_id}"
            if before:
                command += f" --before {before.isoformat()}"
            if since:
                command += f" --since {since.isoformat()}"
            
            self.run_command(command)
            print("Deleted crash logs matching criteria")
            
        except Exception as e:
            raise Exception(f"Failed to delete crash logs: {str(e)}")
    
    def monitor_logs(self, udid: str, bundle_id: Optional[str] = None, 
                    duration: int = 30, output_file: Optional[str] = None) -> str:
        """
        Monitor logs in real-time for a specified duration.
        
        Args:
            udid: Simulator UDID
            bundle_id: Optional bundle ID to filter logs
            duration: Monitoring duration in seconds
            output_file: Optional file to save logs
            
        Returns:
            str: Collected logs
        """
        import time
        import threading
        
        logs_collected = []
        stop_monitoring = threading.Event()
        
        def collect_logs():
            while not stop_monitoring.is_set():
                try:
                    new_logs = self.get_system_logs(udid, bundle=bundle_id, limit=10)
                    if new_logs:
                        logs_collected.append(f"[{datetime.now().isoformat()}]\n{new_logs}\n")
                except:
                    pass
                time.sleep(1)
        
        print(f"Starting log monitoring for {duration} seconds...")
        monitor_thread = threading.Thread(target=collect_logs)
        monitor_thread.start()
        
        time.sleep(duration)
        stop_monitoring.set()
        monitor_thread.join()
        
        all_logs = '\n'.join(logs_collected)
        
        if output_file:
            with open(output_file, 'w') as f:
                f.write(all_logs)
            print(f"Logs saved to: {output_file}")
        
        print("Log monitoring completed")
        return all_logs
    
    def analyze_crash_log(self, udid: str, crash_name: str) -> Dict[str, Any]:
        """
        Analyze a crash log and extract key information.
        
        Args:
            udid: Simulator UDID
            crash_name: Name of the crash log
            
        Returns:
            Dict[str, Any]: Analysis results
        """
        crash_content = self.get_crash_log(udid, crash_name)
        
        analysis = {
            'crash_name': crash_name,
            'timestamp': None,
            'bundle_id': None,
            'exception_type': None,
            'exception_subtype': None,
            'crashed_thread': None,
            'stack_trace': [],
            'system_info': {},
            'summary': 'Unknown crash type'
        }
        
        lines = crash_content.split('\n')
        
        # Parse crash log for key information
        for i, line in enumerate(lines):
            line = line.strip()
            
            # Extract timestamp
            if 'Date/Time:' in line:
                analysis['timestamp'] = line.split('Date/Time:')[1].strip()
            
            # Extract bundle ID
            if 'Process:' in line and '[' in line and ']' in line:
                match = re.search(r'\[(.*?)\]', line)
                if match:
                    analysis['bundle_id'] = match.group(1)
            
            # Extract exception information
            if 'Exception Type:' in line:
                analysis['exception_type'] = line.split('Exception Type:')[1].strip()
            
            if 'Exception Subtype:' in line:
                analysis['exception_subtype'] = line.split('Exception Subtype:')[1].strip()
            
            # Extract crashed thread
            if 'Crashed Thread:' in line:
                analysis['crashed_thread'] = line.split('Crashed Thread:')[1].strip()
            
            # Extract system information
            if 'OS Version:' in line:
                analysis['system_info']['os_version'] = line.split('OS Version:')[1].strip()
            
            if 'Hardware Model:' in line:
                analysis['system_info']['hardware'] = line.split('Hardware Model:')[1].strip()
        
        # Generate summary
        if analysis['exception_type']:
            analysis['summary'] = f"{analysis['exception_type']} crash"
            if analysis['bundle_id']:
                analysis['summary'] += f" in {analysis['bundle_id']}"
        
        return analysis
    
    def export_logs(self, udid: str, output_dir: str, bundle_id: Optional[str] = None,
                   include_crashes: bool = True, since: Optional[datetime] = None) -> List[str]:
        """
        Export logs to files for analysis.
        
        Args:
            udid: Simulator UDID
            output_dir: Directory to save log files
            bundle_id: Optional bundle ID filter
            include_crashes: Whether to include crash logs
            since: Optional datetime filter
            
        Returns:
            List[str]: List of created log files
        """
        import os
        
        os.makedirs(output_dir, exist_ok=True)
        created_files = []
        
        # Export system logs
        try:
            logs = self.get_system_logs(udid, bundle=bundle_id, since=since)
            if logs:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"system_logs_{timestamp}.txt"
                if bundle_id:
                    filename = f"{bundle_id}_logs_{timestamp}.txt"
                
                filepath = os.path.join(output_dir, filename)
                with open(filepath, 'w') as f:
                    f.write(logs)
                created_files.append(filepath)
                print(f"Exported system logs to: {filepath}")
        except Exception as e:
            print(f"Failed to export system logs: {e}")
        
        # Export crash logs if requested
        if include_crashes:
            try:
                crash_logs = self.list_crash_logs(udid, bundle_id=bundle_id, since=since)
                for crash_info in crash_logs:
                    try:
                        crash_content = self.get_crash_log(udid, crash_info.name)
                        filename = f"crash_{crash_info.name}.txt"
                        filepath = os.path.join(output_dir, filename)
                        
                        with open(filepath, 'w') as f:
                            f.write(crash_content)
                        created_files.append(filepath)
                        print(f"Exported crash log to: {filepath}")
                    except Exception as e:
                        print(f"Failed to export crash log {crash_info.name}: {e}")
            except Exception as e:
                print(f"Failed to list crash logs: {e}")
        
        return created_files
    
    def _parse_crash_log_list(self, output: str) -> List[CrashLogInfo]:
        """Parse crash log list output into structured data."""
        crash_logs = []
        lines = [line.strip() for line in output.split('\n') if line.strip()]
        
        for line in lines:
            # Parse crash log line format: "name - bundle_id - date - path"
            parts = line.split(' - ')
            if len(parts) >= 1:
                name = parts[0].strip()
                bundle_id = parts[1].strip() if len(parts) > 1 else None
                
                # Try to parse date
                date = datetime.now()
                if len(parts) > 2:
                    try:
                        date_str = parts[2].strip()
                        date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                    except:
                        pass
                
                path = parts[3].strip() if len(parts) > 3 else ''
                
                crash_logs.append(CrashLogInfo(
                    name=name,
                    bundle_id=bundle_id,
                    date=date,
                    path=path
                ))
        
        return crash_logs
    
    def _filter_logs_by_time(self, logs: str, since: datetime) -> str:
        """Filter logs to only include entries since the specified time."""
        # This is a simplified implementation
        # Real log filtering would parse timestamps from each log entry
        lines = logs.split('\n')
        filtered_lines = []
        
        for line in lines:
            # Look for timestamp patterns in logs
            timestamp_match = re.search(r'\d{4}-\d{2}-\d{2}[\sT]\d{2}:\d{2}:\d{2}', line)
            if timestamp_match:
                try:
                    log_time = datetime.fromisoformat(timestamp_match.group(0).replace(' ', 'T'))
                    if log_time >= since:
                        filtered_lines.append(line)
                except:
                    filtered_lines.append(line)  # Include if we can't parse timestamp
            else:
                filtered_lines.append(line)  # Include lines without timestamps
        
        return '\n'.join(filtered_lines)
    
    def _verify_simulator_booted(self, udid: str) -> None:
        """Verify that simulator is booted."""
        from simulator_manager import SimulatorManager
        sim_manager = SimulatorManager()
        if not sim_manager.is_simulator_booted(udid):
            raise SimulatorNotBootedError(f"Simulator {udid} is not booted")