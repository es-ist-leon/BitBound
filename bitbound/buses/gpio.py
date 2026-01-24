"""
GPIO Bus implementation.
"""

from typing import List, Optional, Callable
from enum import Enum
from .base import Bus, BusConfig, BusType, BusFactory


class PinMode(Enum):
    """GPIO pin modes."""
    INPUT = "INPUT"
    OUTPUT = "OUTPUT"
    INPUT_PULLUP = "INPUT_PULLUP"
    INPUT_PULLDOWN = "INPUT_PULLDOWN"
    OPEN_DRAIN = "OPEN_DRAIN"


class PinEdge(Enum):
    """GPIO interrupt edge triggers."""
    RISING = "RISING"
    FALLING = "FALLING"
    BOTH = "BOTH"


class GPIOPin:
    """
    Represents a single GPIO pin.
    
    Example:
        pin = GPIOPin(13, PinMode.OUTPUT)
        pin.on()
        pin.off()
        pin.toggle()
        
        # Input with callback
        button = GPIOPin(14, PinMode.INPUT_PULLUP)
        button.on_change(lambda: print("Button pressed!"))
    """
    
    def __init__(self, pin_number: int, mode: PinMode = PinMode.INPUT):
        """
        Initialize a GPIO pin.
        
        Args:
            pin_number: Physical pin number
            mode: Pin mode (INPUT, OUTPUT, etc.)
        """
        self._pin_number = pin_number
        self._mode = mode
        self._pin = None
        self._simulation_mode = True
        self._sim_value = 0
        self._callbacks: List[Callable] = []
        
        self._init_pin()
    
    def _init_pin(self) -> None:
        """Initialize the hardware pin."""
        try:
            from machine import Pin
            
            mode_map = {
                PinMode.INPUT: Pin.IN,
                PinMode.OUTPUT: Pin.OUT,
                PinMode.INPUT_PULLUP: Pin.IN,
                PinMode.INPUT_PULLDOWN: Pin.IN,
                PinMode.OPEN_DRAIN: Pin.OPEN_DRAIN,
            }
            
            pull_map = {
                PinMode.INPUT_PULLUP: Pin.PULL_UP,
                PinMode.INPUT_PULLDOWN: Pin.PULL_DOWN,
            }
            
            pull = pull_map.get(self._mode)
            if pull:
                self._pin = Pin(self._pin_number, mode_map[self._mode], pull)
            else:
                self._pin = Pin(self._pin_number, mode_map[self._mode])
            
            self._simulation_mode = False
        except ImportError:
            self._simulation_mode = True
    
    @property
    def value(self) -> int:
        """Get the current pin value (0 or 1)."""
        if self._simulation_mode:
            return self._sim_value
        return self._pin.value()
    
    @value.setter
    def value(self, val: int) -> None:
        """Set the pin value (0 or 1)."""
        if self._simulation_mode:
            old_value = self._sim_value
            self._sim_value = 1 if val else 0
            if old_value != self._sim_value:
                self._trigger_callbacks()
        else:
            self._pin.value(1 if val else 0)
    
    def on(self) -> None:
        """Set pin high."""
        self.value = 1
    
    def off(self) -> None:
        """Set pin low."""
        self.value = 0
    
    def toggle(self) -> None:
        """Toggle pin value."""
        self.value = 0 if self.value else 1
    
    def read(self) -> int:
        """Read pin value."""
        return self.value
    
    def write(self, val: int) -> None:
        """Write pin value."""
        self.value = val
    
    def on_change(self, callback: Callable, edge: PinEdge = PinEdge.BOTH) -> None:
        """
        Register a callback for pin changes.
        
        Args:
            callback: Function to call on change
            edge: Edge trigger type
        """
        self._callbacks.append(callback)
        
        if not self._simulation_mode and self._pin:
            try:
                from machine import Pin
                edge_map = {
                    PinEdge.RISING: Pin.IRQ_RISING,
                    PinEdge.FALLING: Pin.IRQ_FALLING,
                    PinEdge.BOTH: Pin.IRQ_RISING | Pin.IRQ_FALLING,
                }
                self._pin.irq(trigger=edge_map[edge], handler=lambda p: callback())
            except Exception:
                pass
    
    def _trigger_callbacks(self) -> None:
        """Trigger all registered callbacks."""
        for callback in self._callbacks:
            try:
                callback()
            except Exception as e:
                print(f"GPIO callback error: {e}")
    
    def __repr__(self) -> str:
        mode = "SIM" if self._simulation_mode else "HW"
        return f"<GPIOPin [{mode}] {self._pin_number} {self._mode.value}={self.value}>"


class GPIOBus(Bus):
    """
    GPIO bus for managing multiple pins.
    
    Example:
        gpio = GPIOBus()
        gpio.init()
        
        # Get a pin
        led = gpio.pin(13, PinMode.OUTPUT)
        led.on()
        
        # PWM output
        gpio.pwm(14, freq=1000, duty=50)
    """
    
    def __init__(self):
        """Initialize GPIO bus."""
        config = BusConfig(bus_type=BusType.GPIO)
        super().__init__(config)
        
        self._pins: dict = {}
        self._pwm_channels: dict = {}
    
    def init(self) -> bool:
        """Initialize GPIO."""
        self._initialized = True
        return True
    
    def deinit(self) -> None:
        """Deinitialize GPIO."""
        for pin in self._pins.values():
            if hasattr(pin, '_pin') and pin._pin:
                try:
                    pin._pin.irq(handler=None)
                except Exception:
                    pass
        
        for pwm in self._pwm_channels.values():
            try:
                pwm.deinit()
            except Exception:
                pass
        
        self._pins.clear()
        self._pwm_channels.clear()
        self._initialized = False
    
    def scan(self) -> List[int]:
        """Return list of configured pin numbers."""
        return list(self._pins.keys())
    
    def pin(self, pin_number: int, mode: PinMode = PinMode.INPUT) -> GPIOPin:
        """
        Get or create a GPIO pin.
        
        Args:
            pin_number: Pin number
            mode: Pin mode
            
        Returns:
            GPIOPin instance
        """
        if pin_number not in self._pins:
            self._pins[pin_number] = GPIOPin(pin_number, mode)
        return self._pins[pin_number]
    
    def output(self, pin_number: int) -> GPIOPin:
        """Create an output pin."""
        return self.pin(pin_number, PinMode.OUTPUT)
    
    def input(self, pin_number: int, pullup: bool = False) -> GPIOPin:
        """Create an input pin."""
        mode = PinMode.INPUT_PULLUP if pullup else PinMode.INPUT
        return self.pin(pin_number, mode)
    
    def pwm(
        self,
        pin_number: int,
        freq: int = 1000,
        duty: int = 50
    ) -> None:
        """
        Set up PWM on a pin.
        
        Args:
            pin_number: Pin number
            freq: Frequency in Hz
            duty: Duty cycle (0-100)
        """
        try:
            from machine import Pin, PWM
            
            if pin_number not in self._pwm_channels:
                pin = Pin(pin_number)
                self._pwm_channels[pin_number] = PWM(pin)
            
            pwm = self._pwm_channels[pin_number]
            pwm.freq(freq)
            # Convert 0-100 to 0-65535 (16-bit)
            pwm.duty_u16(int(duty * 65535 / 100))
            
        except ImportError:
            # Simulation mode
            pass
    
    def set_pwm_duty(self, pin_number: int, duty: int) -> None:
        """Set PWM duty cycle (0-100)."""
        if pin_number in self._pwm_channels:
            self._pwm_channels[pin_number].duty_u16(int(duty * 65535 / 100))
    
    def stop_pwm(self, pin_number: int) -> None:
        """Stop PWM on a pin."""
        if pin_number in self._pwm_channels:
            self._pwm_channels[pin_number].deinit()
            del self._pwm_channels[pin_number]
    
    def __repr__(self) -> str:
        return f"<GPIOBus pins={list(self._pins.keys())}>"


# Register with factory
BusFactory.register("GPIO", GPIOBus)
