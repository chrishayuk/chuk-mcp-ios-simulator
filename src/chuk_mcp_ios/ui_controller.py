#!/usr/bin/env python3
# chuk_mcp/ui_controller.py
"""
UI Controller Module
Handles user interface interactions including touch, gestures, and input.
"""

import os
import time
from typing import List, Optional, Union, Tuple
from ios_simulator_base import (
    UIControllerInterface,
    CommandExecutor,
    SimulatorNotBootedError
)

class UIController(CommandExecutor, UIControllerInterface):
    """Manages UI interactions and gestures for iOS simulator."""
    
    def __init__(self):
        super().__init__()
        self.verify_idb_availability()
    
    def tap(self, udid: str, x: int, y: int) -> None:
        """
        Tap at specific coordinates.
        
        Args:
            udid: Simulator UDID
            x: X coordinate
            y: Y coordinate
            
        Raises:
            SimulatorNotBootedError: If simulator is not running
        """
        self._verify_simulator_booted(udid)
        
        try:
            self.run_command(f"{self.idb_path} ui --udid {udid} tap {x} {y}")
            print(f"Tapped at coordinates ({x}, {y})")
        except Exception as e:
            raise Exception(f"Failed to tap at ({x}, {y}): {str(e)}")
    
    def double_tap(self, udid: str, x: int, y: int) -> None:
        """
        Double tap at specific coordinates.
        
        Args:
            udid: Simulator UDID
            x: X coordinate
            y: Y coordinate
        """
        self.tap(udid, x, y)
        time.sleep(0.1)  # Brief delay between taps
        self.tap(udid, x, y)
    
    def long_press(self, udid: str, x: int, y: int, duration: float = 1.0) -> None:
        """
        Long press at specific coordinates.
        
        Args:
            udid: Simulator UDID
            x: X coordinate
            y: Y coordinate
            duration: Press duration in seconds
        """
        self._verify_simulator_booted(udid)
        
        try:
            duration_ms = int(duration * 1000)
            self.run_command(f"{self.idb_path} ui --udid {udid} tap {x} {y} --duration {duration_ms}")
            print(f"Long pressed at coordinates ({x}, {y}) for {duration}s")
        except Exception as e:
            raise Exception(f"Failed to long press at ({x}, {y}): {str(e)}")
    
    def swipe(self, udid: str, start_x: int, start_y: int, end_x: int, end_y: int, duration: int = 100) -> None:
        """
        Swipe from start coordinates to end coordinates.
        
        Args:
            udid: Simulator UDID
            start_x: Starting X coordinate
            start_y: Starting Y coordinate
            end_x: Ending X coordinate
            end_y: Ending Y coordinate
            duration: Swipe duration in milliseconds
            
        Raises:
            SimulatorNotBootedError: If simulator is not running
        """
        self._verify_simulator_booted(udid)
        
        try:
            self.run_command(f"{self.idb_path} ui --udid {udid} swipe {start_x} {start_y} {end_x} {end_y} {duration}")
            print(f"Swiped from ({start_x}, {start_y}) to ({end_x}, {end_y})")
        except Exception as e:
            raise Exception(f"Failed to swipe: {str(e)}")
    
    def swipe_up(self, udid: str, x: int = 200, distance: int = 300, duration: int = 100) -> None:
        """Swipe up from a point."""
        start_y = 600  # Adjust based on device
        end_y = start_y - distance
        self.swipe(udid, x, start_y, x, end_y, duration)
    
    def swipe_down(self, udid: str, x: int = 200, distance: int = 300, duration: int = 100) -> None:
        """Swipe down from a point."""
        start_y = 200  # Adjust based on device
        end_y = start_y + distance
        self.swipe(udid, x, start_y, x, end_y, duration)
    
    def swipe_left(self, udid: str, y: int = 400, distance: int = 300, duration: int = 100) -> None:
        """Swipe left from a point."""
        start_x = 600  # Adjust based on device
        end_x = start_x - distance
        self.swipe(udid, start_x, y, end_x, y, duration)
    
    def swipe_right(self, udid: str, y: int = 400, distance: int = 300, duration: int = 100) -> None:
        """Swipe right from a point."""
        start_x = 100  # Adjust based on device
        end_x = start_x + distance
        self.swipe(udid, start_x, y, end_x, y, duration)
    
    def pinch(self, udid: str, center_x: int, center_y: int, scale: float = 0.5) -> None:
        """
        Perform pinch gesture (zoom out).
        
        Args:
            udid: Simulator UDID
            center_x: Center X coordinate
            center_y: Center Y coordinate
            scale: Scale factor (< 1.0 for pinch in, > 1.0 for pinch out)
        """
        # Calculate touch points for pinch
        offset = int(100 * scale)
        
        # Two finger pinch - simulate with two swipes
        self.swipe(udid, center_x - offset, center_y - offset, center_x - offset//2, center_y - offset//2, 200)
        time.sleep(0.1)
        self.swipe(udid, center_x + offset, center_y + offset, center_x + offset//2, center_y + offset//2, 200)
    
    def zoom(self, udid: str, center_x: int, center_y: int, scale: float = 2.0) -> None:
        """
        Perform zoom gesture (pinch out).
        
        Args:
            udid: Simulator UDID
            center_x: Center X coordinate
            center_y: Center Y coordinate
            scale: Scale factor (> 1.0 for zoom in)
        """
        self.pinch(udid, center_x, center_y, scale)
    
    def input_text(self, udid: str, text: str) -> None:
        """
        Input text into the currently focused text field.
        
        Args:
            udid: Simulator UDID
            text: Text to input
            
        Raises:
            SimulatorNotBootedError: If simulator is not running
        """
        self._verify_simulator_booted(udid)
        
        try:
            # Escape special characters
            escaped_text = text.replace('"', '\\"').replace('\\', '\\\\')
            self.run_command(f'{self.idb_path} ui --udid {udid} text "{escaped_text}"')
            print(f"Input text: {text}")
        except Exception as e:
            raise Exception(f"Failed to input text: {str(e)}")
    
    def clear_text(self, udid: str) -> None:
        """Clear text from currently focused text field."""
        # Select all and delete
        self.press_key_combination(udid, ['cmd', 'a'])
        time.sleep(0.1)
        self.press_key(udid, 8)  # Delete key
    
    def press_button(self, udid: str, button: str, duration: Optional[int] = None) -> None:
        """
        Press a hardware button.
        
        Args:
            udid: Simulator UDID
            button: Button name (home, lock, volume_up, volume_down, etc.)
            duration: Optional press duration in milliseconds
            
        Raises:
            SimulatorNotBootedError: If simulator is not running
        """
        self._verify_simulator_booted(udid)
        
        valid_buttons = ['home', 'lock', 'volume_up', 'volume_down', 'siri']
        if button not in valid_buttons:
            raise ValueError(f"Invalid button: {button}. Valid buttons: {valid_buttons}")
        
        try:
            command = f"{self.idb_path} ui --udid {udid} button {button}"
            if duration:
                command += f" --duration {duration}"
            
            self.run_command(command)
            print(f"Pressed {button} button")
        except Exception as e:
            raise Exception(f"Failed to press {button} button: {str(e)}")
    
    def press_key(self, udid: str, key_code: int, duration: Optional[int] = None) -> None:
        """
        Press a key by key code.
        
        Args:
            udid: Simulator UDID
            key_code: Key code to press
            duration: Optional press duration in milliseconds
            
        Raises:
            SimulatorNotBootedError: If simulator is not running
        """
        self._verify_simulator_booted(udid)
        
        try:
            command = f"{self.idb_path} ui --udid {udid} key {key_code}"
            if duration:
                command += f" --duration {duration}"
            
            self.run_command(command)
            print(f"Pressed key code: {key_code}")
        except Exception as e:
            raise Exception(f"Failed to press key {key_code}: {str(e)}")
    
    def press_key_sequence(self, udid: str, key_codes: List[int]) -> None:
        """
        Press a sequence of keys.
        
        Args:
            udid: Simulator UDID
            key_codes: List of key codes to press in sequence
            
        Raises:
            SimulatorNotBootedError: If simulator is not running
        """
        self._verify_simulator_booted(udid)
        
        try:
            key_codes_str = ' '.join(map(str, key_codes))
            self.run_command(f"{self.idb_path} ui --udid {udid} key-sequence {key_codes_str}")
            print(f"Pressed key sequence: {key_codes}")
        except Exception as e:
            raise Exception(f"Failed to press key sequence: {str(e)}")
    
    def press_key_combination(self, udid: str, keys: List[str]) -> None:
        """
        Press a combination of keys (e.g., cmd+c).
        
        Args:
            udid: Simulator UDID
            keys: List of key names to press simultaneously
        """
        # Map common key names to key codes
        key_map = {
            'cmd': 55,
            'shift': 56,
            'alt': 58,
            'ctrl': 59,
            'space': 49,
            'return': 36,
            'escape': 53,
            'tab': 48,
            'delete': 51,
            'backspace': 51,
            'a': 0, 'b': 11, 'c': 8, 'd': 2, 'e': 14, 'f': 3, 'g': 5, 'h': 4,
            'i': 34, 'j': 38, 'k': 40, 'l': 37, 'm': 46, 'n': 45, 'o': 31,
            'p': 35, 'q': 12, 'r': 15, 's': 1, 't': 17, 'u': 32, 'v': 9,
            'w': 13, 'x': 7, 'y': 16, 'z': 6
        }
        
        key_codes = []
        for key in keys:
            if key.lower() in key_map:
                key_codes.append(key_map[key.lower()])
            else:
                raise ValueError(f"Unknown key: {key}")
        
        self.press_key_sequence(udid, key_codes)
    
    def take_screenshot(self, udid: str, output_path: Optional[str] = None) -> Union[bytes, str]:
        """
        Take a screenshot of the simulator.
        
        Args:
            udid: Simulator UDID
            output_path: Optional output file path
            
        Returns:
            Union[bytes, str]: Screenshot data as bytes or file path
            
        Raises:
            SimulatorNotBootedError: If simulator is not running
        """
        self._verify_simulator_booted(udid)
        
        temp_path = output_path or f"screenshot_{int(time.time())}.png"
        
        try:
            self.run_command(f"{self.idb_path} screenshot --udid {udid} '{temp_path}'")
            print(f"Screenshot saved to: {temp_path}")
            
            if output_path:
                return output_path
            else:
                # Read and return bytes, then cleanup
                with open(temp_path, 'rb') as f:
                    buffer = f.read()
                os.unlink(temp_path)
                return buffer
        except Exception as e:
            raise Exception(f"Failed to take screenshot: {str(e)}")
    
    def record_video(self, udid: str, output_path: str, duration: int = 10) -> str:
        """
        Record video from the simulator.
        
        Args:
            udid: Simulator UDID
            output_path: Output video file path
            duration: Recording duration in seconds
            
        Returns:
            str: Path to recorded video
        """
        self._verify_simulator_booted(udid)
        
        try:
            # Use timeout to limit recording duration
            self.run_command(f"timeout {duration} {self.idb_path} record-video --udid {udid} '{output_path}'", timeout=duration + 5)
            print(f"Video recorded to: {output_path}")
            return output_path
        except Exception as e:
            # Timeout is expected for video recording
            if "timeout" in str(e).lower():
                print(f"Video recording completed: {output_path}")
                return output_path
            raise Exception(f"Failed to record video: {str(e)}")
    
    def get_screen_size(self, udid: str) -> Tuple[int, int]:
        """
        Get the screen size of the simulator.
        
        Args:
            udid: Simulator UDID
            
        Returns:
            Tuple[int, int]: Screen width and height
        """
        # This is a simplified implementation
        # In practice, you might query the device capabilities
        device_sizes = {
            'iPhone': (375, 812),
            'iPad': (768, 1024)
        }
        
        # Default to iPhone size
        return device_sizes.get('iPhone', (375, 812))
    
    def wait_for_element(self, udid: str, element_id: str, timeout: int = 10) -> bool:
        """
        Wait for a UI element to appear (simplified implementation).
        
        Args:
            udid: Simulator UDID
            element_id: Element identifier
            timeout: Timeout in seconds
            
        Returns:
            bool: True if element appeared within timeout
        """
        # This would need accessibility inspection tools
        # For now, just wait and return True
        time.sleep(min(timeout, 2))
        return True
    
    def _verify_simulator_booted(self, udid: str) -> None:
        """Verify that simulator is booted."""
        from simulator_manager import SimulatorManager
        sim_manager = SimulatorManager()
        if not sim_manager.is_simulator_booted(udid):
            raise SimulatorNotBootedError(f"Simulator {udid} is not booted")