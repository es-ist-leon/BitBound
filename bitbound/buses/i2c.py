"""
I2C Bus implementation.
"""

from typing import List, Optional
from .base import Bus, BusConfig, BusType, BusFactory


class I2CBus(Bus):
    """
    I2C (Inter-Integrated Circuit) bus implementation.
    
    Supports both real hardware (MicroPython/CircuitPython) and simulation mode.
    
    Example:
        bus = I2CBus(scl=22, sda=21, freq=400000)
        bus.init()
        
        # Scan for devices
        addresses = bus.scan()
        
        # Read/write
        data = bus.read_from(0x76, 3)
        bus.write_to(0x76, bytes([0xF7]))
    """
    
    # Common I2C device addresses for reference
    COMMON_ADDRESSES = {
        0x20: "PCF8574 (I/O Expander)",
        0x27: "LCD I2C",
        0x3C: "SSD1306 OLED",
        0x48: "ADS1115 ADC",
        0x50: "AT24C EEPROM",
        0x68: "DS3231 RTC / MPU6050",
        0x76: "BME280/BMP280",
        0x77: "BME280/BMP280 (alt)",
    }
    
    def __init__(
        self,
        scl: int = 22,
        sda: int = 21,
        freq: int = 400000,
        bus_id: int = 0
    ):
        """
        Initialize I2C bus.
        
        Args:
            scl: SCL pin number
            sda: SDA pin number
            freq: Clock frequency in Hz
            bus_id: I2C bus ID (for boards with multiple I2C)
        """
        config = BusConfig(
            bus_type=BusType.I2C,
            pins={"scl": scl, "sda": sda},
            speed=freq,
            extra={"bus_id": bus_id}
        )
        super().__init__(config)
        
        self._scl = scl
        self._sda = sda
        self._freq = freq
        self._bus_id = bus_id
        self._i2c = None
        
        # Simulated devices for testing
        self._simulated_devices: dict = {}
    
    def init(self) -> bool:
        """Initialize the I2C bus."""
        try:
            # Try MicroPython
            try:
                from machine import I2C, Pin
                self._i2c = I2C(
                    self._bus_id,
                    scl=Pin(self._scl),
                    sda=Pin(self._sda),
                    freq=self._freq
                )
                self._simulation_mode = False
                self._initialized = True
                return True
            except ImportError:
                pass
            
            # Try CircuitPython
            try:
                import board
                import busio
                scl_pin = getattr(board, f"GP{self._scl}", None) or getattr(board, f"D{self._scl}", None)
                sda_pin = getattr(board, f"GP{self._sda}", None) or getattr(board, f"D{self._sda}", None)
                if scl_pin and sda_pin:
                    self._i2c = busio.I2C(scl_pin, sda_pin, frequency=self._freq)
                    self._simulation_mode = False
                    self._initialized = True
                    return True
            except ImportError:
                pass
            
            # Fall back to simulation mode
            self._simulation_mode = True
            self._initialized = True
            self._setup_simulation()
            return True
            
        except Exception as e:
            print(f"I2C init error: {e}")
            return False
    
    def _setup_simulation(self) -> None:
        """Set up simulated devices for testing."""
        # Simulate a BME280 at address 0x76
        self._simulated_devices[0x76] = {
            "type": "BME280",
            "registers": {
                0xD0: 0x60,  # Chip ID for BME280
                0xF7: [0x50, 0x00, 0x00, 0x80, 0x00, 0x00, 0x80, 0x00],  # Raw data
            }
        }
        
        # Simulate an SSD1306 OLED at address 0x3C
        self._simulated_devices[0x3C] = {
            "type": "SSD1306",
            "registers": {}
        }
    
    def add_simulated_device(self, address: int, device_type: str, registers: dict = None) -> None:
        """Add a simulated device for testing."""
        self._simulated_devices[address] = {
            "type": device_type,
            "registers": registers or {}
        }
    
    def deinit(self) -> None:
        """Deinitialize the I2C bus."""
        if self._i2c and hasattr(self._i2c, 'deinit'):
            self._i2c.deinit()
        self._i2c = None
        self._initialized = False
    
    def scan(self) -> List[int]:
        """
        Scan for devices on the I2C bus.
        
        Returns:
            List of device addresses found
        """
        if not self._initialized:
            self.init()
        
        if self._simulation_mode:
            return list(self._simulated_devices.keys())
        
        if self._i2c:
            return self._i2c.scan()
        
        return []
    
    def read_from(
        self,
        address: int,
        num_bytes: int,
        register: Optional[int] = None
    ) -> bytes:
        """
        Read bytes from a device.
        
        Args:
            address: Device address (7-bit)
            num_bytes: Number of bytes to read
            register: Optional register address to read from
            
        Returns:
            Bytes read from device
        """
        if not self._initialized:
            self.init()
        
        if self._simulation_mode:
            return self._sim_read(address, num_bytes, register)
        
        if register is not None:
            # Write register address first
            self._i2c.writeto(address, bytes([register]))
        
        return self._i2c.readfrom(address, num_bytes)
    
    def _sim_read(self, address: int, num_bytes: int, register: Optional[int]) -> bytes:
        """Simulated read operation."""
        if address not in self._simulated_devices:
            raise OSError(f"No device at address 0x{address:02X}")
        
        device = self._simulated_devices[address]
        if register is not None and register in device["registers"]:
            data = device["registers"][register]
            if isinstance(data, list):
                return bytes(data[:num_bytes])
            return bytes([data] * num_bytes)
        
        # Return dummy data
        return bytes([0] * num_bytes)
    
    def write_to(
        self,
        address: int,
        data: bytes,
        register: Optional[int] = None
    ) -> None:
        """
        Write bytes to a device.
        
        Args:
            address: Device address (7-bit)
            data: Bytes to write
            register: Optional register address to write to
        """
        if not self._initialized:
            self.init()
        
        if self._simulation_mode:
            self._sim_write(address, data, register)
            return
        
        if register is not None:
            data = bytes([register]) + data
        
        self._i2c.writeto(address, data)
    
    def _sim_write(self, address: int, data: bytes, register: Optional[int]) -> None:
        """Simulated write operation."""
        if address not in self._simulated_devices:
            raise OSError(f"No device at address 0x{address:02X}")
        
        # Store written data in simulation
        device = self._simulated_devices[address]
        if register is not None:
            device["registers"][register] = list(data)
    
    def read_register(self, address: int, register: int, num_bytes: int = 1) -> bytes:
        """
        Read from a specific register.
        
        Args:
            address: Device address
            register: Register address
            num_bytes: Number of bytes to read
            
        Returns:
            Bytes read
        """
        return self.read_from(address, num_bytes, register)
    
    def write_register(self, address: int, register: int, data: bytes) -> None:
        """
        Write to a specific register.
        
        Args:
            address: Device address
            register: Register address
            data: Data to write
        """
        self.write_to(address, data, register)
    
    def read_byte(self, address: int, register: int) -> int:
        """Read a single byte from a register."""
        return self.read_register(address, register, 1)[0]
    
    def write_byte(self, address: int, register: int, value: int) -> None:
        """Write a single byte to a register."""
        self.write_register(address, register, bytes([value]))
    
    def __repr__(self) -> str:
        mode = "SIM" if self._simulation_mode else "HW"
        return f"<I2CBus [{mode}] SCL={self._scl} SDA={self._sda} {self._freq}Hz>"


# Register with factory
BusFactory.register("I2C", I2CBus)
