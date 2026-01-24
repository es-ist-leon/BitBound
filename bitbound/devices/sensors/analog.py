"""
Analog Sensors (ADC-based).
"""

from typing import Any, Dict, Optional, Callable
from ...device import Sensor, DeviceInfo


class AnalogSensor(Sensor):
    """
    Generic Analog Sensor using ADC.
    
    Can be used for potentiometers, light sensors, etc.
    
    Example:
        from bitbound import Hardware
        
        hw = Hardware()
        
        # Simple analog read
        pot = hw.attach("ADC", type="Analog", pin=34)
        print(f"Value: {pot.value}")
        print(f"Voltage: {pot.voltage}V")
        
        # With custom scaling (e.g., soil moisture)
        moisture = hw.attach("ADC", type="Analog", pin=35,
                            min_val=0, max_val=100, unit="%")
        print(f"Moisture: {moisture.scaled_value}%")
    """
    
    def __init__(
        self,
        bus,
        pin: int,
        name: str = "Analog",
        min_val: float = 0,
        max_val: float = 4095,
        unit: str = "",
        vref: float = 3.3,
        attenuation: int = 3,
        transform: Optional[Callable[[float], float]] = None
    ):
        """
        Initialize analog sensor.
        
        Args:
            bus: GPIO bus instance
            pin: ADC pin number
            name: Device name
            min_val: Minimum scaled value
            max_val: Maximum scaled value
            unit: Unit string for scaled value
            vref: Reference voltage
            attenuation: ADC attenuation (0-3)
            transform: Optional custom transform function
        """
        super().__init__(bus, pin, name)
        
        self._pin = pin
        self._min_val = min_val
        self._max_val = max_val
        self._unit = unit
        self._vref = vref
        self._attenuation = attenuation
        self._transform = transform
        
        self._adc = None
        self._raw_value: int = 0
    
    def connect(self) -> bool:
        """Connect to ADC."""
        try:
            try:
                from machine import ADC, Pin
                
                self._adc = ADC(Pin(self._pin))
                
                # Set attenuation
                atten_map = {
                    0: ADC.ATTN_0DB,    # 0-1.1V
                    1: ADC.ATTN_2_5DB,  # 0-1.5V
                    2: ADC.ATTN_6DB,    # 0-2.2V
                    3: ADC.ATTN_11DB,   # 0-3.3V
                }
                self._adc.atten(atten_map.get(self._attenuation, ADC.ATTN_11DB))
                
                # Set 12-bit resolution
                try:
                    self._adc.width(ADC.WIDTH_12BIT)
                except Exception:
                    pass
                
                self._connected = True
                return True
                
            except ImportError:
                # Simulation mode
                self._connected = True
                return True
                
        except Exception as e:
            print(f"ADC connect error: {e}")
            return False
    
    def disconnect(self) -> None:
        """Disconnect from ADC."""
        self._adc = None
        self._connected = False
    
    def get_info(self) -> DeviceInfo:
        """Get device information."""
        return DeviceInfo(
            device_type="sensor",
            name=self._name,
            address=self._pin,
            bus_type="ADC",
            capabilities=["value", "voltage", "scaled_value"]
        )
    
    def _read(self) -> int:
        """Read raw ADC value."""
        if self._adc:
            self._raw_value = self._adc.read()
        else:
            # Simulation - return middle value
            self._raw_value = 2048
        return self._raw_value
    
    @property
    def value(self) -> int:
        """Get raw ADC value (0-4095)."""
        return self._read()
    
    @property
    def voltage(self) -> float:
        """Get voltage reading."""
        raw = self._read()
        return round((raw / 4095.0) * self._vref, 3)
    
    @property
    def scaled_value(self) -> float:
        """Get scaled value based on min/max configuration."""
        raw = self._read()
        
        if self._transform:
            return self._transform(raw)
        
        # Linear scaling
        normalized = raw / 4095.0
        scaled = self._min_val + (normalized * (self._max_val - self._min_val))
        return round(scaled, 2)
    
    @property
    def percent(self) -> float:
        """Get value as percentage (0-100)."""
        raw = self._read()
        return round((raw / 4095.0) * 100, 1)
    
    def read_all(self) -> Dict[str, Any]:
        """Read all values."""
        raw = self._read()
        return {
            "value": raw,
            "voltage": round((raw / 4095.0) * self._vref, 3),
            "scaled_value": self.scaled_value,
            "percent": round((raw / 4095.0) * 100, 1)
        }
