"""
BME280 Temperature, Humidity, and Pressure Sensor.
"""

from typing import Any, Dict, Optional
import time
from ...device import Sensor, DeviceInfo
from ...buses.base import Bus


class BME280Sensor(Sensor):
    """
    BME280 Temperature, Humidity, and Pressure Sensor.
    
    Provides high-level access to the Bosch BME280 sensor.
    
    Example:
        from bitbound import Hardware
        
        hw = Hardware()
        sensor = hw.attach("I2C", type="BME280")
        
        print(f"Temperature: {sensor.temperature}°C")
        print(f"Humidity: {sensor.humidity}%")
        print(f"Pressure: {sensor.pressure} hPa")
        
        # With threshold events
        sensor.on_threshold("temperature > 25°C", lambda e: print("Hot!"))
    """
    
    # BME280 Register addresses
    REG_CHIP_ID = 0xD0
    REG_RESET = 0xE0
    REG_CTRL_HUM = 0xF2
    REG_STATUS = 0xF3
    REG_CTRL_MEAS = 0xF4
    REG_CONFIG = 0xF5
    REG_PRESS_MSB = 0xF7
    REG_CALIB = 0x88
    REG_CALIB_H = 0xE1
    
    CHIP_ID_BME280 = 0x60
    CHIP_ID_BMP280 = 0x58
    
    # Default I2C addresses
    DEFAULT_ADDRESS = 0x76
    ALT_ADDRESS = 0x77
    
    def __init__(
        self,
        bus: Bus,
        address: int = DEFAULT_ADDRESS,
        name: str = "BME280"
    ):
        """
        Initialize BME280 sensor.
        
        Args:
            bus: I2C bus instance
            address: I2C address (0x76 or 0x77)
            name: Device name
        """
        super().__init__(bus, address, name)
        
        self._chip_id: Optional[int] = None
        self._is_bme280 = True  # vs BMP280 (no humidity)
        
        # Calibration data
        self._cal_t: list = []
        self._cal_p: list = []
        self._cal_h: list = []
        
        # Cached readings
        self._temperature: float = 0.0
        self._humidity: float = 0.0
        self._pressure: float = 0.0
        self._altitude: float = 0.0
        
        # Fine temperature for pressure/humidity compensation
        self._t_fine: int = 0
        
        # Sea level pressure for altitude calculation
        self._sea_level_pressure: float = 1013.25
    
    def connect(self) -> bool:
        """Connect to the BME280 sensor."""
        try:
            # Read and verify chip ID
            if hasattr(self._bus, 'read_byte'):
                self._chip_id = self._bus.read_byte(self._address, self.REG_CHIP_ID)
            else:
                data = self._bus.read_from(self._address, 1, self.REG_CHIP_ID)
                self._chip_id = data[0]
            
            if self._chip_id == self.CHIP_ID_BME280:
                self._is_bme280 = True
            elif self._chip_id == self.CHIP_ID_BMP280:
                self._is_bme280 = False
            else:
                # In simulation mode, accept any chip ID
                if self._bus.is_simulation:
                    self._chip_id = self.CHIP_ID_BME280
                    self._is_bme280 = True
                else:
                    print(f"Unknown chip ID: 0x{self._chip_id:02X}")
                    return False
            
            # Read calibration data
            self._read_calibration()
            
            # Configure sensor
            self._configure()
            
            self._connected = True
            return True
            
        except Exception as e:
            print(f"BME280 connect error: {e}")
            return False
    
    def disconnect(self) -> None:
        """Disconnect from the sensor."""
        self._connected = False
    
    def get_info(self) -> DeviceInfo:
        """Get device information."""
        device_type = "BME280" if self._is_bme280 else "BMP280"
        return DeviceInfo(
            device_type="sensor",
            name=self._name,
            manufacturer="Bosch",
            model=device_type,
            address=self._address,
            bus_type="I2C",
            capabilities=["temperature", "pressure"] + (["humidity"] if self._is_bme280 else []),
            properties={"chip_id": f"0x{self._chip_id:02X}" if self._chip_id else "unknown"}
        )
    
    def _read_calibration(self) -> None:
        """Read calibration data from sensor."""
        if self._bus.is_simulation:
            # Use default calibration values for simulation
            self._cal_t = [27504, 26435, -1000]
            self._cal_p = [36477, -10685, 3024, 2855, 140, -7, 9900, -10230, 4285]
            self._cal_h = [75, 363, 0, 326, 50, 30]
            return
        
        # Read temperature and pressure calibration
        cal_data = self._bus.read_from(self._address, 26, self.REG_CALIB)
        
        # Temperature calibration
        self._cal_t = [
            self._u16(cal_data, 0),
            self._s16(cal_data, 2),
            self._s16(cal_data, 4),
        ]
        
        # Pressure calibration
        self._cal_p = [
            self._u16(cal_data, 6),
            self._s16(cal_data, 8),
            self._s16(cal_data, 10),
            self._s16(cal_data, 12),
            self._s16(cal_data, 14),
            self._s16(cal_data, 16),
            self._s16(cal_data, 18),
            self._s16(cal_data, 20),
            self._s16(cal_data, 22),
        ]
        
        # Humidity calibration (BME280 only)
        if self._is_bme280:
            self._cal_h = [cal_data[25]]
            hum_cal = self._bus.read_from(self._address, 7, self.REG_CALIB_H)
            self._cal_h.extend([
                self._s16(hum_cal, 0),
                hum_cal[2],
                (hum_cal[3] << 4) | (hum_cal[4] & 0x0F),
                (hum_cal[5] << 4) | ((hum_cal[4] >> 4) & 0x0F),
                self._s8(hum_cal[6]),
            ])
    
    def _configure(self) -> None:
        """Configure the sensor for normal operation."""
        if self._bus.is_simulation:
            return
        
        # Humidity oversampling x1
        if self._is_bme280:
            self._bus.write_byte(self._address, self.REG_CTRL_HUM, 0x01)
        
        # Temperature and pressure oversampling x1, normal mode
        self._bus.write_byte(self._address, self.REG_CTRL_MEAS, 0x27)
        
        # Standby 1000ms, filter off
        self._bus.write_byte(self._address, self.REG_CONFIG, 0xA0)
    
    def _read_raw(self) -> None:
        """Read raw sensor data and convert to physical values."""
        if self._bus.is_simulation:
            # Simulated readings
            self._temperature = 23.5
            self._humidity = 45.0
            self._pressure = 1013.25
            return
        
        # Read raw data
        data = self._bus.read_from(self._address, 8, self.REG_PRESS_MSB)
        
        # Parse raw values
        raw_press = (data[0] << 12) | (data[1] << 4) | (data[2] >> 4)
        raw_temp = (data[3] << 12) | (data[4] << 4) | (data[5] >> 4)
        raw_hum = (data[6] << 8) | data[7]
        
        # Compensate temperature
        self._temperature = self._compensate_temperature(raw_temp)
        
        # Compensate pressure
        self._pressure = self._compensate_pressure(raw_press)
        
        # Compensate humidity
        if self._is_bme280:
            self._humidity = self._compensate_humidity(raw_hum)
        else:
            self._humidity = 0.0
        
        # Calculate altitude
        self._altitude = self._calculate_altitude()
    
    def _compensate_temperature(self, raw: int) -> float:
        """Compensate raw temperature reading."""
        t = self._cal_t
        
        var1 = ((raw / 16384.0) - (t[0] / 1024.0)) * t[1]
        var2 = ((raw / 131072.0) - (t[0] / 8192.0)) ** 2 * t[2]
        
        self._t_fine = int(var1 + var2)
        return (var1 + var2) / 5120.0
    
    def _compensate_pressure(self, raw: int) -> float:
        """Compensate raw pressure reading."""
        p = self._cal_p
        
        var1 = self._t_fine / 2.0 - 64000.0
        var2 = var1 * var1 * p[5] / 32768.0
        var2 = var2 + var1 * p[4] * 2.0
        var2 = var2 / 4.0 + p[3] * 65536.0
        var1 = (p[2] * var1 * var1 / 524288.0 + p[1] * var1) / 524288.0
        var1 = (1.0 + var1 / 32768.0) * p[0]
        
        if var1 == 0:
            return 0.0
        
        pressure = 1048576.0 - raw
        pressure = ((pressure - var2 / 4096.0) * 6250.0) / var1
        var1 = p[8] * pressure * pressure / 2147483648.0
        var2 = pressure * p[7] / 32768.0
        
        return (pressure + (var1 + var2 + p[6]) / 16.0) / 100.0  # hPa
    
    def _compensate_humidity(self, raw: int) -> float:
        """Compensate raw humidity reading."""
        h = self._cal_h
        
        humidity = self._t_fine - 76800.0
        if humidity == 0:
            return 0.0
        
        humidity = raw - (h[3] * 64.0 + (h[4] / 16384.0) * humidity)
        humidity *= (h[1] / 65536.0) * (1.0 + (h[5] / 67108864.0) * humidity * (1.0 + (h[2] / 67108864.0) * humidity))
        humidity *= 1.0 - h[0] * humidity / 524288.0
        
        return max(0.0, min(100.0, humidity))
    
    def _calculate_altitude(self) -> float:
        """Calculate altitude from pressure."""
        if self._pressure == 0:
            return 0.0
        
        return 44330.0 * (1.0 - pow(self._pressure / self._sea_level_pressure, 0.1903))
    
    # Helper methods for parsing calibration data
    def _u16(self, data: bytes, offset: int) -> int:
        return data[offset] | (data[offset + 1] << 8)
    
    def _s16(self, data: bytes, offset: int) -> int:
        val = self._u16(data, offset)
        if val >= 32768:
            val -= 65536
        return val
    
    def _s8(self, val: int) -> int:
        if val >= 128:
            val -= 256
        return val
    
    # Properties
    
    @property
    def temperature(self) -> float:
        """Get temperature in Celsius."""
        self._read_raw()
        return round(self._temperature, 2)
    
    @property
    def humidity(self) -> float:
        """Get relative humidity in percent."""
        self._read_raw()
        return round(self._humidity, 2)
    
    @property
    def pressure(self) -> float:
        """Get pressure in hPa."""
        self._read_raw()
        return round(self._pressure, 2)
    
    @property
    def altitude(self) -> float:
        """Get calculated altitude in meters."""
        self._read_raw()
        return round(self._altitude, 2)
    
    @property
    def sea_level_pressure(self) -> float:
        """Get reference sea level pressure."""
        return self._sea_level_pressure
    
    @sea_level_pressure.setter
    def sea_level_pressure(self, value: float) -> None:
        """Set reference sea level pressure for altitude calculation."""
        self._sea_level_pressure = value
    
    def read_all(self) -> Dict[str, Any]:
        """Read all sensor values."""
        self._read_raw()
        result = {
            "temperature": round(self._temperature, 2),
            "pressure": round(self._pressure, 2),
            "altitude": round(self._altitude, 2),
        }
        if self._is_bme280:
            result["humidity"] = round(self._humidity, 2)
        return result
