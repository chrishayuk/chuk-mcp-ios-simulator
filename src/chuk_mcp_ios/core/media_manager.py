#!/usr/bin/env python3
# chuk_mcp_ios/core/media_manager.py
"""
Unified Media Manager for iOS Device Control

Handles media operations (photos, videos) and location services for both simulators and real devices.
"""

import os
import shutil
import tempfile
import json
import time
from typing import List, Optional, Union, Tuple, Dict, Any
from dataclasses import dataclass
from pathlib import Path
from datetime import datetime
import mimetypes

from .base import (
    MediaManagerInterface,
    CommandExecutor,
    DeviceType,
    DeviceNotAvailableError,
    DeviceError,
    detect_available_tools
)
from .device_manager import UnifiedDeviceManager
from .session_manager import UnifiedSessionManager

@dataclass
class Location:
    """Represents a geographic location."""
    latitude: float
    longitude: float
    altitude: Optional[float] = None
    name: Optional[str] = None
    
    def validate(self):
        """Validate location coordinates."""
        if not (-90 <= self.latitude <= 90):
            raise ValueError(f"Invalid latitude: {self.latitude}")
        if not (-180 <= self.longitude <= 180):
            raise ValueError(f"Invalid longitude: {self.longitude}")

@dataclass
class MediaFile:
    """Represents a media file."""
    path: str
    type: str  # photo, video, live_photo
    size: int
    created_at: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None

class UnifiedMediaManager(CommandExecutor, MediaManagerInterface):
    """
    Unified media manager supporting both iOS simulators and real devices.
    Handles photos, videos, and location services.
    """
    
    def __init__(self):
        super().__init__()
        self.device_manager = UnifiedDeviceManager()
        self.session_manager = None  # Optional session manager
        self.available_tools = detect_available_tools()
        
        # Predefined locations
        self.known_locations = {
            # US Cities
            'san francisco': Location(37.7749, -122.4194, name="San Francisco, CA"),
            'new york': Location(40.7128, -74.0060, name="New York, NY"),
            'los angeles': Location(34.0522, -118.2437, name="Los Angeles, CA"),
            'chicago': Location(41.8781, -87.6298, name="Chicago, IL"),
            'miami': Location(25.7617, -80.1918, name="Miami, FL"),
            'seattle': Location(47.6062, -122.3321, name="Seattle, WA"),
            'boston': Location(42.3601, -71.0589, name="Boston, MA"),
            'austin': Location(30.2672, -97.7431, name="Austin, TX"),
            'denver': Location(39.7392, -104.9903, name="Denver, CO"),
            'las vegas': Location(36.1699, -115.1398, name="Las Vegas, NV"),
            
            # International Cities
            'london': Location(51.5074, -0.1278, name="London, UK"),
            'paris': Location(48.8566, 2.3522, name="Paris, France"),
            'tokyo': Location(35.6762, 139.6503, name="Tokyo, Japan"),
            'sydney': Location(-33.8688, 151.2093, name="Sydney, Australia"),
            'beijing': Location(39.9042, 116.4074, name="Beijing, China"),
            'dubai': Location(25.2048, 55.2708, name="Dubai, UAE"),
            'singapore': Location(1.3521, 103.8198, name="Singapore"),
            'moscow': Location(55.7558, 37.6176, name="Moscow, Russia"),
            'toronto': Location(43.6532, -79.3832, name="Toronto, Canada"),
            'berlin': Location(52.5200, 13.4050, name="Berlin, Germany"),
            
            # Landmarks
            'apple park': Location(37.3348, -122.0090, name="Apple Park, Cupertino"),
            'golden gate bridge': Location(37.8199, -122.4783, name="Golden Gate Bridge"),
            'statue of liberty': Location(40.6892, -74.0445, name="Statue of Liberty"),
            'eiffel tower': Location(48.8584, 2.2945, name="Eiffel Tower"),
            'big ben': Location(51.5007, -0.1246, name="Big Ben"),
            'times square': Location(40.7580, -73.9855, name="Times Square"),
            'mount everest': Location(27.9881, 86.9250, 8848, name="Mount Everest"),
            'grand canyon': Location(36.1069, -112.1129, name="Grand Canyon"),
        }
        
        # Supported media formats
        self.supported_photo_formats = {'.jpg', '.jpeg', '.png', '.heic', '.heif', '.gif', '.bmp', '.tiff'}
        self.supported_video_formats = {'.mp4', '.mov', '.m4v', '.avi', '.mkv', '.3gp'}
        self.supported_formats = self.supported_photo_formats | self.supported_video_formats
    
    def set_session_manager(self, session_manager: UnifiedSessionManager):
        """Set session manager for session-based operations."""
        self.session_manager = session_manager
    
    # Media Operations
    
    def add_media(self, target: Union[str, Dict], media_paths: List[str],
                  albums: Optional[List[str]] = None) -> List[MediaFile]:
        """
        Add media files to device.
        
        Args:
            target: Device UDID or session ID
            media_paths: List of media file paths
            albums: Optional album names to add media to
            
        Returns:
            List[MediaFile]: Added media files
            
        Raises:
            DeviceNotAvailableError: If device is not available
            FileNotFoundError: If media files don't exist
        """
        udid = self._resolve_target(target)
        self._verify_device_available(udid)
        
        # Validate and analyze media files
        media_files = self._validate_media_files(media_paths)
        
        if not media_files:
            print("No valid media files to add")
            return []
        
        device = self.device_manager.get_device(udid)
        if not device:
            raise DeviceNotAvailableError(f"Device not found: {udid}")
        
        # Add media based on device type
        if device.device_type == DeviceType.SIMULATOR:
            added_files = self._add_media_simulator(udid, media_files)
        else:
            added_files = self._add_media_real_device(udid, media_files)
        
        # Report results
        photo_count = len([f for f in added_files if f.type == 'photo'])
        video_count = len([f for f in added_files if f.type == 'video'])
        
        print(f"✅ Added {len(added_files)} media files:")
        if photo_count:
            print(f"   📸 {photo_count} photos")
        if video_count:
            print(f"   🎬 {video_count} videos")
        
        return added_files
    
    def add_photos(self, target: Union[str, Dict], photo_paths: List[str]) -> List[MediaFile]:
        """Add only photo files."""
        valid_paths = [p for p in photo_paths 
                      if os.path.splitext(p)[1].lower() in self.supported_photo_formats]
        return self.add_media(target, valid_paths)
    
    def add_videos(self, target: Union[str, Dict], video_paths: List[str]) -> List[MediaFile]:
        """Add only video files."""
        valid_paths = [p for p in video_paths 
                      if os.path.splitext(p)[1].lower() in self.supported_video_formats]
        return self.add_media(target, valid_paths)
    
    def create_sample_media(self, output_dir: Union[str, Path], 
                           photo_count: int = 3, video_count: int = 0) -> List[str]:
        """
        Create sample media files for testing.
        
        Args:
            output_dir: Directory to create media files
            photo_count: Number of photos to create
            video_count: Number of videos to create (not implemented)
            
        Returns:
            List[str]: Created file paths
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        created_files = []
        
        try:
            from PIL import Image, ImageDraw, ImageFont
            import random
            
            for i in range(photo_count):
                # Create colorful test image
                width, height = 800, 600
                
                # Random gradient background
                image = Image.new('RGB', (width, height))
                draw = ImageDraw.Draw(image)
                
                # Create gradient
                for y in range(height):
                    r = int(255 * (y / height))
                    g = random.randint(100, 200)
                    b = random.randint(100, 255)
                    draw.line([(0, y), (width, y)], fill=(r, g, b))
                
                # Add text
                try:
                    font = ImageFont.load_default()
                    text = f"Test Photo {i+1}"
                    draw.text((width//2 - 50, height//2), text, fill='white', font=font)
                except:
                    draw.text((width//2 - 50, height//2), f"Test Photo {i+1}", fill='white')
                
                # Add shapes
                draw.rectangle([50, 50, 150, 150], outline='white', width=3)
                draw.ellipse([width-200, 50, width-50, 200], outline='white', width=3)
                
                # Add timestamp
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                draw.text((10, height-30), timestamp, fill='white')
                
                # Save
                filename = f"sample_photo_{i+1:02d}.png"
                filepath = output_dir / filename
                image.save(filepath)
                created_files.append(str(filepath))
                
            print(f"✅ Created {len(created_files)} sample media files in {output_dir}")
            
        except ImportError:
            print("⚠️  PIL not available, creating placeholder files")
            for i in range(photo_count):
                filename = f"sample_photo_{i+1:02d}.txt"
                filepath = output_dir / filename
                filepath.write_text(f"Placeholder photo {i+1}")
                created_files.append(str(filepath))
        
        return created_files
    
    # Location Operations
    
    def set_location(self, target: Union[str, Dict], latitude: float, longitude: float,
                    altitude: Optional[float] = None) -> None:
        """
        Set device location.
        
        Args:
            target: Device UDID or session ID
            latitude: Latitude coordinate (-90 to 90)
            longitude: Longitude coordinate (-180 to 180)
            altitude: Optional altitude in meters
            
        Raises:
            DeviceNotAvailableError: If device is not available
            ValueError: If coordinates are invalid
        """
        location = Location(latitude, longitude, altitude)
        location.validate()
        
        udid = self._resolve_target(target)
        self._verify_device_available(udid)
        
        device = self.device_manager.get_device(udid)
        if not device:
            raise DeviceNotAvailableError(f"Device not found: {udid}")
        
        # Check capability
        caps = self.device_manager.get_device_capabilities(udid)
        if not caps.get('can_simulate_location', False):
            raise DeviceError("Device doesn't support location simulation")
        
        # Set location based on device type
        if device.device_type == DeviceType.SIMULATOR:
            self._set_location_simulator(udid, location)
        else:
            self._set_location_real_device(udid, location)
        
        location_name = self._get_location_name(latitude, longitude)
        if location_name:
            print(f"✅ Location set to: {location_name}")
        else:
            print(f"✅ Location set to: {latitude}, {longitude}")
    
    def set_location_by_name(self, target: Union[str, Dict], location_name: str) -> None:
        """
        Set location by name.
        
        Args:
            target: Device UDID or session ID
            location_name: Name of known location
            
        Raises:
            ValueError: If location name is not recognized
        """
        location_key = location_name.lower().strip()
        
        if location_key in self.known_locations:
            location = self.known_locations[location_key]
            self.set_location(target, location.latitude, location.longitude, location.altitude)
        else:
            # Try to find partial match
            matches = [k for k in self.known_locations if location_key in k]
            if matches:
                location = self.known_locations[matches[0]]
                self.set_location(target, location.latitude, location.longitude, location.altitude)
            else:
                available = list(self.known_locations.keys())
                raise ValueError(f"Unknown location: {location_name}. Try one of: {', '.join(available[:10])}...")
    
    def clear_location(self, target: Union[str, Dict]) -> None:
        """Clear/reset device location."""
        # Set to default location (Apple Park)
        self.set_location(target, 37.3348, -122.0090)
        print("✅ Location reset to default")
    
    def simulate_route(self, target: Union[str, Dict], waypoints: List[Tuple[float, float]], 
                      speed_kmh: float = 50.0, interval: float = 1.0) -> None:
        """
        Simulate movement along a route.
        
        Args:
            target: Device UDID or session ID
            waypoints: List of (latitude, longitude) tuples
            speed_kmh: Speed in kilometers per hour
            interval: Update interval in seconds
        """
        if len(waypoints) < 2:
            raise ValueError("At least 2 waypoints required for route")
        
        print(f"🗺️  Starting route simulation with {len(waypoints)} waypoints at {speed_kmh} km/h")
        
        for i in range(len(waypoints) - 1):
            current = waypoints[i]
            next_point = waypoints[i + 1]
            
            # Calculate intermediate points based on speed
            distance = self._calculate_distance(current, next_point)
            travel_time = (distance / speed_kmh) * 3600  # seconds
            steps = int(travel_time / interval)
            
            if steps < 1:
                steps = 1
            
            for step in range(steps + 1):
                # Interpolate position
                ratio = step / steps
                lat = current[0] + (next_point[0] - current[0]) * ratio
                lng = current[1] + (next_point[1] - current[1]) * ratio
                
                self.set_location(target, lat, lng)
                
                if step < steps:
                    time.sleep(interval)
            
            print(f"   ✅ Reached waypoint {i+2}/{len(waypoints)}")
        
        print("✅ Route simulation completed")
    
    def simulate_city_tour(self, target: Union[str, Dict], city: str, 
                          duration_minutes: int = 10) -> None:
        """
        Simulate a tour around a city.
        
        Args:
            target: Device UDID or session ID
            city: City name
            duration_minutes: Tour duration
        """
        # Predefined city tours
        city_tours = {
            'san francisco': [
                (37.8199, -122.4783),  # Golden Gate Bridge
                (37.8027, -122.4188),  # Fisherman's Wharf
                (37.7956, -122.3937),  # Ferry Building
                (37.7749, -122.4194),  # Downtown
                (37.7614, -122.4356),  # Golden Gate Park
            ],
            'new york': [
                (40.6892, -74.0445),   # Statue of Liberty
                (40.7128, -74.0060),   # Downtown
                (40.7580, -73.9855),   # Times Square
                (40.7829, -73.9654),   # Central Park
                (40.7489, -73.9680),   # Empire State Building
            ],
            'paris': [
                (48.8584, 2.2945),     # Eiffel Tower
                (48.8606, 2.3376),     # Louvre
                (48.8530, 2.3499),     # Notre-Dame
                (48.8738, 2.2950),     # Arc de Triomphe
                (48.8867, 2.3431),     # Sacré-Cœur
            ]
        }
        
        city_key = city.lower()
        if city_key not in city_tours:
            available = list(city_tours.keys())
            raise ValueError(f"No tour available for {city}. Try: {', '.join(available)}")
        
        waypoints = city_tours[city_key]
        
        # Calculate speed to complete tour in given duration
        total_distance = sum(self._calculate_distance(waypoints[i], waypoints[i+1]) 
                           for i in range(len(waypoints)-1))
        speed_kmh = (total_distance / duration_minutes) * 60
        
        print(f"🏙️  Starting {city.title()} city tour ({duration_minutes} minutes)")
        self.simulate_route(target, waypoints, speed_kmh)
    
    def get_current_location(self, target: Union[str, Dict]) -> Optional[Location]:
        """
        Get current device location (if available).
        
        Note: This may not be supported on all devices/tools.
        """
        udid = self._resolve_target(target)
        device = self.device_manager.get_device(udid)
        
        if not device:
            return None
        
        # This would require querying the device for current location
        # For now, return None as most tools don't support reading location
        print("⚠️  Reading current location not supported by most tools")
        return None
    
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
    
    def _validate_media_files(self, media_paths: List[str]) -> List[MediaFile]:
        """Validate and analyze media files."""
        media_files = []
        
        for path in media_paths:
            if not os.path.exists(path):
                print(f"⚠️  File not found: {path}")
                continue
            
            # Get file info
            ext = os.path.splitext(path)[1].lower()
            if ext not in self.supported_formats:
                print(f"⚠️  Unsupported format: {path}")
                continue
            
            # Determine media type
            if ext in self.supported_photo_formats:
                media_type = 'photo'
            else:
                media_type = 'video'
            
            # Get file metadata
            stat = os.stat(path)
            media_file = MediaFile(
                path=path,
                type=media_type,
                size=stat.st_size,
                created_at=datetime.fromtimestamp(stat.st_mtime)
            )
            
            media_files.append(media_file)
        
        return media_files
    
    def _calculate_distance(self, point1: Tuple[float, float], 
                           point2: Tuple[float, float]) -> float:
        """Calculate distance between two points in kilometers."""
        import math
        
        lat1, lon1 = point1
        lat2, lon2 = point2
        
        # Haversine formula
        R = 6371  # Earth's radius in kilometers
        
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * \
            math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        
        return R * c
    
    def _get_location_name(self, latitude: float, longitude: float) -> Optional[str]:
        """Get human-readable name for coordinates."""
        # Check if close to any known location
        for name, location in self.known_locations.items():
            distance = self._calculate_distance((latitude, longitude), 
                                              (location.latitude, location.longitude))
            if distance < 1.0:  # Within 1km
                return location.name or name.title()
        
        return None
    
    # Simulator-specific implementations
    
    def _add_media_simulator(self, udid: str, media_files: List[MediaFile]) -> List[MediaFile]:
        """Add media to simulator."""
        added_files = []
        
        # Use simctl addmedia
        try:
            file_paths = [f.path for f in media_files]
            paths_str = ' '.join([f"'{p}'" for p in file_paths])
            
            self.run_command(f"{self.simctl_path} addmedia {udid} {paths_str}")
            added_files = media_files
            
        except Exception as e:
            print(f"⚠️  Failed to add media via simctl: {e}")
            
            # Try alternative method via Photos app
            if self.available_tools.get('idb'):
                for media_file in media_files:
                    try:
                        self.run_command(f"{self.idb_path} add-media --udid {udid} '{media_file.path}'")
                        added_files.append(media_file)
                    except Exception as e:
                        print(f"⚠️  Failed to add {media_file.path}: {e}")
        
        return added_files
    
    def _set_location_simulator(self, udid: str, location: Location):
        """Set location on simulator."""
        try:
            # simctl expects format: latitude,longitude
            self.run_command(f"{self.simctl_path} location {udid} set {location.latitude},{location.longitude}")
        except Exception as e:
            raise DeviceError(f"Failed to set location: {e}")
    
    # Real device-specific implementations
    
    def _add_media_real_device(self, udid: str, media_files: List[MediaFile]) -> List[MediaFile]:
        """Add media to real device."""
        if not self.available_tools.get('idb'):
            raise DeviceError("idb required for adding media to real devices")
        
        added_files = []
        
        for media_file in media_files:
            try:
                self.run_command(f"{self.idb_path} add-media --udid {udid} '{media_file.path}'")
                added_files.append(media_file)
            except Exception as e:
                print(f"⚠️  Failed to add {media_file.path}: {e}")
        
        return added_files
    
    def _set_location_real_device(self, udid: str, location: Location):
        """Set location on real device."""
        if not self.available_tools.get('idb'):
            raise DeviceError("idb required for location simulation on real devices")
        
        try:
            self.run_command(f"{self.idb_path} set_location --udid {udid} {location.latitude} {location.longitude}")
        except Exception as e:
            raise DeviceError(f"Failed to set location: {e}")
    
    # Export functionality
    
    def export_locations(self, output_file: Path):
        """Export all known locations to file."""
        data = {
            'export_time': datetime.now().isoformat(),
            'total_locations': len(self.known_locations),
            'locations': {}
        }
        
        for name, location in self.known_locations.items():
            data['locations'][name] = {
                'latitude': location.latitude,
                'longitude': location.longitude,
                'altitude': location.altitude,
                'display_name': location.name or name.title()
            }
        
        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"📄 Exported {len(self.known_locations)} locations to {output_file}")