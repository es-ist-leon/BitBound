"""
Main Hardware class for BitBound.

Provides a high-level interface for hardware interaction.
"""

from typing import Any, Dict, List, Optional, Type, Callable
import threading

from .buses.base import Bus, BusFactory, BusType
from .buses.i2c import I2CBus
from .buses.spi import SPIBus
from .buses.gpio import GPIOBus
from .buses.uart import UARTBus
from .buses.onewire import OneWireBus
from .device import Device
from .event import EventLoop, get_event_loop


# Device registry
DEVICE_REGISTRY: Dict[str, Dict[str, Type]] = {
    "sensors": {},
    "actuators": {},
    "displays": {},
}


def register_device(category: str, device_type: str, device_class: Type) -> None:
    """Register a device class."""
    if category not in DEVICE_REGISTRY:
        DEVICE_REGISTRY[category] = {}
    DEVICE_REGISTRY[category][device_type.upper()] = device_class


def _register_builtin_devices() -> None:
    """Register all built-in devices."""
    # Sensors
    from .devices.sensors import (
        BME280Sensor, DHTSensor, DHT11, DHT22,
        DS18B20Sensor, AnalogSensor, PIRSensor, MPU6050Sensor,
        BH1750Sensor
    )
    
    register_device("sensors", "BME280", BME280Sensor)
    register_device("sensors", "BMP280", BME280Sensor)
    register_device("sensors", "DHT", DHTSensor)
    register_device("sensors", "DHT11", DHT11)
    register_device("sensors", "DHT22", DHT22)
    register_device("sensors", "DS18B20", DS18B20Sensor)
    register_device("sensors", "ANALOG", AnalogSensor)
    register_device("sensors", "PIR", PIRSensor)
    register_device("sensors", "MPU6050", MPU6050Sensor)
    register_device("sensors", "BH1750", BH1750Sensor)
    
    # Actuators
    from .devices.actuators import (
        Relay, RelayBoard, DCMotor, ServoMotor, StepperMotor,
        LED, RGBLed, NeoPixel, Buzzer
    )
    
    register_device("actuators", "RELAY", Relay)
    register_device("actuators", "RELAYBOARD", RelayBoard)
    register_device("actuators", "DCMOTOR", DCMotor)
    register_device("actuators", "MOTOR", DCMotor)
    register_device("actuators", "SERVO", ServoMotor)
    register_device("actuators", "STEPPER", StepperMotor)
    register_device("actuators", "LED", LED)
    register_device("actuators", "RGB", RGBLed)
    register_device("actuators", "RGBLED", RGBLed)
    register_device("actuators", "NEOPIXEL", NeoPixel)
    register_device("actuators", "WS2812", NeoPixel)
    register_device("actuators", "BUZZER", Buzzer)
    register_device("actuators", "FAN", Relay)  # Fan is just a relay
    
    # Displays
    from .devices.displays import (
        LCD1602, LCD2004, SSD1306Display, SevenSegmentDisplay
    )
    
    register_device("displays", "LCD", LCD1602)
    register_device("displays", "LCD1602", LCD1602)
    register_device("displays", "LCD2004", LCD2004)
    register_device("displays", "SSD1306", SSD1306Display)
    register_device("displays", "OLED", SSD1306Display)
    register_device("displays", "7SEGMENT", SevenSegmentDisplay)
    register_device("displays", "SEGMENT", SevenSegmentDisplay)


# Register devices on import
_register_builtin_devices()


class Hardware:
    """
    High-level hardware abstraction layer.
    
    Provides a simple, declarative interface for working with hardware components.
    
    Example:
        from bitbound import Hardware
        
        # Create hardware manager
        hardware = Hardware()
        
        # Attach devices
        sensor = hardware.attach("I2C", type="BME280")
        led = hardware.attach("GPIO", type="LED", pin=2)
        fan = hardware.attach("GPIO", type="Relay", pin=5)
        
        # Use declarative events
        sensor.on_threshold("temperature > 25°C", lambda e: fan.on())
        sensor.on_threshold("temperature < 23°C", lambda e: fan.off())
        
        # Read sensor values
        print(f"Temperature: {sensor.temperature}°C")
        print(f"Humidity: {sensor.humidity}%")
        print(f"Pressure: {sensor.pressure} hPa")
        
        # Control actuators
        led.blink(times=3)
        
        # Run event loop
        hardware.run()
    """
    
    def __init__(
        self,
        auto_scan: bool = True,
        simulation: bool = None
    ):
        """
        Initialize hardware manager.
        
        Args:
            auto_scan: Automatically scan for devices on attach
            simulation: Force simulation mode (None = auto-detect)
        """
        self._buses: Dict[str, Bus] = {}
        self._devices: List[Device] = []
        self._event_loop: Optional[EventLoop] = None
        self._auto_scan = auto_scan
        self._simulation = simulation
        self._lock = threading.Lock()
        
        # I2C default pins (ESP32)
        self._default_pins = {
            "I2C": {"scl": 22, "sda": 21},
            "SPI": {"sck": 18, "mosi": 23, "miso": 19},
            "UART": {"tx": 17, "rx": 16},
            "ONEWIRE": {"pin": 4},
        }
    
    def _get_or_create_bus(self, bus_type: str, **kwargs) -> Bus:
        """Get existing bus or create a new one."""
        bus_type = bus_type.upper()
        
        # Create unique key based on pins
        key_parts = [bus_type]
        if kwargs:
            key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()) if v is not None)
        key = ":".join(key_parts)
        
        if key not in self._buses:
            # Apply defaults
            defaults = self._default_pins.get(bus_type, {})
            for k, v in defaults.items():
                if k not in kwargs:
                    kwargs[k] = v
            
            # Create bus
            bus = BusFactory.create(bus_type, **kwargs)
            bus.init()
            self._buses[key] = bus
        
        return self._buses[key]
    
    def attach(
        self,
        bus_type: str,
        type: str = None,
        **kwargs
    ) -> Device:
        """
        Attach a hardware device.
        
        Args:
            bus_type: Type of bus ("I2C", "SPI", "GPIO", "UART", "OneWire")
            type: Device type ("BME280", "DHT22", "LED", etc.)
            **kwargs: Device-specific configuration
            
        Returns:
            Configured device instance
            
        Examples:
            # Attach BME280 temperature sensor on I2C
            sensor = hardware.attach("I2C", type="BME280")
            
            # Attach DHT22 on GPIO pin 4
            dht = hardware.attach("GPIO", type="DHT22", pin=4)
            
            # Attach LED on GPIO pin 2
            led = hardware.attach("GPIO", type="LED", pin=2)
            
            # Attach relay for fan control
            fan = hardware.attach("GPIO", type="Relay", pin=5)
        """
        if type is None:
            raise ValueError("Device type must be specified")
        
        type_upper = type.upper()
        bus_type_upper = bus_type.upper()
        
        # Extract bus-specific kwargs
        bus_kwargs = {}
        device_kwargs = {}
        
        bus_params = {"scl", "sda", "sck", "mosi", "miso", "cs", "tx", "rx", "freq", "bus_id"}
        
        for k, v in kwargs.items():
            if k in bus_params:
                bus_kwargs[k] = v
            else:
                device_kwargs[k] = v
        
        # Get or create bus
        bus = self._get_or_create_bus(bus_type_upper, **bus_kwargs)
        
        # Find device class
        device_class = None
        for category in DEVICE_REGISTRY.values():
            if type_upper in category:
                device_class = category[type_upper]
                break
        
        if device_class is None:
            raise ValueError(f"Unknown device type: {type}")
        
        # Create device instance
        device = device_class(bus, **device_kwargs)
        device.connect()
        
        with self._lock:
            self._devices.append(device)
        
        return device
    
    def scan(self, bus_type: str = "I2C", **kwargs) -> List[int]:
        """
        Scan for devices on a bus.
        
        Args:
            bus_type: Bus type to scan
            **kwargs: Bus configuration
            
        Returns:
            List of device addresses found
        """
        bus = self._get_or_create_bus(bus_type, **kwargs)
        return bus.scan()
    
    def discover(self) -> Dict[str, List[Device]]:
        """
        Auto-discover connected devices.
        
        Returns:
            Dictionary of discovered devices by category
        """
        discovered = {"sensors": [], "actuators": [], "displays": []}
        
        # Scan I2C bus
        try:
            i2c = self._get_or_create_bus("I2C")
            addresses = i2c.scan()
            
            # Known I2C addresses
            known_devices = {
                0x76: ("sensors", "BME280"),
                0x77: ("sensors", "BME280"),
                0x3C: ("displays", "SSD1306"),
                0x3D: ("displays", "SSD1306"),
                0x23: ("sensors", "BH1750"),
                0x5C: ("sensors", "BH1750"),
                0x27: ("displays", "LCD1602"),
                0x3F: ("displays", "LCD1602"),
                0x68: ("sensors", "MPU6050"),
                0x69: ("sensors", "MPU6050"),
            }
            
            for addr in addresses:
                if addr in known_devices:
                    category, dev_type = known_devices[addr]
                    device_class = DEVICE_REGISTRY[category].get(dev_type.upper())
                    if device_class:
                        device = device_class(i2c, address=addr)
                        if device.connect():
                            discovered[category].append(device)
                            self._devices.append(device)
        except Exception as e:
            print(f"I2C discovery error: {e}")
        
        return discovered
    
    @property
    def devices(self) -> List[Device]:
        """Get list of attached devices."""
        return self._devices.copy()
    
    @property
    def event_loop(self) -> EventLoop:
        """Get or create the event loop."""
        if self._event_loop is None:
            self._event_loop = get_event_loop()
        return self._event_loop
    
    def start(self) -> None:
        """Start the event loop in background."""
        self.event_loop.start()
    
    def stop(self) -> None:
        """Stop the event loop and disconnect all devices."""
        if self._event_loop:
            self._event_loop.stop()
        
        for device in self._devices:
            try:
                device.disconnect()
            except Exception:
                pass
        
        for bus in self._buses.values():
            try:
                bus.deinit()
            except Exception:
                pass
    
    def run(self, poll_interval_ms: int = 100) -> None:
        """
        Run the event loop (blocking).
        
        Args:
            poll_interval_ms: How often to check for events
        """
        self.event_loop.poll_interval = poll_interval_ms / 1000.0
        self.event_loop.run_forever()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()
        return False
    
    def __repr__(self) -> str:
        return f"<Hardware devices={len(self._devices)} buses={list(self._buses.keys())}>"


# Convenience function for quick setup
def create_hardware(**kwargs) -> Hardware:
    """
    Create and configure a Hardware instance.
    
    Args:
        **kwargs: Configuration options
        
    Returns:
        Configured Hardware instance
    """
    return Hardware(**kwargs)
