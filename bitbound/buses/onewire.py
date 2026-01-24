"""
OneWire Bus implementation.
"""

from typing import List, Optional
from .base import Bus, BusConfig, BusType, BusFactory


class OneWireBus(Bus):
    """
    OneWire bus implementation for devices like DS18B20 temperature sensors.
    
    Example:
        bus = OneWireBus(pin=4)
        bus.init()
        
        # Scan for devices
        devices = bus.scan()
        
        # Read temperature from DS18B20
        temp = bus.read_ds18b20(devices[0])
    """
    
    def __init__(self, pin: int = 4):
        """
        Initialize OneWire bus.
        
        Args:
            pin: Data pin number
        """
        config = BusConfig(
            bus_type=BusType.ONEWIRE,
            pins={"data": pin}
        )
        super().__init__(config)
        
        self._pin = pin
        self._ow = None
        
        # Simulated devices
        self._simulated_devices = {}
    
    def init(self) -> bool:
        """Initialize OneWire bus."""
        try:
            from machine import Pin
            import onewire
            
            self._ow = onewire.OneWire(Pin(self._pin))
            self._simulation_mode = False
            self._initialized = True
            return True
            
        except ImportError:
            self._simulation_mode = True
            self._initialized = True
            self._setup_simulation()
            return True
    
    def _setup_simulation(self) -> None:
        """Set up simulated devices."""
        # Simulate a DS18B20 temperature sensor
        self._simulated_devices[b'\x28\x01\x02\x03\x04\x05\x06\x07'] = {
            "type": "DS18B20",
            "temperature": 23.5
        }
    
    def add_simulated_device(self, rom: bytes, device_type: str, **kwargs) -> None:
        """Add a simulated device."""
        self._simulated_devices[rom] = {"type": device_type, **kwargs}
    
    def deinit(self) -> None:
        """Deinitialize OneWire."""
        self._ow = None
        self._initialized = False
    
    def scan(self) -> List[bytes]:
        """
        Scan for devices on the OneWire bus.
        
        Returns:
            List of ROM codes (8 bytes each)
        """
        if not self._initialized:
            self.init()
        
        if self._simulation_mode:
            return list(self._simulated_devices.keys())
        
        if self._ow:
            return self._ow.scan()
        return []
    
    def reset(self) -> bool:
        """
        Reset the bus.
        
        Returns:
            True if device presence detected
        """
        if self._simulation_mode:
            return len(self._simulated_devices) > 0
        
        if self._ow:
            return self._ow.reset()
        return False
    
    def read_ds18b20(self, rom: bytes) -> Optional[float]:
        """
        Read temperature from a DS18B20 sensor.
        
        Args:
            rom: 8-byte ROM code of the sensor
            
        Returns:
            Temperature in Celsius or None if error
        """
        if self._simulation_mode:
            if rom in self._simulated_devices:
                return self._simulated_devices[rom].get("temperature")
            return None
        
        try:
            import ds18x20
            ds = ds18x20.DS18X20(self._ow)
            ds.convert_temp()
            
            import time
            time.sleep_ms(750)  # Conversion time
            
            return ds.read_temp(rom)
        except Exception as e:
            print(f"DS18B20 read error: {e}")
            return None
    
    def read_all_ds18b20(self) -> dict:
        """
        Read temperature from all DS18B20 sensors.
        
        Returns:
            Dict mapping ROM codes to temperatures
        """
        result = {}
        for rom in self.scan():
            temp = self.read_ds18b20(rom)
            if temp is not None:
                result[rom] = temp
        return result
    
    def set_simulated_temp(self, rom: bytes, temperature: float) -> None:
        """Set temperature for a simulated sensor."""
        if rom in self._simulated_devices:
            self._simulated_devices[rom]["temperature"] = temperature
    
    def __repr__(self) -> str:
        mode = "SIM" if self._simulation_mode else "HW"
        return f"<OneWireBus [{mode}] pin={self._pin}>"


# Register with factory
BusFactory.register("ONEWIRE", OneWireBus)
BusFactory.register("1WIRE", OneWireBus)
