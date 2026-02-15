"""
BitBound – High-Level Embedded Python Library

A declarative hardware abstraction layer that makes embedded development
as simple as working with modern web APIs.

Example:
    from bitbound import Hardware
    
    hardware = Hardware()
    sensor = hardware.attach("I2C", type="BME280")
    sensor.on_threshold("temperature > 25°C", trigger_fan)
"""

__version__ = "1.0.0"
__author__ = "BitBound Team"

from .hardware import Hardware
from .device import Device
from .event import Event, EventLoop
from .expression import Expression
from .units import Unit, parse_value
from .config import Config
from .power import PowerManager
from .ota import OTAManager

__all__ = [
    "Hardware",
    "Device",
    "Event",
    "EventLoop",
    "Expression",
    "Unit",
    "parse_value",
    "Config",
    "PowerManager",
    "OTAManager",
]
