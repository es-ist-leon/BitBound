"""
DS18B20 Temperature Sensor.
"""

from typing import Any, Dict, List, Optional
from ...device import Sensor, DeviceInfo


class DS18B20Sensor(Sensor):
    """
    DS18B20 OneWire Temperature Sensor.
    
    Example:
        from bitbound import Hardware
        
        hw = Hardware()
        sensor = hw.attach("OneWire", type="DS18B20", pin=4)
        
        print(f"Temperature: {sensor.temperature}°C")
    """
    
    def __init__(
        self,
        bus,
        rom: bytes = None,
        pin: int = 4,
        name: str = "DS18B20"
    ):
        """
        Initialize DS18B20 sensor.
        
        Args:
            bus: OneWire bus instance
            rom: Specific ROM code (or None for first found)
            pin: OneWire data pin
            name: Device name
        """
        super().__init__(bus, None, name)
        
        self._pin = pin
        self._rom = rom
        self._ds = None
        
        # Cached reading
        self._temperature: float = 0.0
    
    def connect(self) -> bool:
        """Connect to DS18B20 sensor."""
        try:
            # Find sensors on bus
            roms = self._bus.scan()
            
            if not roms:
                print("No DS18B20 sensors found")
                return False
            
            # Use specified ROM or first found
            if self._rom is None:
                self._rom = roms[0]
            elif self._rom not in roms:
                print(f"Specified ROM not found: {self._rom.hex()}")
                return False
            
            self._connected = True
            return True
            
        except Exception as e:
            print(f"DS18B20 connect error: {e}")
            return False
    
    def disconnect(self) -> None:
        """Disconnect from sensor."""
        self._connected = False
    
    def get_info(self) -> DeviceInfo:
        """Get device information."""
        return DeviceInfo(
            device_type="sensor",
            name=self._name,
            manufacturer="Dallas/Maxim",
            model="DS18B20",
            bus_type="OneWire",
            capabilities=["temperature"],
            properties={"rom": self._rom.hex() if self._rom else "unknown"}
        )
    
    @property
    def temperature(self) -> float:
        """Get temperature in Celsius."""
        if self._rom:
            temp = self._bus.read_ds18b20(self._rom)
            if temp is not None:
                self._temperature = temp
        return round(self._temperature, 2)
    
    @property
    def rom(self) -> Optional[bytes]:
        """Get the ROM code."""
        return self._rom
    
    def read_all(self) -> Dict[str, Any]:
        """Read all values."""
        return {"temperature": self.temperature}
    
    @classmethod
    def scan(cls, bus) -> List[bytes]:
        """Scan for DS18B20 sensors on the bus."""
        return bus.scan()
