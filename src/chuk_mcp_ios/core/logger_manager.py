#!/usr/bin/env python3
# chuk_mcp_ios/core/logger_manager.py
"""
Unified Logger Manager for iOS Device Control

Handles logging, crash reports, and debugging information for both simulators and real devices.
"""

import os
import re
import json
import time
import threading
from typing import List, Optional, Union, Dict, Any, Callable
from dataclasses import dataclass
from pathlib import Path
from datetime import datetime, timedelta
from collections import deque

from .base import (
    CommandExecutor,
    DeviceType,
    DeviceNotAvailableError,
    DeviceError,
    detect_available_tools
)
from .device_manager import UnifiedDeviceManager
from .session_manager import UnifiedSessionManager

@dataclass
class LogEntry:
    """Represents a single log entry."""
    timestamp: datetime
    level: str  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    process: str
    pid: Optional[int]
    message: str
    subsystem: Optional[str] = None
    category: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'timestamp': self.timestamp.isoformat(),
            'level': self.level,
            'process': self.process,
            'pid': self.pid,
            'message': self.message,
            'subsystem': self.subsystem,
            'category': self.category
        }

@dataclass
class CrashReport:
    """Represents a crash report."""
    app_name: str
    bundle_id: str
    timestamp: datetime
    exception_type: str
    exception_codes: str
    crashed_thread: int
    backtrace: List[str]
    system_info: Dict[str, str]
    full_report: str
    
    def get_summary(self) -> str:
        """Get crash summary."""
        return (f"Crash in {self.app_name} ({self.bundle_id}) at {self.timestamp}\n"
                f"Exception: {self.exception_type} - {self.exception_codes}\n"
                f"Thread {self.crashed_thread} crashed")

class LogFilter:
    """Filter for log entries."""
    
    def __init__(self, 
                 bundle_id: Optional[str] = None,
                 process: Optional[str] = None,
                 level: Optional[str] = None,
                 subsystem: Optional[str] = None,
                 category: Optional[str] = None,
                 since: Optional[datetime] = None,
                 until: Optional[datetime] = None,
                 pattern: Optional[str] = None):
        self.bundle_id = bundle_id
        self.process = process
        self.level = level
        self.subsystem = subsystem
        self.category = category
        self.since = since
        self.until = until
        self.pattern = re.compile(pattern) if pattern else None
    
    def matches(self, entry: LogEntry) -> bool:
        """Check if log entry matches filter."""
        if self.process and entry.process != self.process:
            return False
        if self.level and entry.level != self.level:
            return False
        if self.subsystem and entry.subsystem != self.subsystem:
            return False
        if self.category and entry.category != self.category:
            return False
        if self.since and entry.timestamp < self.since:
            return False
        if self.until and entry.timestamp > self.until:
            return False
        if self.pattern and not self.pattern.search(entry.message):
            return False
        return True

class UnifiedLoggerManager(CommandExecutor):
    """
    Unified logger manager supporting both iOS simulators and real devices.
    Handles system logs, app logs, crash reports, and real-time monitoring.
    """
    
    def __init__(self):
        super().__init__()
        self.device_manager = UnifiedDeviceManager()
        self.session_manager = None  # Optional session manager
        self.available_tools = detect_available_tools()
        self._monitors = {}  # Active log monitors
        self._log_cache = {}  # Recent logs cache
    
    def set_session_manager(self, session_manager: UnifiedSessionManager):
        """Set session manager for session-based operations."""
        self.session_manager = session_manager
    
    # Log Retrieval
    
    def get_logs(self, target: Union[str, Dict], 
                 filter: Optional[LogFilter] = None,
                 limit: Optional[int] = None) -> List[LogEntry]:
        """
        Get device logs with optional filtering.
        
        Args:
            target: Device UDID or session ID
            filter: Optional log filter
            limit: Maximum number of entries
            
        Returns:
            List[LogEntry]: Filtered log entries
        """
        udid = self._resolve_target(target)
        self._verify_device_available(udid)
        
        device = self.device_manager.get_device(udid)
        if not device:
            raise DeviceNotAvailableError(f"Device not found: {udid}")
        
        # Get logs based on device type
        if device.device_type == DeviceType.SIMULATOR:
            entries = self._get_logs_simulator(udid, filter)
        else:
            entries = self._get_logs_real_device(udid, filter)
        
        # Apply additional filtering
        if filter:
            entries = [e for e in entries if filter.matches(e)]
        
        # Apply limit
        if limit and len(entries) > limit:
            entries = entries[-limit:]  # Get most recent
        
        return entries
    
    def get_app_logs(self, target: Union[str, Dict], bundle_id: str,
                     since: Optional[datetime] = None,
                     limit: Optional[int] = None) -> List[LogEntry]:
        """Get logs for a specific app."""
        filter = LogFilter(bundle_id=bundle_id, since=since)
        return self.get_logs(target, filter, limit)
    
    def get_system_logs(self, target: Union[str, Dict],
                       since: Optional[datetime] = None,
                       limit: Optional[int] = 100) -> List[LogEntry]:
        """Get system logs."""
        filter = LogFilter(since=since)
        return self.get_logs(target, filter, limit)
    
    def search_logs(self, target: Union[str, Dict], pattern: str,
                   since: Optional[datetime] = None,
                   limit: Optional[int] = None) -> List[LogEntry]:
        """Search logs for pattern."""
        filter = LogFilter(pattern=pattern, since=since)
        return self.get_logs(target, filter, limit)
    
    # Real-time Monitoring
    
    def start_monitoring(self, target: Union[str, Dict],
                        callback: Callable[[LogEntry], None],
                        filter: Optional[LogFilter] = None) -> str:
        """
        Start real-time log monitoring.
        
        Args:
            target: Device UDID or session ID
            callback: Function called for each log entry
            filter: Optional log filter
            
        Returns:
            str: Monitor ID for stopping later
        """
        udid = self._resolve_target(target)
        monitor_id = f"monitor_{udid}_{int(time.time())}"
        
        # Create monitor thread
        monitor_thread = threading.Thread(
            target=self._monitor_logs,
            args=(udid, monitor_id, callback, filter),
            daemon=True
        )
        
        self._monitors[monitor_id] = {
            'thread': monitor_thread,
            'active': True,
            'udid': udid,
            'filter': filter,
            'started_at': datetime.now()
        }
        
        monitor_thread.start()
        print(f"✅ Started log monitoring: {monitor_id}")
        
        return monitor_id
    
    def stop_monitoring(self, monitor_id: str) -> None:
        """Stop log monitoring."""
        if monitor_id in self._monitors:
            self._monitors[monitor_id]['active'] = False
            print(f"✅ Stopped log monitoring: {monitor_id}")
    
    def stop_all_monitoring(self) -> None:
        """Stop all active monitors."""
        for monitor_id in list(self._monitors.keys()):
            self.stop_monitoring(monitor_id)
    
    # Crash Reports
    
    def get_crash_reports(self, target: Union[str, Dict],
                         bundle_id: Optional[str] = None,
                         since: Optional[datetime] = None) -> List[CrashReport]:
        """
        Get crash reports.
        
        Args:
            target: Device UDID or session ID
            bundle_id: Optional app bundle ID filter
            since: Optional time filter
            
        Returns:
            List[CrashReport]: Crash reports
        """
        udid = self._resolve_target(target)
        self._verify_device_available(udid)
        
        device = self.device_manager.get_device(udid)
        if not device:
            raise DeviceNotAvailableError(f"Device not found: {udid}")
        
        # Get crash reports based on device type
        if device.device_type == DeviceType.SIMULATOR:
            reports = self._get_crash_reports_simulator(udid)
        else:
            reports = self._get_crash_reports_real_device(udid)
        
        # Filter by bundle ID
        if bundle_id:
            reports = [r for r in reports if r.bundle_id == bundle_id]
        
        # Filter by time
        if since:
            reports = [r for r in reports if r.timestamp >= since]
        
        return sorted(reports, key=lambda r: r.timestamp, reverse=True)
    
    def get_latest_crash(self, target: Union[str, Dict],
                        bundle_id: str) -> Optional[CrashReport]:
        """Get the latest crash report for an app."""
        reports = self.get_crash_reports(target, bundle_id)
        return reports[0] if reports else None
    
    def export_crash_report(self, crash_report: CrashReport,
                           output_path: Path) -> None:
        """Export crash report to file."""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Export full report
        output_path.write_text(crash_report.full_report)
        
        # Also export summary
        summary_path = output_path.with_suffix('.summary.txt')
        summary_path.write_text(crash_report.get_summary())
        
        print(f"📄 Exported crash report to {output_path}")
    
    # Log Export
    
    def export_logs(self, target: Union[str, Dict], output_dir: Path,
                   filter: Optional[LogFilter] = None,
                   format: str = 'json') -> List[Path]:
        """
        Export logs to files.
        
        Args:
            target: Device UDID or session ID
            output_dir: Output directory
            filter: Optional log filter
            format: Export format (json, txt, csv)
            
        Returns:
            List[Path]: Created file paths
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Get logs
        logs = self.get_logs(target, filter)
        
        if not logs:
            print("No logs to export")
            return []
        
        created_files = []
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if format == 'json':
            # Export as JSON
            file_path = output_dir / f"logs_{timestamp}.json"
            data = {
                'export_time': datetime.now().isoformat(),
                'device_udid': self._resolve_target(target),
                'total_entries': len(logs),
                'entries': [log.to_dict() for log in logs]
            }
            
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2)
            
            created_files.append(file_path)
            
        elif format == 'txt':
            # Export as text
            file_path = output_dir / f"logs_{timestamp}.txt"
            with open(file_path, 'w') as f:
                for log in logs:
                    f.write(f"[{log.timestamp}] {log.level} - {log.process}: {log.message}\n")
            
            created_files.append(file_path)
            
        elif format == 'csv':
            # Export as CSV
            import csv
            file_path = output_dir / f"logs_{timestamp}.csv"
            
            with open(file_path, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['Timestamp', 'Level', 'Process', 'PID', 'Message', 'Subsystem', 'Category'])
                
                for log in logs:
                    writer.writerow([
                        log.timestamp.isoformat(),
                        log.level,
                        log.process,
                        log.pid or '',
                        log.message,
                        log.subsystem or '',
                        log.category or ''
                    ])
            
            created_files.append(file_path)
        
        print(f"📄 Exported {len(logs)} log entries to {len(created_files)} files")
        return created_files
    
    # Analysis Functions
    
    def analyze_logs(self, target: Union[str, Dict],
                    filter: Optional[LogFilter] = None) -> Dict[str, Any]:
        """
        Analyze logs and provide statistics.
        
        Returns:
            Dict with analysis results
        """
        logs = self.get_logs(target, filter)
        
        if not logs:
            return {'total_entries': 0}
        
        # Count by level
        level_counts = {}
        for log in logs:
            level_counts[log.level] = level_counts.get(log.level, 0) + 1
        
        # Count by process
        process_counts = {}
        for log in logs:
            process_counts[log.process] = process_counts.get(log.process, 0) + 1
        
        # Find errors and warnings
        errors = [log for log in logs if log.level in ['ERROR', 'CRITICAL']]
        warnings = [log for log in logs if log.level == 'WARNING']
        
        # Time range
        time_range = {
            'start': min(log.timestamp for log in logs),
            'end': max(log.timestamp for log in logs)
        }
        
        return {
            'total_entries': len(logs),
            'time_range': time_range,
            'level_distribution': level_counts,
            'top_processes': sorted(process_counts.items(), key=lambda x: x[1], reverse=True)[:10],
            'error_count': len(errors),
            'warning_count': len(warnings),
            'errors_per_minute': len(errors) / max(1, (time_range['end'] - time_range['start']).total_seconds() / 60)
        }
    
    def get_error_summary(self, target: Union[str, Dict],
                         since: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """Get summary of errors."""
        filter = LogFilter(level='ERROR', since=since)
        errors = self.get_logs(target, filter)
        
        # Group errors by message pattern
        error_groups = {}
        for error in errors:
            # Simple grouping by first 50 chars of message
            key = error.message[:50]
            if key not in error_groups:
                error_groups[key] = {
                    'pattern': key,
                    'count': 0,
                    'first_seen': error.timestamp,
                    'last_seen': error.timestamp,
                    'processes': set()
                }
            
            error_groups[key]['count'] += 1
            error_groups[key]['last_seen'] = max(error_groups[key]['last_seen'], error.timestamp)
            error_groups[key]['processes'].add(error.process)
        
        # Convert to list
        summary = []
        for group in error_groups.values():
            summary.append({
                'pattern': group['pattern'],
                'count': group['count'],
                'first_seen': group['first_seen'].isoformat(),
                'last_seen': group['last_seen'].isoformat(),
                'processes': list(group['processes'])
            })
        
        return sorted(summary, key=lambda x: x['count'], reverse=True)
    
    # Helper Methods
    
    def _resolve_target(self, target: Union[str, Dict]) -> str:
        """Resolve target to device UDID."""
        if isinstance(target, str):
            # Check if it's a session ID
            if self.session_manager and target.startswith(('session_', 'automation_')):
                try:
                    return self.session_manager.get_device_udid(target)
                except:
                    pass
            # Otherwise assume it's a UDID
            return target
        elif isinstance(target, dict):
            # Extract UDID from dict
            return target.get('udid', target.get('device_udid', ''))
        else:
            raise ValueError(f"Invalid target: {target}")
    
    def _verify_device_available(self, udid: str):
        """Verify device is available."""
        if not self.device_manager.is_device_available(udid):
            raise DeviceNotAvailableError(f"Device not available: {udid}")
    
    def _parse_log_line(self, line: str) -> Optional[LogEntry]:
        """Parse a log line into LogEntry."""
        # Common log format: timestamp level process[pid]: message
        # This is simplified - real implementation would handle various formats
        
        patterns = [
            # Standard format
            r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d+) (\w+)\s+(\w+)\[(\d+)\]: (.+)',
            # Alternative format
            r'(\w+ \d+ \d{2}:\d{2}:\d{2}) .+ (\w+)\[(\d+)\] <(\w+)>: (.+)'
        ]
        
        for pattern in patterns:
            match = re.match(pattern, line)
            if match:
                groups = match.groups()
                try:
                    # Parse timestamp
                    timestamp = datetime.strptime(groups[0], '%Y-%m-%d %H:%M:%S.%f')
                    
                    return LogEntry(
                        timestamp=timestamp,
                        level=groups[1].upper(),
                        process=groups[2],
                        pid=int(groups[3]) if groups[3].isdigit() else None,
                        message=groups[4]
                    )
                except:
                    pass
        
        # Fallback - treat whole line as message
        return LogEntry(
            timestamp=datetime.now(),
            level='INFO',
            process='unknown',
            pid=None,
            message=line.strip()
        )
    
    def _monitor_logs(self, udid: str, monitor_id: str,
                     callback: Callable[[LogEntry], None],
                     filter: Optional[LogFilter]):
        """Monitor logs in real-time (runs in thread)."""
        device = self.device_manager.get_device(udid)
        if not device:
            return
        
        print(f"Starting log monitor for {device.name}")
        
        # Use appropriate command based on device type
        if device.device_type == DeviceType.SIMULATOR:
            if self.available_tools.get('idb'):
                command = f"{self.idb_path} log --udid {udid} --follow"
            else:
                # Use log stream
                command = f"log stream --device {udid}"
        else:
            if self.available_tools.get('idb'):
                command = f"{self.idb_path} log --udid {udid} --follow"
            else:
                return  # No alternative for real devices
        
        # Start log process
        import subprocess
        process = subprocess.Popen(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )
        
        # Read logs line by line
        try:
            while self._monitors[monitor_id]['active']:
                line = process.stdout.readline()
                if not line:
                    break
                
                # Parse log entry
                entry = self._parse_log_line(line)
                if entry and (not filter or filter.matches(entry)):
                    callback(entry)
        
        finally:
            process.terminate()
            del self._monitors[monitor_id]
    
    # Simulator-specific implementations
    
    def _get_logs_simulator(self, udid: str, filter: Optional[LogFilter]) -> List[LogEntry]:
        """Get logs from simulator."""
        entries = []
        
        if self.available_tools.get('idb'):
            try:
                # Use idb log
                command = f"{self.idb_path} log --udid {udid}"
                if filter and filter.bundle_id:
                    command += f" --bundle {filter.bundle_id}"
                
                result = self.run_command(command, timeout=10)
                
                for line in result.stdout.split('\n'):
                    if line.strip():
                        entry = self._parse_log_line(line)
                        if entry:
                            entries.append(entry)
                
            except Exception as e:
                print(f"Warning: Failed to get logs via idb: {e}")
        
        # Fallback to log show
        if not entries:
            try:
                # Use log show command
                command = f"log show --device {udid} --style syslog"
                if filter and filter.since:
                    command += f" --start '{filter.since.strftime('%Y-%m-%d %H:%M:%S')}'"
                
                result = self.run_command(command, timeout=10)
                
                for line in result.stdout.split('\n'):
                    if line.strip():
                        entry = self._parse_log_line(line)
                        if entry:
                            entries.append(entry)
                            
            except Exception as e:
                print(f"Warning: Failed to get logs via log show: {e}")
        
        return entries
    
    def _get_crash_reports_simulator(self, udid: str) -> List[CrashReport]:
        """Get crash reports from simulator."""
        reports = []
        
        # Crash logs location
        crash_dir = Path.home() / "Library/Logs/DiagnosticReports"
        
        if crash_dir.exists():
            for crash_file in crash_dir.glob("*.crash"):
                try:
                    content = crash_file.read_text()
                    
                    # Parse crash report (simplified)
                    report = self._parse_crash_report(content)
                    if report:
                        reports.append(report)
                        
                except Exception as e:
                    print(f"Warning: Failed to parse crash report {crash_file}: {e}")
        
        return reports
    
    # Real device-specific implementations
    
    def _get_logs_real_device(self, udid: str, filter: Optional[LogFilter]) -> List[LogEntry]:
        """Get logs from real device."""
        if not self.available_tools.get('idb'):
            raise DeviceError("idb required for real device logs")
        
        entries = []
        
        try:
            command = f"{self.idb_path} log --udid {udid}"
            if filter and filter.bundle_id:
                command += f" --bundle {filter.bundle_id}"
            
            result = self.run_command(command, timeout=10)
            
            for line in result.stdout.split('\n'):
                if line.strip():
                    entry = self._parse_log_line(line)
                    if entry:
                        entries.append(entry)
                        
        except Exception as e:
            raise DeviceError(f"Failed to get logs: {e}")
        
        return entries
    
    def _get_crash_reports_real_device(self, udid: str) -> List[CrashReport]:
        """Get crash reports from real device."""
        if not self.available_tools.get('idb'):
            raise DeviceError("idb required for real device crash reports")
        
        reports = []
        
        try:
            # List crash logs
            result = self.run_command(f"{self.idb_path} crash list --udid {udid}")
            
            # Parse list and fetch each crash
            for line in result.stdout.split('\n'):
                if line.strip():
                    try:
                        # Get crash details
                        crash_result = self.run_command(f"{self.idb_path} crash show --udid {udid} {line.strip()}")
                        report = self._parse_crash_report(crash_result.stdout)
                        if report:
                            reports.append(report)
                    except:
                        pass
                        
        except Exception as e:
            print(f"Warning: Failed to get crash reports: {e}")
        
        return reports
    
    def _parse_crash_report(self, content: str) -> Optional[CrashReport]:
        """Parse crash report content."""
        # This is a simplified parser - real implementation would be more complex
        
        try:
            lines = content.split('\n')
            
            # Extract basic info
            app_name = "Unknown"
            bundle_id = "Unknown"
            exception_type = "Unknown"
            exception_codes = "Unknown"
            crashed_thread = 0
            
            for line in lines:
                if 'Process:' in line:
                    app_name = line.split('Process:')[1].split('[')[0].strip()
                elif 'Identifier:' in line:
                    bundle_id = line.split('Identifier:')[1].strip()
                elif 'Exception Type:' in line:
                    exception_type = line.split('Exception Type:')[1].strip()
                elif 'Exception Codes:' in line:
                    exception_codes = line.split('Exception Codes:')[1].strip()
                elif 'Crashed Thread:' in line:
                    crashed_thread = int(line.split('Crashed Thread:')[1].split()[0])
            
            return CrashReport(
                app_name=app_name,
                bundle_id=bundle_id,
                timestamp=datetime.now(),  # Would parse from report
                exception_type=exception_type,
                exception_codes=exception_codes,
                crashed_thread=crashed_thread,
                backtrace=[],  # Would parse backtrace
                system_info={},  # Would parse system info
                full_report=content
            )
            
        except Exception:
            return None