"""
Event system for reactive hardware programming.

Provides event loops, callbacks, and threshold-based triggers.
"""

import time
import threading
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Set
from enum import Enum
from .expression import Expression, parse_expression


class EventType(Enum):
    """Types of events that can be triggered."""
    THRESHOLD = "threshold"
    CHANGE = "change"
    INTERVAL = "interval"
    EDGE_RISING = "edge_rising"
    EDGE_FALLING = "edge_falling"
    ERROR = "error"
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"


@dataclass
class Event:
    """Represents a hardware event."""
    event_type: EventType
    source: Any
    property_name: Optional[str] = None
    old_value: Any = None
    new_value: Any = None
    timestamp: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __repr__(self) -> str:
        return f"Event({self.event_type.value}, {self.source}, {self.property_name}={self.new_value})"


@dataclass
class EventHandler:
    """A registered event handler."""
    callback: Callable
    event_type: EventType
    expression: Optional[Expression] = None
    property_name: Optional[str] = None
    interval: Optional[float] = None
    debounce_ms: int = 0
    last_triggered: float = 0
    enabled: bool = True
    
    def should_trigger(self, event: Event, values: Dict[str, Any]) -> bool:
        """Check if this handler should be triggered for the given event."""
        if not self.enabled:
            return False
        
        # Check debounce
        if self.debounce_ms > 0:
            elapsed = (time.time() - self.last_triggered) * 1000
            if elapsed < self.debounce_ms:
                return False
        
        # Check event type
        if event.event_type != self.event_type:
            return False
        
        # Check property name if specified
        if self.property_name and event.property_name != self.property_name:
            return False
        
        # Check expression if specified
        if self.expression:
            return self.expression.evaluate(values)
        
        return True
    
    def trigger(self, event: Event) -> None:
        """Execute the callback."""
        self.last_triggered = time.time()
        try:
            self.callback(event)
        except Exception as e:
            print(f"Error in event handler: {e}")


class EventLoop:
    """
    Main event loop for processing hardware events.
    
    Example:
        loop = EventLoop()
        loop.start()
        
        # Register handlers
        loop.on_threshold("temperature > 25°C", sensor, handle_temp)
        
        # Run forever
        loop.run_forever()
    """
    
    def __init__(self, poll_interval_ms: int = 100):
        """
        Initialize the event loop.
        
        Args:
            poll_interval_ms: How often to poll devices for changes (milliseconds)
        """
        self.poll_interval = poll_interval_ms / 1000.0
        self.handlers: List[EventHandler] = []
        self.devices: List[Any] = []
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
        self._device_values: Dict[int, Dict[str, Any]] = {}
    
    def register_device(self, device: Any) -> None:
        """Register a device for polling."""
        with self._lock:
            if device not in self.devices:
                self.devices.append(device)
                self._device_values[id(device)] = {}
    
    def unregister_device(self, device: Any) -> None:
        """Unregister a device from polling."""
        with self._lock:
            if device in self.devices:
                self.devices.remove(device)
                self._device_values.pop(id(device), None)
    
    def add_handler(self, handler: EventHandler) -> None:
        """Add an event handler."""
        with self._lock:
            self.handlers.append(handler)
    
    def remove_handler(self, handler: EventHandler) -> None:
        """Remove an event handler."""
        with self._lock:
            if handler in self.handlers:
                self.handlers.remove(handler)
    
    def on_threshold(
        self,
        expression: str,
        device: Any,
        callback: Callable,
        debounce_ms: int = 0
    ) -> EventHandler:
        """
        Register a threshold-based event handler.
        
        Args:
            expression: Condition like "temperature > 25°C"
            device: The device to monitor
            callback: Function to call when condition is met
            debounce_ms: Minimum time between triggers
            
        Returns:
            The registered EventHandler
        """
        parsed_expr = parse_expression(expression)
        handler = EventHandler(
            callback=callback,
            event_type=EventType.THRESHOLD,
            expression=parsed_expr,
            debounce_ms=debounce_ms
        )
        
        self.register_device(device)
        self.add_handler(handler)
        return handler
    
    def on_change(
        self,
        property_name: str,
        device: Any,
        callback: Callable,
        debounce_ms: int = 0
    ) -> EventHandler:
        """
        Register a change-based event handler.
        
        Args:
            property_name: Property to monitor for changes
            device: The device to monitor
            callback: Function to call when value changes
            debounce_ms: Minimum time between triggers
            
        Returns:
            The registered EventHandler
        """
        handler = EventHandler(
            callback=callback,
            event_type=EventType.CHANGE,
            property_name=property_name,
            debounce_ms=debounce_ms
        )
        
        self.register_device(device)
        self.add_handler(handler)
        return handler
    
    def on_interval(
        self,
        interval_ms: int,
        device: Any,
        callback: Callable
    ) -> EventHandler:
        """
        Register an interval-based event handler.
        
        Args:
            interval_ms: Interval in milliseconds
            device: The device to read
            callback: Function to call at each interval
            
        Returns:
            The registered EventHandler
        """
        handler = EventHandler(
            callback=callback,
            event_type=EventType.INTERVAL,
            interval=interval_ms / 1000.0
        )
        
        self.register_device(device)
        self.add_handler(handler)
        return handler
    
    def start(self) -> None:
        """Start the event loop in a background thread."""
        if self._running:
            return
        
        self._running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
    
    def stop(self) -> None:
        """Stop the event loop."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=1.0)
            self._thread = None
    
    def run_forever(self) -> None:
        """Run the event loop in the current thread (blocking)."""
        self._running = True
        self._run_loop()
    
    def _run_loop(self) -> None:
        """Internal event loop."""
        while self._running:
            try:
                self._poll_devices()
                time.sleep(self.poll_interval)
            except Exception as e:
                print(f"Event loop error: {e}")
    
    def _poll_devices(self) -> None:
        """Poll all registered devices and check for events."""
        with self._lock:
            devices = list(self.devices)
            handlers = list(self.handlers)
        
        for device in devices:
            try:
                # Get current values from device
                current_values = self._read_device(device)
                device_id = id(device)
                old_values = self._device_values.get(device_id, {})
                
                # Check for changes and trigger events
                for prop_name, new_value in current_values.items():
                    old_value = old_values.get(prop_name)
                    
                    # Create change event if value changed
                    if old_value != new_value:
                        event = Event(
                            event_type=EventType.CHANGE,
                            source=device,
                            property_name=prop_name,
                            old_value=old_value,
                            new_value=new_value
                        )
                        self._dispatch_event(event, current_values, handlers)
                    
                    # Create threshold event for checking conditions
                    event = Event(
                        event_type=EventType.THRESHOLD,
                        source=device,
                        property_name=prop_name,
                        new_value=new_value
                    )
                    self._dispatch_event(event, current_values, handlers)
                
                # Store current values
                self._device_values[device_id] = current_values
                
            except Exception as e:
                # Create error event
                event = Event(
                    event_type=EventType.ERROR,
                    source=device,
                    metadata={"error": str(e)}
                )
                self._dispatch_event(event, {}, handlers)
    
    def _read_device(self, device: Any) -> Dict[str, Any]:
        """Read all properties from a device."""
        if hasattr(device, 'read_all'):
            return device.read_all()
        elif hasattr(device, 'properties'):
            return {prop: getattr(device, prop, None) for prop in device.properties}
        else:
            return {}
    
    def _dispatch_event(
        self,
        event: Event,
        values: Dict[str, Any],
        handlers: List[EventHandler]
    ) -> None:
        """Dispatch an event to all matching handlers."""
        for handler in handlers:
            if handler.should_trigger(event, values):
                handler.trigger(event)


# Global event loop instance
_global_loop: Optional[EventLoop] = None


def get_event_loop() -> EventLoop:
    """Get or create the global event loop."""
    global _global_loop
    if _global_loop is None:
        _global_loop = EventLoop()
    return _global_loop


def set_event_loop(loop: EventLoop) -> None:
    """Set the global event loop."""
    global _global_loop
    _global_loop = loop
