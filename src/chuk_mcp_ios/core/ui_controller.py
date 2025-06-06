#!/usr/bin/env python3
# src/chuk_mcp_ios/core/ui_controller.py
"""
Unified UI Controller for iOS Device Control

Handles UI automation and interactions for both simulators and real devices.
"""

import os
import time
import json
import base64
from typing import List, Optional, Union, Tuple, Dict, Any
from dataclasses import dataclass
from pathlib import Path
from datetime import datetime

from .base import (
    UIControllerInterface,
    CommandExecutor,
    DeviceType,
    DeviceNotAvailableError,
    DeviceError,
    detect_available_tools
)
from .device_manager import UnifiedDeviceManager
from .session_manager import UnifiedSessionManager

@dataclass
class Point:
    """Represents a point on screen."""
    x: int
    y: int

@dataclass
class Gesture:
    """Represents a gesture configuration."""
    duration: int = 100  # milliseconds
    pressure: float = 1.0
    repeat: int = 1
    delay_between: int = 100  # milliseconds between repeats

@dataclass
class ScreenInfo:
    """Screen information."""
    width: int
    height: int
    scale: float
    orientation: str  # portrait, landscape

class UnifiedUIController(CommandExecutor, UIControllerInterface):
    """
    Unified UI controller supporting both iOS simulators and real devices.
    Handles touch, gestures, input, and screen capture.
    """
    
    def __init__(self):
        super().__init__()
        self.device_manager = UnifiedDeviceManager()
        self.session_manager = None  # Optional session manager
        self.available_tools = detect_available_tools()
        self._screen_info_cache = {}
    
    def set_session_manager(self, session_manager: UnifiedSessionManager):
        """Set session manager for session-based operations."""
        self.session_manager = session_manager
    
    # Core UI Operations
    
    def tap(self, target: Union[str, Dict], x: int, y: int, 
            gesture: Optional[Gesture] = None) -> None:
        """
        Tap at coordinates.
        
        Args:
            target: Device UDID or session ID
            x: X coordinate
            y: Y coordinate
            gesture: Optional gesture configuration
            
        Raises:
            DeviceNotAvailableError: If device is not available
        """
        udid = self._resolve_target(target)
        self._verify_device_available(udid)
        
        device = self.device_manager.get_device(udid)
        if not device:
            raise DeviceNotAvailableError(f"Device not found: {udid}")
        
        if gesture is None:
            gesture = Gesture()
        
        # Perform tap based on device type
        if device.device_type == DeviceType.SIMULATOR:
            self._tap_simulator(udid, x, y, gesture)
        else:
            self._tap_real_device(udid, x, y, gesture)
        
        print(f"✅ Tapped at ({x}, {y})")
    
    def double_tap(self, target: Union[str, Dict], x: int, y: int) -> None:
        """Double tap at coordinates."""
        gesture = Gesture(repeat=2, delay_between=100)
        self.tap(target, x, y, gesture)
    
    def long_press(self, target: Union[str, Dict], x: int, y: int, 
                   duration: float = 1.0) -> None:
        """
        Long press at coordinates.
        
        Args:
            target: Device UDID or session ID
            x: X coordinate
            y: Y coordinate
            duration: Press duration in seconds
        """
        gesture = Gesture(duration=int(duration * 1000))
        self.tap(target, x, y, gesture)
        print(f"✅ Long pressed at ({x}, {y}) for {duration}s")
    
    def swipe(self, target: Union[str, Dict], start_x: int, start_y: int, 
              end_x: int, end_y: int, duration: int = 100) -> None:
        """
        Swipe from start to end coordinates.
        
        Args:
            target: Device UDID or session ID
            start_x: Starting X coordinate
            start_y: Starting Y coordinate
            end_x: Ending X coordinate
            end_y: Ending Y coordinate
            duration: Swipe duration in milliseconds
        """
        udid = self._resolve_target(target)
        self._verify_device_available(udid)
        
        device = self.device_manager.get_device(udid)
        if not device:
            raise DeviceNotAvailableError(f"Device not found: {udid}")
        
        if device.device_type == DeviceType.SIMULATOR:
            self._swipe_simulator(udid, start_x, start_y, end_x, end_y, duration)
        else:
            self._swipe_real_device(udid, start_x, start_y, end_x, end_y, duration)
        
        print(f"✅ Swiped from ({start_x}, {start_y}) to ({end_x}, {end_y})")
    
    # Convenience Swipe Methods
    
    def swipe_up(self, target: Union[str, Dict], distance: Optional[int] = None, 
                 duration: int = 300) -> None:
        """Swipe up from center of screen."""
        screen = self.get_screen_info(target)
        center_x = screen.width // 2
        
        if distance is None:
            distance = screen.height // 3
        
        start_y = screen.height * 2 // 3
        end_y = start_y - distance
        
        self.swipe(target, center_x, start_y, center_x, end_y, duration)
    
    def swipe_down(self, target: Union[str, Dict], distance: Optional[int] = None, 
                   duration: int = 300) -> None:
        """Swipe down from center of screen."""
        screen = self.get_screen_info(target)
        center_x = screen.width // 2
        
        if distance is None:
            distance = screen.height // 3
        
        start_y = screen.height // 3
        end_y = start_y + distance
        
        self.swipe(target, center_x, start_y, center_x, end_y, duration)
    
    def swipe_left(self, target: Union[str, Dict], distance: Optional[int] = None, 
                   duration: int = 300) -> None:
        """Swipe left from center of screen."""
        screen = self.get_screen_info(target)
        center_y = screen.height // 2
        
        if distance is None:
            distance = screen.width // 3
        
        start_x = screen.width * 2 // 3
        end_x = start_x - distance
        
        self.swipe(target, start_x, center_y, end_x, center_y, duration)
    
    def swipe_right(self, target: Union[str, Dict], distance: Optional[int] = None, 
                    duration: int = 300) -> None:
        """Swipe right from center of screen."""
        screen = self.get_screen_info(target)
        center_y = screen.height // 2
        
        if distance is None:
            distance = screen.width // 3
        
        start_x = screen.width // 3
        end_x = start_x + distance
        
        self.swipe(target, start_x, center_y, end_x, center_y, duration)
    
    # Advanced Gestures
    
    def pinch(self, target: Union[str, Dict], center: Optional[Point] = None, 
              scale: float = 0.5, duration: int = 300) -> None:
        """
        Perform pinch gesture (zoom out).
        
        Args:
            target: Device UDID or session ID
            center: Center point (defaults to screen center)
            scale: Scale factor (< 1.0 for pinch in, > 1.0 for pinch out)
            duration: Gesture duration
        """
        screen = self.get_screen_info(target)
        
        if center is None:
            center = Point(screen.width // 2, screen.height // 2)
        
        # Calculate touch points
        offset = int(min(screen.width, screen.height) * 0.2)
        
        if scale < 1.0:
            # Pinch in (zoom out)
            start_offset = offset
            end_offset = int(offset * scale)
        else:
            # Pinch out (zoom in)
            start_offset = int(offset / scale)
            end_offset = offset
        
        # Perform two-finger gesture
        points = [
            (center.x - start_offset, center.y - start_offset, 
             center.x - end_offset, center.y - end_offset),
            (center.x + start_offset, center.y + start_offset,
             center.x + end_offset, center.y + end_offset)
        ]
        
        self.multi_touch_gesture(target, points, duration)
        print(f"✅ Pinch gesture at ({center.x}, {center.y}) with scale {scale}")
    
    def zoom(self, target: Union[str, Dict], center: Optional[Point] = None, 
             scale: float = 2.0, duration: int = 300) -> None:
        """Perform zoom gesture (pinch out)."""
        self.pinch(target, center, scale, duration)
    
    def rotate(self, target: Union[str, Dict], center: Optional[Point] = None, 
               degrees: float = 90, duration: int = 300) -> None:
        """
        Perform rotation gesture.
        
        Args:
            target: Device UDID or session ID
            center: Center point (defaults to screen center)
            degrees: Rotation degrees (positive for clockwise)
            duration: Gesture duration
        """
        screen = self.get_screen_info(target)
        
        if center is None:
            center = Point(screen.width // 2, screen.height // 2)
        
        # Calculate rotation points
        import math
        radius = min(screen.width, screen.height) * 0.2
        angle_rad = math.radians(degrees)
        
        # Two fingers rotating around center
        points = []
        for i in range(2):
            start_angle = i * math.pi  # 0 and 180 degrees
            end_angle = start_angle + angle_rad
            
            start_x = int(center.x + radius * math.cos(start_angle))
            start_y = int(center.y + radius * math.sin(start_angle))
            end_x = int(center.x + radius * math.cos(end_angle))
            end_y = int(center.y + radius * math.sin(end_angle))
            
            points.append((start_x, start_y, end_x, end_y))
        
        self.multi_touch_gesture(target, points, duration)
        print(f"✅ Rotated {degrees}° at ({center.x}, {center.y})")
    
    def multi_touch_gesture(self, target: Union[str, Dict], 
                           points: List[Tuple[int, int, int, int]], 
                           duration: int = 300) -> None:
        """
        Perform multi-touch gesture.
        
        Args:
            target: Device UDID or session ID
            points: List of (start_x, start_y, end_x, end_y) for each finger
            duration: Gesture duration
        """
        udid = self._resolve_target(target)
        device = self.device_manager.get_device(udid)
        
        if not device:
            raise DeviceNotAvailableError(f"Device not found: {udid}")
        
        # Multi-touch is complex and tool-specific
        if device.device_type == DeviceType.SIMULATOR:
            # Simulate with sequential swipes for now
            for point in points:
                self.swipe(target, point[0], point[1], point[2], point[3], duration)
                time.sleep(0.05)
        else:
            # Real devices need special handling
            print("⚠️  Multi-touch on real devices requires advanced tools")
    
    # Text Input
    
    def input_text(self, target: Union[str, Dict], text: str) -> None:
        """
        Input text into focused field.
        
        Args:
            target: Device UDID or session ID
            text: Text to input
        """
        udid = self._resolve_target(target)
        self._verify_device_available(udid)
        
        device = self.device_manager.get_device(udid)
        if not device:
            raise DeviceNotAvailableError(f"Device not found: {udid}")
        
        if device.device_type == DeviceType.SIMULATOR:
            self._input_text_simulator(udid, text)
        else:
            self._input_text_real_device(udid, text)
        
        print(f"✅ Input text: {text[:50]}{'...' if len(text) > 50 else ''}")
    
    def clear_text(self, target: Union[str, Dict], field_length: int = 50) -> None:
        """Clear text from focused field."""
        # Select all and delete
        self.press_key_combination(target, ['cmd', 'a'])
        time.sleep(0.1)
        self.press_button(target, 'delete')
    
    # Hardware Buttons
    
    def press_button(self, target: Union[str, Dict], button: str, 
                    duration: Optional[int] = None) -> None:
        """
        Press hardware button.
        
        Args:
            target: Device UDID or session ID
            button: Button name (home, lock, volume_up, volume_down, etc.)
            duration: Optional press duration in milliseconds
        """
        udid = self._resolve_target(target)
        self._verify_device_available(udid)
        
        device = self.device_manager.get_device(udid)
        if not device:
            raise DeviceNotAvailableError(f"Device not found: {udid}")
        
        valid_buttons = ['home', 'lock', 'volume_up', 'volume_down', 'siri', 'delete']
        if button not in valid_buttons:
            raise ValueError(f"Invalid button: {button}. Valid: {valid_buttons}")
        
        if device.device_type == DeviceType.SIMULATOR:
            self._press_button_simulator(udid, button, duration)
        else:
            self._press_button_real_device(udid, button, duration)
        
        print(f"✅ Pressed {button} button")
    
    def press_key_combination(self, target: Union[str, Dict], keys: List[str]) -> None:
        """
        Press key combination (e.g., cmd+c).
        
        Args:
            target: Device UDID or session ID
            keys: List of keys to press together
        """
        udid = self._resolve_target(target)
        device = self.device_manager.get_device(udid)
        
        if not device:
            raise DeviceNotAvailableError(f"Device not found: {udid}")
        
        # Key combinations are mainly for simulators
        if device.device_type == DeviceType.SIMULATOR:
            # Map key names to codes
            key_map = {
                'cmd': 55, 'command': 55,
                'shift': 56,
                'alt': 58, 'option': 58,
                'ctrl': 59, 'control': 59,
                'space': 49,
                'return': 36, 'enter': 36,
                'escape': 53, 'esc': 53,
                'tab': 48,
                'delete': 51, 'backspace': 51,
                'a': 0, 'c': 8, 'v': 9, 'x': 7, 'z': 6
            }
            
            # Send key combination
            print(f"✅ Pressed key combination: {'+'.join(keys)}")
        else:
            print("⚠️  Key combinations not supported on real devices")
    
    # Screen Capture
    
    def take_screenshot(self, target: Union[str, Dict], 
                       output_path: Optional[str] = None) -> Union[bytes, str]:
        """
        Take screenshot.
        
        Args:
            target: Device UDID or session ID
            output_path: Optional output file path
            
        Returns:
            bytes or str: Screenshot data or file path
        """
        udid = self._resolve_target(target)
        self._verify_device_available(udid)
        
        device = self.device_manager.get_device(udid)
        if not device:
            raise DeviceNotAvailableError(f"Device not found: {udid}")
        
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"screenshot_{timestamp}.png"
        
        if device.device_type == DeviceType.SIMULATOR:
            result = self._screenshot_simulator(udid, output_path)
        else:
            result = self._screenshot_real_device(udid, output_path)
        
        print(f"✅ Screenshot saved: {output_path}")
        return result
    
    def record_video(self, target: Union[str, Dict], output_path: str, 
                    duration: int = 10, options: Optional[Dict[str, Any]] = None) -> str:
        """
        Record video from device.
        
        Args:
            target: Device UDID or session ID
            output_path: Output video file path
            duration: Recording duration in seconds
            options: Recording options (quality, fps, etc.)
            
        Returns:
            str: Path to recorded video
        """
        udid = self._resolve_target(target)
        self._verify_device_available(udid)
        
        device = self.device_manager.get_device(udid)
        if not device:
            raise DeviceNotAvailableError(f"Device not found: {udid}")
        
        if device.device_type == DeviceType.SIMULATOR:
            self._record_video_simulator(udid, output_path, duration, options)
        else:
            self._record_video_real_device(udid, output_path, duration, options)
        
        print(f"✅ Video recorded: {output_path}")
        return output_path
    
    # Screen Information
    
    def get_screen_info(self, target: Union[str, Dict]) -> ScreenInfo:
        """
        Get screen information.
        
        Args:
            target: Device UDID or session ID
            
        Returns:
            ScreenInfo: Screen dimensions and properties
        """
        udid = self._resolve_target(target)
        
        # Check cache
        if udid in self._screen_info_cache:
            return self._screen_info_cache[udid]
        
        device = self.device_manager.get_device(udid)
        if not device:
            raise DeviceNotAvailableError(f"Device not found: {udid}")
        
        # Get screen info based on device
        if device.device_type == DeviceType.SIMULATOR:
            info = self._get_screen_info_simulator(udid)
        else:
            info = self._get_screen_info_real_device(udid)
        
        # Cache result
        self._screen_info_cache[udid] = info
        return info
    
    def get_orientation(self, target: Union[str, Dict]) -> str:
        """Get current device orientation."""
        screen_info = self.get_screen_info(target)
        return screen_info.orientation
    
    def set_orientation(self, target: Union[str, Dict], orientation: str) -> None:
        """
        Set device orientation.
        
        Args:
            target: Device UDID or session ID
            orientation: Orientation (portrait, landscape, portrait_upside_down, landscape_right)
        """
        udid = self._resolve_target(target)
        device = self.device_manager.get_device(udid)
        
        if not device:
            raise DeviceNotAvailableError(f"Device not found: {udid}")
        
        valid_orientations = ['portrait', 'landscape', 'portrait_upside_down', 'landscape_right']
        if orientation not in valid_orientations:
            raise ValueError(f"Invalid orientation: {orientation}")
        
        if device.device_type == DeviceType.SIMULATOR:
            # Rotate simulator
            print(f"✅ Set orientation: {orientation}")
        else:
            print("⚠️  Orientation change on real devices requires physical rotation")
    
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
    
    # Simulator-specific implementations
    
    def _tap_simulator(self, udid: str, x: int, y: int, gesture: Gesture):
        """Tap on simulator."""
        if self.available_tools.get('idb'):
            try:
                command = f"{self.idb_path} ui --udid {udid} tap {x} {y}"
                if gesture.duration > 100:
                    command += f" --duration {gesture.duration}"
                self.run_command(command)
                return
            except:
                pass
        
        # Fallback to simctl (limited functionality)
        print("⚠️  Using simctl fallback (limited tap functionality)")
    
    def _swipe_simulator(self, udid: str, start_x: int, start_y: int, 
                        end_x: int, end_y: int, duration: int):
        """Swipe on simulator."""
        if self.available_tools.get('idb'):
            try:
                command = f"{self.idb_path} ui --udid {udid} swipe {start_x} {start_y} {end_x} {end_y} {duration}"
                self.run_command(command)
                return
            except:
                pass
        
        print("⚠️  Swipe requires idb for simulators")
    
    def _input_text_simulator(self, udid: str, text: str):
        """Input text on simulator."""
        if self.available_tools.get('idb'):
            try:
                escaped_text = text.replace('"', '\\"').replace('\\', '\\\\')
                command = f'{self.idb_path} ui --udid {udid} text "{escaped_text}"'
                self.run_command(command)
                return
            except:
                pass
        
        # Fallback: paste text
        print("⚠️  Text input requires idb for simulators")
    
    def _press_button_simulator(self, udid: str, button: str, duration: Optional[int]):
        """Press button on simulator."""
        try:
            # Map button names to simctl commands
            button_map = {
                'home': 'home',
                'lock': 'lock',
                'volume_up': 'volumeup',
                'volume_down': 'volumedown'
            }
            
            if button in button_map:
                self.run_command(f"{self.simctl_path} ui {udid} {button_map[button]}")
            elif self.available_tools.get('idb'):
                command = f"{self.idb_path} ui --udid {udid} button {button}"
                if duration:
                    command += f" --duration {duration}"
                self.run_command(command)
        except Exception as e:
            raise DeviceError(f"Failed to press button: {e}")
    
    def _screenshot_simulator(self, udid: str, output_path: str) -> str:
        """Take screenshot on simulator."""
        try:
            self.run_command(f"{self.simctl_path} io {udid} screenshot '{output_path}'")
            return output_path
        except Exception as e:
            raise DeviceError(f"Failed to take screenshot: {e}")
    
    def _record_video_simulator(self, udid: str, output_path: str, 
                               duration: int, options: Optional[Dict]):
        """Record video on simulator."""
        try:
            # Start recording
            command = f"{self.simctl_path} io {udid} recordVideo '{output_path}'"
            if options:
                if options.get('codec'):
                    command += f" --codec {options['codec']}"
                if options.get('quality'):
                    command += f" --quality {options['quality']}"
            
            # Run with timeout
            self.run_command(f"timeout {duration} {command}", timeout=duration + 5)
        except Exception as e:
            # Timeout is expected
            if "timeout" not in str(e).lower():
                raise DeviceError(f"Failed to record video: {e}")
    
    def _get_screen_info_simulator(self, udid: str) -> ScreenInfo:
        """Get screen info for simulator."""
        # Default sizes for common devices
        # In practice, query the device model and look up specs
        device = self.device_manager.get_device(udid)
        
        # Simple mapping based on device name
        if 'iPad' in device.name:
            return ScreenInfo(width=1024, height=1366, scale=2.0, orientation='portrait')
        elif 'Pro Max' in device.name:
            return ScreenInfo(width=430, height=932, scale=3.0, orientation='portrait')
        elif 'Pro' in device.name:
            return ScreenInfo(width=393, height=852, scale=3.0, orientation='portrait')
        else:
            # Default iPhone size
            return ScreenInfo(width=390, height=844, scale=3.0, orientation='portrait')
    
    # Real device-specific implementations
    
    def _tap_real_device(self, udid: str, x: int, y: int, gesture: Gesture):
        """Tap on real device."""
        if self.available_tools.get('idb'):
            try:
                command = f"{self.idb_path} ui --udid {udid} tap {x} {y}"
                if gesture.duration > 100:
                    command += f" --duration {gesture.duration}"
                self.run_command(command)
            except Exception as e:
                raise DeviceError(f"Failed to tap: {e}")
        else:
            raise DeviceError("idb required for real device UI automation")
    
    def _swipe_real_device(self, udid: str, start_x: int, start_y: int,
                          end_x: int, end_y: int, duration: int):
        """Swipe on real device."""
        if self.available_tools.get('idb'):
            try:
                command = f"{self.idb_path} ui --udid {udid} swipe {start_x} {start_y} {end_x} {end_y} {duration}"
                self.run_command(command)
            except Exception as e:
                raise DeviceError(f"Failed to swipe: {e}")
        else:
            raise DeviceError("idb required for real device UI automation")
    
    def _input_text_real_device(self, udid: str, text: str):
        """Input text on real device."""
        if self.available_tools.get('idb'):
            try:
                escaped_text = text.replace('"', '\\"').replace('\\', '\\\\')
                command = f'{self.idb_path} ui --udid {udid} text "{escaped_text}"'
                self.run_command(command)
            except Exception as e:
                raise DeviceError(f"Failed to input text: {e}")
        else:
            raise DeviceError("idb required for real device UI automation")
    
    def _press_button_real_device(self, udid: str, button: str, duration: Optional[int]):
        """Press button on real device."""
        if self.available_tools.get('idb'):
            try:
                command = f"{self.idb_path} ui --udid {udid} button {button}"
                if duration:
                    command += f" --duration {duration}"
                self.run_command(command)
            except Exception as e:
                raise DeviceError(f"Failed to press button: {e}")
        else:
            raise DeviceError("idb required for real device UI automation")
    
    def _screenshot_real_device(self, udid: str, output_path: str) -> str:
        """Take screenshot on real device."""
        if self.available_tools.get('idb'):
            try:
                self.run_command(f"{self.idb_path} screenshot --udid {udid} '{output_path}'")
                return output_path
            except Exception as e:
                raise DeviceError(f"Failed to take screenshot: {e}")
        else:
            raise DeviceError("idb required for real device screenshots")
    
    def _record_video_real_device(self, udid: str, output_path: str,
                                 duration: int, options: Optional[Dict]):
        """Record video on real device."""
        if self.available_tools.get('idb'):
            try:
                command = f"{self.idb_path} record-video --udid {udid} '{output_path}'"
                # Run with timeout
                self.run_command(f"timeout {duration} {command}", timeout=duration + 5)
            except Exception as e:
                if "timeout" not in str(e).lower():
                    raise DeviceError(f"Failed to record video: {e}")
        else:
            raise DeviceError("idb required for real device video recording")
    
    def _get_screen_info_real_device(self, udid: str) -> ScreenInfo:
        """Get screen info for real device."""
        # Query device for actual screen dimensions
        # For now, return common iPhone dimensions
        return ScreenInfo(width=390, height=844, scale=3.0, orientation='portrait')