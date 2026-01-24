"""
UART (Serial) Bus implementation.
"""

from typing import List, Optional
from .base import Bus, BusConfig, BusType, BusFactory


class UARTBus(Bus):
    """
    UART (Universal Asynchronous Receiver-Transmitter) bus implementation.
    
    Example:
        uart = UARTBus(tx=17, rx=16, baudrate=115200)
        uart.init()
        
        uart.write(b"Hello\\n")
        response = uart.read(10)
    """
    
    def __init__(
        self,
        tx: int = 17,
        rx: int = 16,
        baudrate: int = 115200,
        bits: int = 8,
        parity: Optional[str] = None,
        stop: int = 1,
        uart_id: int = 1
    ):
        """
        Initialize UART bus.
        
        Args:
            tx: Transmit pin
            rx: Receive pin
            baudrate: Baud rate
            bits: Data bits (5, 6, 7, or 8)
            parity: Parity ('E', 'O', or None)
            stop: Stop bits (1 or 2)
            uart_id: UART peripheral ID
        """
        config = BusConfig(
            bus_type=BusType.UART,
            pins={"tx": tx, "rx": rx},
            speed=baudrate,
            extra={"bits": bits, "parity": parity, "stop": stop, "uart_id": uart_id}
        )
        super().__init__(config)
        
        self._tx = tx
        self._rx = rx
        self._baudrate = baudrate
        self._bits = bits
        self._parity = parity
        self._stop = stop
        self._uart_id = uart_id
        self._uart = None
        
        # Simulation buffer
        self._sim_rx_buffer = bytearray()
    
    def init(self) -> bool:
        """Initialize UART."""
        try:
            from machine import UART, Pin
            
            parity_val = None
            if self._parity == 'E':
                parity_val = 0
            elif self._parity == 'O':
                parity_val = 1
            
            self._uart = UART(
                self._uart_id,
                baudrate=self._baudrate,
                bits=self._bits,
                parity=parity_val,
                stop=self._stop,
                tx=Pin(self._tx),
                rx=Pin(self._rx)
            )
            
            self._simulation_mode = False
            self._initialized = True
            return True
            
        except ImportError:
            self._simulation_mode = True
            self._initialized = True
            return True
    
    def deinit(self) -> None:
        """Deinitialize UART."""
        if self._uart and hasattr(self._uart, 'deinit'):
            self._uart.deinit()
        self._uart = None
        self._initialized = False
    
    def scan(self) -> List[int]:
        """UART doesn't support scanning."""
        return []
    
    def write(self, data: bytes) -> int:
        """
        Write data to UART.
        
        Args:
            data: Bytes to write
            
        Returns:
            Number of bytes written
        """
        if not self._initialized:
            self.init()
        
        if self._simulation_mode:
            return len(data)
        
        return self._uart.write(data)
    
    def read(self, num_bytes: int = -1, timeout_ms: int = 1000) -> bytes:
        """
        Read data from UART.
        
        Args:
            num_bytes: Number of bytes to read (-1 for all available)
            timeout_ms: Read timeout in milliseconds
            
        Returns:
            Bytes read
        """
        if not self._initialized:
            self.init()
        
        if self._simulation_mode:
            if num_bytes == -1:
                data = bytes(self._sim_rx_buffer)
                self._sim_rx_buffer.clear()
                return data
            else:
                data = bytes(self._sim_rx_buffer[:num_bytes])
                self._sim_rx_buffer = self._sim_rx_buffer[num_bytes:]
                return data
        
        if num_bytes == -1:
            return self._uart.read() or b''
        return self._uart.read(num_bytes) or b''
    
    def readline(self, timeout_ms: int = 1000) -> bytes:
        """
        Read a line from UART.
        
        Args:
            timeout_ms: Read timeout
            
        Returns:
            Line read (including newline)
        """
        if not self._initialized:
            self.init()
        
        if self._simulation_mode:
            return b''
        
        return self._uart.readline() or b''
    
    def any(self) -> int:
        """
        Check how many bytes are available.
        
        Returns:
            Number of bytes available
        """
        if self._simulation_mode:
            return len(self._sim_rx_buffer)
        
        if self._uart:
            return self._uart.any()
        return 0
    
    def flush(self) -> None:
        """Flush UART buffers."""
        if self._simulation_mode:
            self._sim_rx_buffer.clear()
        elif self._uart and hasattr(self._uart, 'flush'):
            self._uart.flush()
    
    def sim_receive(self, data: bytes) -> None:
        """Simulate receiving data (for testing)."""
        self._sim_rx_buffer.extend(data)
    
    def __repr__(self) -> str:
        mode = "SIM" if self._simulation_mode else "HW"
        return f"<UARTBus [{mode}] TX={self._tx} RX={self._rx} {self._baudrate}bps>"


# Register with factory
BusFactory.register("UART", UARTBus)
BusFactory.register("SERIAL", UARTBus)
