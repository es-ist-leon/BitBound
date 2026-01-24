"""
Motion Sensors (PIR, Accelerometer, Gyroscope).
"""

from typing import Any, Dict, Optional
from ...device import Sensor, DeviceInfo


class MotionSensor(Sensor):
    """Base class for motion sensors."""
    pass


class PIRSensor(MotionSensor):
    """
    PIR Motion Sensor.
    
    Example:
        from bitbound import Hardware
        
        hw = Hardware()
        pir = hw.attach("GPIO", type="PIR", pin=14)
        
        pir.on_change("motion", lambda e: print("Motion detected!"))
    """
    
    def __init__(self, bus, pin: int = 14, name: str = "PIR"):
        """
        Initialize PIR sensor.
        
        Args:
            bus: GPIO bus instance
            pin: Signal pin
            name: Device name
        """
        super().__init__(bus, pin, name)
        
        self._pin = pin
        self._gpio_pin = None
    
    def connect(self) -> bool:
        """Connect to PIR sensor."""
        try:
            if hasattr(self._bus, 'pin'):
                from ..buses.gpio import PinMode
                self._gpio_pin = self._bus.pin(self._pin, PinMode.INPUT)
            
            self._connected = True
            return True
        except Exception as e:
            print(f"PIR connect error: {e}")
            return False
    
    def disconnect(self) -> None:
        """Disconnect from sensor."""
        self._connected = False
    
    def get_info(self) -> DeviceInfo:
        """Get device information."""
        return DeviceInfo(
            device_type="sensor",
            name=self._name,
            model="PIR",
            address=self._pin,
            bus_type="GPIO",
            capabilities=["motion"]
        )
    
    @property
    def motion(self) -> bool:
        """Check if motion is detected."""
        if self._gpio_pin:
            return bool(self._gpio_pin.value)
        # Simulation
        return False
    
    @property
    def detected(self) -> bool:
        """Alias for motion."""
        return self.motion
    
    def read_all(self) -> Dict[str, Any]:
        """Read all values."""
        return {"motion": self.motion}


class MPU6050Sensor(MotionSensor):
    """
    MPU6050 6-axis Accelerometer/Gyroscope.
    
    Example:
        from bitbound import Hardware
        
        hw = Hardware()
        imu = hw.attach("I2C", type="MPU6050")
        
        print(f"Acceleration: {imu.acceleration}")
        print(f"Gyroscope: {imu.gyroscope}")
        print(f"Temperature: {imu.temperature}°C")
    """
    
    # Register addresses
    REG_PWR_MGMT_1 = 0x6B
    REG_ACCEL_XOUT_H = 0x3B
    REG_GYRO_XOUT_H = 0x43
    REG_TEMP_OUT_H = 0x41
    REG_WHO_AM_I = 0x75
    
    DEFAULT_ADDRESS = 0x68
    
    def __init__(self, bus, address: int = DEFAULT_ADDRESS, name: str = "MPU6050"):
        """
        Initialize MPU6050 sensor.
        
        Args:
            bus: I2C bus instance
            address: I2C address (0x68 or 0x69)
            name: Device name
        """
        super().__init__(bus, address, name)
        
        # Scaling factors
        self._accel_scale = 16384.0  # ±2g
        self._gyro_scale = 131.0     # ±250°/s
        
        # Cached values
        self._accel = (0.0, 0.0, 0.0)
        self._gyro = (0.0, 0.0, 0.0)
        self._temp = 0.0
    
    def connect(self) -> bool:
        """Connect to MPU6050."""
        try:
            # Wake up the device
            if hasattr(self._bus, 'write_byte'):
                self._bus.write_byte(self._address, self.REG_PWR_MGMT_1, 0)
            else:
                self._bus.write_to(self._address, bytes([0]), self.REG_PWR_MGMT_1)
            
            self._connected = True
            return True
        except Exception as e:
            print(f"MPU6050 connect error: {e}")
            # Simulation mode
            self._connected = True
            return True
    
    def disconnect(self) -> None:
        """Disconnect from sensor."""
        self._connected = False
    
    def get_info(self) -> DeviceInfo:
        """Get device information."""
        return DeviceInfo(
            device_type="sensor",
            name=self._name,
            manufacturer="InvenSense",
            model="MPU6050",
            address=self._address,
            bus_type="I2C",
            capabilities=["acceleration", "gyroscope", "temperature"]
        )
    
    def _read_word(self, reg: int) -> int:
        """Read a 16-bit signed value."""
        if self._bus.is_simulation:
            return 0
        
        data = self._bus.read_from(self._address, 2, reg)
        value = (data[0] << 8) | data[1]
        if value >= 32768:
            value -= 65536
        return value
    
    def _read_sensors(self) -> None:
        """Read all sensor values."""
        if self._bus.is_simulation:
            self._accel = (0.0, 0.0, 9.81)
            self._gyro = (0.0, 0.0, 0.0)
            self._temp = 25.0
            return
        
        # Read accelerometer
        ax = self._read_word(self.REG_ACCEL_XOUT_H) / self._accel_scale
        ay = self._read_word(self.REG_ACCEL_XOUT_H + 2) / self._accel_scale
        az = self._read_word(self.REG_ACCEL_XOUT_H + 4) / self._accel_scale
        self._accel = (ax, ay, az)
        
        # Read temperature
        raw_temp = self._read_word(self.REG_TEMP_OUT_H)
        self._temp = raw_temp / 340.0 + 36.53
        
        # Read gyroscope
        gx = self._read_word(self.REG_GYRO_XOUT_H) / self._gyro_scale
        gy = self._read_word(self.REG_GYRO_XOUT_H + 2) / self._gyro_scale
        gz = self._read_word(self.REG_GYRO_XOUT_H + 4) / self._gyro_scale
        self._gyro = (gx, gy, gz)
    
    @property
    def acceleration(self) -> tuple:
        """Get acceleration (x, y, z) in g."""
        self._read_sensors()
        return tuple(round(v, 3) for v in self._accel)
    
    @property
    def gyroscope(self) -> tuple:
        """Get angular velocity (x, y, z) in °/s."""
        self._read_sensors()
        return tuple(round(v, 2) for v in self._gyro)
    
    @property
    def temperature(self) -> float:
        """Get temperature in Celsius."""
        self._read_sensors()
        return round(self._temp, 1)
    
    def read_all(self) -> Dict[str, Any]:
        """Read all values."""
        self._read_sensors()
        return {
            "acceleration": self.acceleration,
            "gyroscope": self.gyroscope,
            "temperature": round(self._temp, 1)
        }
