"""
Light Sensors.
"""

from typing import Any, Dict
from ...device import Sensor, DeviceInfo


class LightSensor(Sensor):
    """Base class for light sensors."""
    pass


class BH1750Sensor(LightSensor):
    """
    BH1750 Digital Light Sensor.
    
    Example:
        from bitbound import Hardware
        
        hw = Hardware()
        light = hw.attach("I2C", type="BH1750")
        
        print(f"Light: {light.lux} lux")
    """
    
    DEFAULT_ADDRESS = 0x23
    ALT_ADDRESS = 0x5C
    
    # Commands
    CMD_POWER_ON = 0x01
    CMD_RESET = 0x07
    CMD_CONTINUOUS_H = 0x10  # 1 lux resolution, 120ms
    CMD_CONTINUOUS_H2 = 0x11  # 0.5 lux resolution, 120ms
    CMD_CONTINUOUS_L = 0x13  # 4 lux resolution, 16ms
    
    def __init__(self, bus, address: int = DEFAULT_ADDRESS, name: str = "BH1750"):
        """
        Initialize BH1750 sensor.
        
        Args:
            bus: I2C bus instance
            address: I2C address (0x23 or 0x5C)
            name: Device name
        """
        super().__init__(bus, address, name)
        
        self._lux: float = 0.0
    
    def connect(self) -> bool:
        """Connect to BH1750."""
        try:
            if not self._bus.is_simulation:
                # Power on
                self._bus.write_to(self._address, bytes([self.CMD_POWER_ON]))
                # Set continuous high resolution mode
                self._bus.write_to(self._address, bytes([self.CMD_CONTINUOUS_H]))
            
            self._connected = True
            return True
        except Exception as e:
            print(f"BH1750 connect error: {e}")
            self._connected = True  # Simulation
            return True
    
    def disconnect(self) -> None:
        """Disconnect from sensor."""
        self._connected = False
    
    def get_info(self) -> DeviceInfo:
        """Get device information."""
        return DeviceInfo(
            device_type="sensor",
            name=self._name,
            model="BH1750",
            address=self._address,
            bus_type="I2C",
            capabilities=["lux"]
        )
    
    @property
    def lux(self) -> float:
        """Get light intensity in lux."""
        if self._bus.is_simulation:
            return 500.0  # Typical indoor lighting
        
        try:
            data = self._bus.read_from(self._address, 2)
            raw = (data[0] << 8) | data[1]
            self._lux = raw / 1.2
        except Exception:
            pass
        
        return round(self._lux, 1)
    
    @property
    def illuminance(self) -> float:
        """Alias for lux."""
        return self.lux
    
    def read_all(self) -> Dict[str, Any]:
        """Read all values."""
        return {"lux": self.lux}
