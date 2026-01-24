"""
SPI Bus implementation.
"""

from typing import List, Optional
from .base import Bus, BusConfig, BusType, BusFactory


class SPIBus(Bus):
    """
    SPI (Serial Peripheral Interface) bus implementation.
    
    Example:
        bus = SPIBus(sck=18, mosi=23, miso=19, cs=5)
        bus.init()
        
        # Transfer data
        result = bus.transfer(bytes([0x9F]))  # Read JEDEC ID
    """
    
    def __init__(
        self,
        sck: int = 18,
        mosi: int = 23,
        miso: int = 19,
        cs: Optional[int] = None,
        freq: int = 1000000,
        mode: int = 0,
        bus_id: int = 1
    ):
        """
        Initialize SPI bus.
        
        Args:
            sck: Clock pin
            mosi: Master Out Slave In pin
            miso: Master In Slave Out pin
            cs: Chip Select pin (optional)
            freq: Clock frequency in Hz
            mode: SPI mode (0-3)
            bus_id: SPI bus ID
        """
        config = BusConfig(
            bus_type=BusType.SPI,
            pins={"sck": sck, "mosi": mosi, "miso": miso, "cs": cs},
            speed=freq,
            mode=mode,
            extra={"bus_id": bus_id}
        )
        super().__init__(config)
        
        self._sck = sck
        self._mosi = mosi
        self._miso = miso
        self._cs = cs
        self._freq = freq
        self._mode = mode
        self._bus_id = bus_id
        self._spi = None
        self._cs_pin = None
    
    def init(self) -> bool:
        """Initialize the SPI bus."""
        try:
            # Try MicroPython
            try:
                from machine import SPI, Pin
                
                polarity = self._mode >> 1
                phase = self._mode & 1
                
                self._spi = SPI(
                    self._bus_id,
                    baudrate=self._freq,
                    polarity=polarity,
                    phase=phase,
                    sck=Pin(self._sck),
                    mosi=Pin(self._mosi),
                    miso=Pin(self._miso)
                )
                
                if self._cs is not None:
                    self._cs_pin = Pin(self._cs, Pin.OUT)
                    self._cs_pin.value(1)  # Deselect
                
                self._simulation_mode = False
                self._initialized = True
                return True
            except ImportError:
                pass
            
            # Fall back to simulation
            self._simulation_mode = True
            self._initialized = True
            return True
            
        except Exception as e:
            print(f"SPI init error: {e}")
            return False
    
    def deinit(self) -> None:
        """Deinitialize the SPI bus."""
        if self._spi and hasattr(self._spi, 'deinit'):
            self._spi.deinit()
        self._spi = None
        self._initialized = False
    
    def scan(self) -> List[int]:
        """SPI doesn't support scanning - return empty list."""
        return []
    
    def select(self) -> None:
        """Assert chip select (low)."""
        if self._cs_pin:
            self._cs_pin.value(0)
    
    def deselect(self) -> None:
        """Deassert chip select (high)."""
        if self._cs_pin:
            self._cs_pin.value(1)
    
    def transfer(self, data: bytes, read: bool = True) -> Optional[bytes]:
        """
        Transfer data over SPI.
        
        Args:
            data: Bytes to send
            read: Whether to read response
            
        Returns:
            Response bytes if read=True
        """
        if not self._initialized:
            self.init()
        
        if self._simulation_mode:
            return bytes([0] * len(data)) if read else None
        
        self.select()
        try:
            if read:
                result = bytearray(len(data))
                self._spi.write_readinto(data, result)
                return bytes(result)
            else:
                self._spi.write(data)
                return None
        finally:
            self.deselect()
    
    def write(self, data: bytes) -> None:
        """Write data without reading response."""
        self.transfer(data, read=False)
    
    def read(self, num_bytes: int, write_value: int = 0) -> bytes:
        """
        Read bytes from SPI.
        
        Args:
            num_bytes: Number of bytes to read
            write_value: Value to write while reading (usually 0 or 0xFF)
            
        Returns:
            Bytes read
        """
        return self.transfer(bytes([write_value] * num_bytes))
    
    def __repr__(self) -> str:
        mode = "SIM" if self._simulation_mode else "HW"
        return f"<SPIBus [{mode}] SCK={self._sck} MOSI={self._mosi} MISO={self._miso} {self._freq}Hz>"


# Register with factory
BusFactory.register("SPI", SPIBus)
