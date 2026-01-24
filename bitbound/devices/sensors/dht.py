"""
DHT11/DHT22 Temperature and Humidity Sensors.
"""

from typing import Any, Dict, Optional
import time
from ...device import Sensor, DeviceInfo


class DHTSensor(Sensor):
    """
    DHT11/DHT22 Temperature and Humidity Sensor.
    
    Example:
        from bitbound import Hardware
        
        hw = Hardware()
        sensor = hw.attach("GPIO", type="DHT22", pin=4)
        
        print(f"Temperature: {sensor.temperature}°C")
        print(f"Humidity: {sensor.humidity}%")
    """
    
    def __init__(
        self,
        bus,
        pin: int = 4,
        dht_type: str = "DHT22",
        name: str = None
    ):
        """
        Initialize DHT sensor.
        
        Args:
            bus: GPIO bus instance
            pin: Data pin number
            dht_type: "DHT11" or "DHT22"
            name: Device name
        """
        super().__init__(bus, pin, name or dht_type)
        
        self._pin = pin
        self._dht_type = dht_type.upper()
        self._dht = None
        
        # Cached readings
        self._temperature: float = 0.0
        self._humidity: float = 0.0
        self._last_read: float = 0
        self._min_interval: float = 2.0 if self._dht_type == "DHT22" else 1.0
    
    def connect(self) -> bool:
        """Connect to DHT sensor."""
        try:
            try:
                import dht
                from machine import Pin
                
                if self._dht_type == "DHT11":
                    self._dht = dht.DHT11(Pin(self._pin))
                else:
                    self._dht = dht.DHT22(Pin(self._pin))
                
                self._connected = True
                return True
                
            except ImportError:
                # Simulation mode
                self._connected = True
                return True
                
        except Exception as e:
            print(f"DHT connect error: {e}")
            return False
    
    def disconnect(self) -> None:
        """Disconnect from sensor."""
        self._dht = None
        self._connected = False
    
    def get_info(self) -> DeviceInfo:
        """Get device information."""
        return DeviceInfo(
            device_type="sensor",
            name=self._name,
            model=self._dht_type,
            address=self._pin,
            bus_type="GPIO",
            capabilities=["temperature", "humidity"]
        )
    
    def _read(self) -> None:
        """Read sensor data."""
        now = time.time()
        
        # Respect minimum read interval
        if now - self._last_read < self._min_interval:
            return
        
        if self._dht:
            try:
                self._dht.measure()
                self._temperature = self._dht.temperature()
                self._humidity = self._dht.humidity()
            except Exception as e:
                print(f"DHT read error: {e}")
        else:
            # Simulation
            self._temperature = 22.5
            self._humidity = 55.0
        
        self._last_read = now
    
    @property
    def temperature(self) -> float:
        """Get temperature in Celsius."""
        self._read()
        return round(self._temperature, 1)
    
    @property
    def humidity(self) -> float:
        """Get relative humidity in percent."""
        self._read()
        return round(self._humidity, 1)
    
    def read_all(self) -> Dict[str, Any]:
        """Read all values."""
        self._read()
        return {
            "temperature": round(self._temperature, 1),
            "humidity": round(self._humidity, 1)
        }


class DHT11(DHTSensor):
    """DHT11 Temperature and Humidity Sensor."""
    
    def __init__(self, bus, pin: int = 4, name: str = "DHT11"):
        super().__init__(bus, pin, "DHT11", name)


class DHT22(DHTSensor):
    """DHT22 Temperature and Humidity Sensor."""
    
    def __init__(self, bus, pin: int = 4, name: str = "DHT22"):
        super().__init__(bus, pin, "DHT22", name)
