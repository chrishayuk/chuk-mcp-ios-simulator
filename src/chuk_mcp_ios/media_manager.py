#!/usr/bin/env python3
#src/chuk_mcp_ios/media_manager.py
"""
Media Manager Module
Handles media operations including photo/video management and location services.
"""

import os
from typing import List, Optional, Tuple
from ios_simulator_base import (
    MediaManagerInterface,
    CommandExecutor,
    SimulatorNotBootedError
)

class MediaManager(CommandExecutor, MediaManagerInterface):
    """Manages media files and location services for iOS simulator."""
    
    def __init__(self):
        super().__init__()
        self.verify_idb_availability()
    
    def add_media(self, udid: str, media_paths: List[str]) -> None:
        """
        Add media files to the simulator's photo library.
        
        Args:
            udid: Simulator UDID
            media_paths: List of paths to media files
            
        Raises:
            SimulatorNotBootedError: If simulator is not running
            FileNotFoundError: If media files don't exist
        """
        self._verify_simulator_booted(udid)
        
        # Validate all files exist
        missing_files = [path for path in media_paths if not os.path.exists(path)]
        if missing_files:
            raise FileNotFoundError(f"Media files not found: {missing_files}")
        
        # Validate file types
        valid_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.mp4', '.mov', '.m4v', '.heic', '.heif'}
        invalid_files = []
        for path in media_paths:
            ext = os.path.splitext(path)[1].lower()
            if ext not in valid_extensions:
                invalid_files.append(path)
        
        if invalid_files:
            print(f"Warning: Unsupported file types: {invalid_files}")
            print(f"Supported types: {sorted(valid_extensions)}")
        
        try:
            # Escape file paths for shell command
            escaped_paths = [f"'{path}'" for path in media_paths]
            media_paths_str = ' '.join(escaped_paths)
            
            self.run_command(f"{self.idb_path} add-media --udid {udid} {media_paths_str}")
            print(f"Successfully added {len(media_paths)} media files to photo library")
            
            # List added files
            for path in media_paths:
                filename = os.path.basename(path)
                file_size = os.path.getsize(path)
                print(f"  ✅ {filename} ({self._format_file_size(file_size)})")
                
        except Exception as e:
            raise Exception(f"Failed to add media files: {str(e)}")
    
    def add_photos(self, udid: str, photo_paths: List[str]) -> None:
        """
        Add photo files specifically to the photo library.
        
        Args:
            udid: Simulator UDID
            photo_paths: List of paths to photo files
        """
        photo_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.heic', '.heif'}
        valid_photos = []
        
        for path in photo_paths:
            ext = os.path.splitext(path)[1].lower()
            if ext in photo_extensions:
                valid_photos.append(path)
            else:
                print(f"Skipping non-photo file: {path}")
        
        if valid_photos:
            self.add_media(udid, valid_photos)
        else:
            print("No valid photo files found")
    
    def add_videos(self, udid: str, video_paths: List[str]) -> None:
        """
        Add video files specifically to the photo library.
        
        Args:
            udid: Simulator UDID
            video_paths: List of paths to video files
        """
        video_extensions = {'.mp4', '.mov', '.m4v', '.avi', '.mkv'}
        valid_videos = []
        
        for path in video_paths:
            ext = os.path.splitext(path)[1].lower()
            if ext in video_extensions:
                valid_videos.append(path)
            else:
                print(f"Skipping non-video file: {path}")
        
        if valid_videos:
            self.add_media(udid, valid_videos)
        else:
            print("No valid video files found")
    
    def set_location(self, udid: str, latitude: float, longitude: float) -> None:
        """
        Set the location of the simulator.
        
        Args:
            udid: Simulator UDID
            latitude: Latitude coordinate (-90 to 90)
            longitude: Longitude coordinate (-180 to 180)
            
        Raises:
            SimulatorNotBootedError: If simulator is not running
            ValueError: If coordinates are invalid
        """
        self._verify_simulator_booted(udid)
        
        # Validate coordinates
        if not (-90 <= latitude <= 90):
            raise ValueError(f"Invalid latitude: {latitude}. Must be between -90 and 90")
        if not (-180 <= longitude <= 180):
            raise ValueError(f"Invalid longitude: {longitude}. Must be between -180 and 180")
        
        try:
            self.run_command(f"{self.idb_path} set_location --udid {udid} {latitude} {longitude}")
            print(f"Location set to: {latitude}, {longitude}")
            
            # Try to get location name for better UX
            location_name = self._get_location_name(latitude, longitude)
            if location_name:
                print(f"Location: {location_name}")
                
        except Exception as e:
            raise Exception(f"Failed to set location: {str(e)}")
    
    def set_location_by_name(self, udid: str, location_name: str) -> None:
        """
        Set location by city/place name (requires geocoding).
        
        Args:
            udid: Simulator UDID
            location_name: Name of the location (e.g., "New York", "London")
        """
        # Predefined locations for common places
        known_locations = {
            'new york': (40.7128, -74.0060),
            'london': (51.5074, -0.1278),
            'paris': (48.8566, 2.3522),
            'tokyo': (35.6762, 139.6503),
            'sydney': (-33.8688, 151.2093),
            'san francisco': (37.7749, -122.4194),
            'los angeles': (34.0522, -118.2437),
            'chicago': (41.8781, -87.6298),
            'miami': (25.7617, -80.1918),
            'seattle': (47.6062, -122.3321),
            'berlin': (52.5200, 13.4050),
            'madrid': (40.4168, -3.7038),
            'rome': (41.9028, 12.4964),
            'moscow': (55.7558, 37.6176),
            'beijing': (39.9042, 116.4074),
            'singapore': (1.3521, 103.8198),
            'dubai': (25.2048, 55.2708)
        }
        
        location_key = location_name.lower().strip()
        if location_key in known_locations:
            lat, lng = known_locations[location_key]
            self.set_location(udid, lat, lng)
        else:
            raise ValueError(f"Unknown location: {location_name}. Try using coordinates instead.")
    
    def clear_location(self, udid: str) -> None:
        """
        Clear/reset the simulator's location to default.
        
        Args:
            udid: Simulator UDID
        """
        try:
            # Set to Apple Park coordinates as default
            self.set_location(udid, 37.3348, -122.0090)
            print("Location reset to default (Apple Park)")
        except Exception as e:
            raise Exception(f"Failed to clear location: {str(e)}")
    
    def simulate_location_route(self, udid: str, waypoints: List[Tuple[float, float]], 
                               interval: float = 1.0) -> None:
        """
        Simulate movement along a route with multiple waypoints.
        
        Args:
            udid: Simulator UDID
            waypoints: List of (latitude, longitude) tuples
            interval: Time interval between waypoints in seconds
        """
        import time
        
        if len(waypoints) < 2:
            raise ValueError("At least 2 waypoints are required for a route")
        
        print(f"Starting location simulation with {len(waypoints)} waypoints...")
        
        for i, (lat, lng) in enumerate(waypoints):
            self.set_location(udid, lat, lng)
            print(f"Waypoint {i+1}/{len(waypoints)}: ({lat}, {lng})")
            
            if i < len(waypoints) - 1:  # Don't sleep after the last waypoint
                time.sleep(interval)
        
        print("Route simulation completed")
    
    def get_media_library_info(self, udid: str) -> dict:
        """
        Get information about the media library (simplified implementation).
        
        Args:
            udid: Simulator UDID
            
        Returns:
            dict: Media library information
        """
        # This is a simplified implementation
        # Real implementation would query the photo library database
        try:
            # Try to get some basic info about the simulator's photo library
            # This would require more sophisticated querying in practice
            return {
                "status": "available",
                "message": "Media library is accessible",
                "note": "Detailed media info requires additional implementation"
            }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }
    
    def create_sample_media(self, output_dir: str, count: int = 5) -> List[str]:
        """
        Create sample media files for testing.
        
        Args:
            output_dir: Directory to create sample files
            count: Number of sample files to create
            
        Returns:
            List[str]: Paths to created sample files
        """
        import random
        from PIL import Image, ImageDraw, ImageFont
        
        os.makedirs(output_dir, exist_ok=True)
        created_files = []
        
        for i in range(count):
            # Create a simple colored image
            width, height = 800, 600
            color = (
                random.randint(50, 255),
                random.randint(50, 255),
                random.randint(50, 255)
            )
            
            image = Image.new('RGB', (width, height), color)
            draw = ImageDraw.Draw(image)
            
            # Add some text
            try:
                # Try to use a default font
                font = ImageFont.load_default()
                text = f"Sample Image {i+1}"
                draw.text((width//2 - 50, height//2), text, fill='white', font=font)
            except:
                # Fallback if font loading fails
                draw.text((width//2 - 50, height//2), f"Sample {i+1}", fill='white')
            
            # Add some shapes
            draw.rectangle([50, 50, 150, 150], outline='white', width=3)
            draw.ellipse([width-200, height-200, width-50, height-50], outline='white', width=3)
            
            filename = f"sample_image_{i+1:02d}.png"
            filepath = os.path.join(output_dir, filename)
            image.save(filepath)
            created_files.append(filepath)
        
        print(f"Created {len(created_files)} sample images in {output_dir}")
        return created_files
    
    def _format_file_size(self, size_bytes: int) -> str:
        """Format file size in human readable format."""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"
    
    def _get_location_name(self, latitude: float, longitude: float) -> Optional[str]:
        """
        Try to get a human-readable location name from coordinates.
        This is a simplified implementation with common locations.
        """
        # Simple reverse geocoding for known locations
        known_locations = {
            (40.7128, -74.0060): "New York, NY",
            (51.5074, -0.1278): "London, UK",
            (48.8566, 2.3522): "Paris, France",
            (35.6762, 139.6503): "Tokyo, Japan",
            (37.7749, -122.4194): "San Francisco, CA",
            (37.3348, -122.0090): "Cupertino, CA (Apple Park)"
        }
        
        # Find closest known location within reasonable distance
        min_distance = float('inf')
        closest_location = None
        
        for (known_lat, known_lng), name in known_locations.items():
            distance = ((latitude - known_lat) ** 2 + (longitude - known_lng) ** 2) ** 0.5
            if distance < 0.1 and distance < min_distance:  # Within ~10km
                min_distance = distance
                closest_location = name
        
        return closest_location
    
    def _verify_simulator_booted(self, udid: str) -> None:
        """Verify that simulator is booted."""
        from simulator_manager import SimulatorManager
        sim_manager = SimulatorManager()
        if not sim_manager.is_simulator_booted(udid):
            raise SimulatorNotBootedError(f"Simulator {udid} is not booted")