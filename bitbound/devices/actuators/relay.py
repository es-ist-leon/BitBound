"""
Relay and Relay Board actuators.
"""

from typing import Any, Dict, List
from ...device import Actuator, DeviceInfo


class Relay(Actuator):
    """
    Single Relay actuator.
    
    Example:
        from bitbound import Hardware
        
        hw = Hardware()
        relay = hw.attach("GPIO", type="Relay", pin=5)
        
        relay.on()
        relay.off()
        relay.toggle()
        
        # Use as context manager
        with relay:
            # Relay is ON
            pass
        # Relay is OFF
    """
    
    def __init__(
        self,
        bus,
        pin: int,
        active_low: bool = True,
        name: str = "Relay"
    ):
        """
        Initialize relay.
        
        Args:
            bus: GPIO bus instance
            pin: Control pin
            active_low: True if relay is active on LOW signal
            name: Device name
        """
        super().__init__(bus, pin, name)
        
        self._pin = pin
        self._active_low = active_low
        self._gpio_pin = None
        self._state = False
    
    def connect(self) -> bool:
        """Connect to relay."""
        try:
            if hasattr(self._bus, 'output'):
                self._gpio_pin = self._bus.output(self._pin)
                self.off()  # Start in off state
            
            self._connected = True
            return True
        except Exception as e:
            print(f"Relay connect error: {e}")
            return False
    
    def disconnect(self) -> None:
        """Disconnect from relay."""
        self.off()
        self._connected = False
    
    def get_info(self) -> DeviceInfo:
        """Get device information."""
        return DeviceInfo(
            device_type="actuator",
            name=self._name,
            model="Relay",
            address=self._pin,
            bus_type="GPIO",
            capabilities=["on", "off", "toggle"]
        )
    
    def on(self) -> None:
        """Turn relay ON."""
        if self._gpio_pin:
            self._gpio_pin.value = 0 if self._active_low else 1
        self._state = True
    
    def off(self) -> None:
        """Turn relay OFF."""
        if self._gpio_pin:
            self._gpio_pin.value = 1 if self._active_low else 0
        self._state = False
    
    def toggle(self) -> None:
        """Toggle relay state."""
        if self._state:
            self.off()
        else:
            self.on()
    
    @property
    def state(self) -> bool:
        """Get current state."""
        return self._state
    
    @property
    def is_on(self) -> bool:
        """Check if relay is ON."""
        return self._state
    
    def read_all(self) -> Dict[str, Any]:
        """Read all values."""
        return {"state": self._state}
    
    def __enter__(self):
        """Context manager - turn ON."""
        self.on()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager - turn OFF."""
        self.off()
        return False


class RelayBoard(Actuator):
    """
    Multi-channel Relay Board.
    
    Example:
        from bitbound import Hardware
        
        hw = Hardware()
        board = hw.attach("GPIO", type="RelayBoard", pins=[5, 6, 7, 8])
        
        board.on(0)      # Turn on channel 0
        board.off(1)     # Turn off channel 1
        board.all_on()   # All channels on
        board.all_off()  # All channels off
    """
    
    def __init__(
        self,
        bus,
        pins: List[int],
        active_low: bool = True,
        name: str = "RelayBoard"
    ):
        """
        Initialize relay board.
        
        Args:
            bus: GPIO bus instance
            pins: List of control pins
            active_low: True if relays are active on LOW signal
            name: Device name
        """
        super().__init__(bus, None, name)
        
        self._pins = pins
        self._active_low = active_low
        self._relays: List[Relay] = []
        self._states: List[bool] = [False] * len(pins)
    
    def connect(self) -> bool:
        """Connect to relay board."""
        try:
            for i, pin in enumerate(self._pins):
                relay = Relay(self._bus, pin, self._active_low, f"Relay_{i}")
                relay.connect()
                self._relays.append(relay)
            
            self._connected = True
            return True
        except Exception as e:
            print(f"RelayBoard connect error: {e}")
            return False
    
    def disconnect(self) -> None:
        """Disconnect from relay board."""
        self.all_off()
        for relay in self._relays:
            relay.disconnect()
        self._connected = False
    
    def get_info(self) -> DeviceInfo:
        """Get device information."""
        return DeviceInfo(
            device_type="actuator",
            name=self._name,
            model="RelayBoard",
            bus_type="GPIO",
            capabilities=["on", "off", "toggle", "all_on", "all_off"],
            properties={"channels": len(self._pins)}
        )
    
    def on(self, channel: int = None) -> None:
        """Turn ON a channel or all channels."""
        if channel is None:
            self.all_on()
        elif 0 <= channel < len(self._relays):
            self._relays[channel].on()
            self._states[channel] = True
    
    def off(self, channel: int = None) -> None:
        """Turn OFF a channel or all channels."""
        if channel is None:
            self.all_off()
        elif 0 <= channel < len(self._relays):
            self._relays[channel].off()
            self._states[channel] = False
    
    def toggle(self, channel: int) -> None:
        """Toggle a channel."""
        if 0 <= channel < len(self._relays):
            self._relays[channel].toggle()
            self._states[channel] = not self._states[channel]
    
    def all_on(self) -> None:
        """Turn ON all channels."""
        for i, relay in enumerate(self._relays):
            relay.on()
            self._states[i] = True
    
    def all_off(self) -> None:
        """Turn OFF all channels."""
        for i, relay in enumerate(self._relays):
            relay.off()
            self._states[i] = False
    
    def set_pattern(self, pattern: List[bool]) -> None:
        """
        Set multiple channels at once.
        
        Args:
            pattern: List of boolean states
        """
        for i, state in enumerate(pattern):
            if i < len(self._relays):
                if state:
                    self.on(i)
                else:
                    self.off(i)
    
    @property
    def states(self) -> List[bool]:
        """Get states of all channels."""
        return self._states.copy()
    
    @property
    def channels(self) -> int:
        """Get number of channels."""
        return len(self._relays)
    
    def __getitem__(self, index: int) -> Relay:
        """Get a specific relay channel."""
        return self._relays[index]
    
    def read_all(self) -> Dict[str, Any]:
        """Read all values."""
        return {"states": self._states.copy()}
