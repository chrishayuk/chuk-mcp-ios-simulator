#!/usr/bin/env python3
# src/chuk_mcp_ios/devices/__init__.py
"""
iOS Device implementations module.

Provides device-specific implementations for simulators and real devices.
"""

from .simulator import SimulatorManager, SimulatorDevice
from .real_device import RealDeviceManager, RealDevice
from .detector import DeviceDetector, UnifiedDevice

__all__ = [
    'SimulatorManager',
    'SimulatorDevice',
    'RealDeviceManager', 
    'RealDevice',
    'DeviceDetector',
    'UnifiedDevice'
]