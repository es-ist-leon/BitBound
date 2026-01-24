"""
Base Device class for all hardware components.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Set, TYPE_CHECKING
import time
import threading

from .event import Event, EventHandler, EventLoop, EventType, get_event_loop
from .expression import parse_expression


@dataclass
class DeviceInfo:
    """Information about a hardware device."""
    device_type: str
    name: str
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    address: Optional[int] = None
    bus_type: Optional[str] = None
    capabilities: List[str] = field(default_factory=list)
    properties: Dict[str, str] = field(default_factory=dict)


class Device(ABC):
    """
    Base class for all hardware devices.
    
    Provides a unified interface for sensors, actuators, and displays
    with declarative event handling and property access.
    
    Example:
        class TemperatureSensor(Device):
            @property
            def temperature(self):
                return self._read_temperature()
            
            @property 
            def humidity(self):
                return self._read_humidity()
    """
    
    def __init__(
        self,
        bus: Any,
        address: Optional[int] = None,
        name: Optional[str] = None
    ):
        """
        Initialize a device.
        
        Args:
            bus: The bus interface (I2C, SPI, GPIO, etc.)
            address: Device address on the bus
            name: Human-readable name for the device
        """
        self._bus = bus
        self._address = address
        self._name = name or self.__class__.__name__
        self._event_loop: Optional[EventLoop] = None
        self._handlers: List[EventHandler] = []
        self._connected = False
        self._last_read: Dict[str, Any] = {}
        self._last_read_time: float = 0
        self._cache_duration: float = 0.1  # 100ms cache
        self._lock = threading.Lock()
        
        # Auto-detect properties
        self._properties: Set[str] = self._detect_properties()
    
    def _detect_properties(self) -> Set[str]:
        """Detect readable properties on this device."""
        props = set()
        for name in dir(self.__class__):
            if not name.startswith('_'):
                attr = getattr(self.__class__, name, None)
                if isinstance(attr, property):
                    props.add(name)
        return props
    
    @property
    def properties(self) -> Set[str]:
        """Get the set of readable properties."""
        return self._properties
    
    @property
    def name(self) -> str:
        """Get the device name."""
        return self._name
    
    @property
    def address(self) -> Optional[int]:
        """Get the device address."""
        return self._address
    
    @property
    def connected(self) -> bool:
        """Check if device is connected."""
        return self._connected
    
    @abstractmethod
    def connect(self) -> bool:
        """
        Connect to the device.
        
        Returns:
            True if connection successful
        """
        pass
    
    @abstractmethod
    def disconnect(self) -> None:
        """Disconnect from the device."""
        pass
    
    @abstractmethod
    def get_info(self) -> DeviceInfo:
        """Get device information."""
        pass
    
    def read_all(self) -> Dict[str, Any]:
        """
        Read all properties from the device.
        
        Returns:
            Dictionary of property names to values
        """
        with self._lock:
            # Check cache
            now = time.time()
            if now - self._last_read_time < self._cache_duration:
                return self._last_read.copy()
            
            # Read fresh values
            values = {}
            for prop in self._properties:
                try:
                    values[prop] = getattr(self, prop)
                except Exception as e:
                    values[prop] = None
            
            self._last_read = values
            self._last_read_time = now
            return values.copy()
    
    def __getitem__(self, key: str) -> Any:
        """Allow dictionary-style access to properties."""
        if key in self._properties:
            return getattr(self, key)
        raise KeyError(f"Unknown property: {key}")
    
    # Event handling methods
    
    def on_threshold(
        self,
        expression: str,
        callback: Callable[[Event], None],
        debounce_ms: int = 0
    ) -> EventHandler:
        """
        Register a callback when a threshold condition is met.
        
        Args:
            expression: Condition like "temperature > 25°C"
            callback: Function to call when condition is met
            debounce_ms: Minimum time between callbacks
            
        Returns:
            The EventHandler (can be used to disable later)
            
        Example:
            sensor.on_threshold("temperature > 25°C", lambda e: fan.on())
        """
        if self._event_loop is None:
            self._event_loop = get_event_loop()
        
        handler = self._event_loop.on_threshold(
            expression, self, callback, debounce_ms
        )
        self._handlers.append(handler)
        return handler
    
    def on_change(
        self,
        property_name: str,
        callback: Callable[[Event], None],
        debounce_ms: int = 0
    ) -> EventHandler:
        """
        Register a callback when a property value changes.
        
        Args:
            property_name: Name of property to monitor
            callback: Function to call when value changes
            debounce_ms: Minimum time between callbacks
            
        Returns:
            The EventHandler
            
        Example:
            button.on_change("pressed", lambda e: handle_press(e))
        """
        if self._event_loop is None:
            self._event_loop = get_event_loop()
        
        handler = self._event_loop.on_change(
            property_name, self, callback, debounce_ms
        )
        self._handlers.append(handler)
        return handler
    
    def on_interval(
        self,
        interval_ms: int,
        callback: Callable[[Event], None]
    ) -> EventHandler:
        """
        Register a callback at regular intervals.
        
        Args:
            interval_ms: Interval in milliseconds
            callback: Function to call at each interval
            
        Returns:
            The EventHandler
        """
        if self._event_loop is None:
            self._event_loop = get_event_loop()
        
        handler = self._event_loop.on_interval(interval_ms, self, callback)
        self._handlers.append(handler)
        return handler
    
    def remove_handler(self, handler: EventHandler) -> None:
        """Remove an event handler."""
        if handler in self._handlers:
            self._handlers.remove(handler)
        if self._event_loop:
            self._event_loop.remove_handler(handler)
    
    def remove_all_handlers(self) -> None:
        """Remove all event handlers for this device."""
        for handler in self._handlers:
            if self._event_loop:
                self._event_loop.remove_handler(handler)
        self._handlers.clear()
    
    def __repr__(self) -> str:
        addr_str = f"@0x{self._address:02X}" if self._address else ""
        return f"<{self.__class__.__name__} {self._name}{addr_str}>"


class Sensor(Device):
    """Base class for sensor devices."""
    
    def get_info(self) -> DeviceInfo:
        return DeviceInfo(
            device_type="sensor",
            name=self._name,
            address=self._address,
            capabilities=list(self._properties)
        )


class Actuator(Device):
    """Base class for actuator devices (motors, relays, etc.)."""
    
    def get_info(self) -> DeviceInfo:
        return DeviceInfo(
            device_type="actuator",
            name=self._name,
            address=self._address,
            capabilities=list(self._properties)
        )
    
    @abstractmethod
    def on(self) -> None:
        """Turn on the actuator."""
        pass
    
    @abstractmethod
    def off(self) -> None:
        """Turn off the actuator."""
        pass


class Display(Device):
    """Base class for display devices."""
    
    def get_info(self) -> DeviceInfo:
        return DeviceInfo(
            device_type="display",
            name=self._name,
            address=self._address,
            capabilities=list(self._properties)
        )
    
    @abstractmethod
    def clear(self) -> None:
        """Clear the display."""
        pass
    
    @abstractmethod
    def write(self, text: str, x: int = 0, y: int = 0) -> None:
        """Write text to the display."""
        pass
