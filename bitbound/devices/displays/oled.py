"""
OLED Displays.
"""

from typing import Any, Dict, List, Tuple, Optional
from ...device import Display, DeviceInfo


class OLEDDisplay(Display):
    """Base class for OLED displays."""
    pass


class SSD1306Display(OLEDDisplay):
    """
    SSD1306 OLED Display (128x64 or 128x32).
    
    Example:
        from bitbound import Hardware
        
        hw = Hardware()
        oled = hw.attach("I2C", type="SSD1306")
        
        oled.text("Hello World!", 0, 0)
        oled.line(0, 10, 127, 10)
        oled.show()
    """
    
    DEFAULT_ADDRESS = 0x3C
    ALT_ADDRESS = 0x3D
    
    # SSD1306 Commands
    CMD_SET_CONTRAST = 0x81
    CMD_DISPLAY_ALL_ON_RESUME = 0xA4
    CMD_DISPLAY_ALL_ON = 0xA5
    CMD_NORMAL_DISPLAY = 0xA6
    CMD_INVERT_DISPLAY = 0xA7
    CMD_DISPLAY_OFF = 0xAE
    CMD_DISPLAY_ON = 0xAF
    CMD_SET_DISPLAY_OFFSET = 0xD3
    CMD_SET_COM_PINS = 0xDA
    CMD_SET_VCOM_DETECT = 0xDB
    CMD_SET_DISPLAY_CLOCK_DIV = 0xD5
    CMD_SET_PRECHARGE = 0xD9
    CMD_SET_MULTIPLEX = 0xA8
    CMD_SET_LOW_COLUMN = 0x00
    CMD_SET_HIGH_COLUMN = 0x10
    CMD_SET_START_LINE = 0x40
    CMD_MEMORY_MODE = 0x20
    CMD_COLUMN_ADDR = 0x21
    CMD_PAGE_ADDR = 0x22
    CMD_COM_SCAN_INC = 0xC0
    CMD_COM_SCAN_DEC = 0xC8
    CMD_SEG_REMAP = 0xA0
    CMD_CHARGE_PUMP = 0x8D
    
    def __init__(
        self,
        bus,
        address: int = DEFAULT_ADDRESS,
        width: int = 128,
        height: int = 64,
        name: str = "SSD1306"
    ):
        """
        Initialize SSD1306 display.
        
        Args:
            bus: I2C bus instance
            address: I2C address
            width: Display width in pixels
            height: Display height in pixels
            name: Device name
        """
        super().__init__(bus, address, name)
        
        self._width = width
        self._height = height
        self._pages = height // 8
        
        # Frame buffer
        self._buffer = bytearray(width * self._pages)
        
        # Try to use framebuf if available
        self._fb = None
    
    def connect(self) -> bool:
        """Connect to display."""
        try:
            if not self._bus.is_simulation:
                self._init_display()
            
            # Try to create framebuffer
            try:
                import framebuf
                self._fb = framebuf.FrameBuffer(
                    self._buffer,
                    self._width,
                    self._height,
                    framebuf.MONO_VLSB
                )
            except ImportError:
                pass
            
            self._connected = True
            return True
        except Exception as e:
            print(f"SSD1306 connect error: {e}")
            self._connected = True  # Simulation
            return True
    
    def _init_display(self) -> None:
        """Initialize the display."""
        init_cmds = [
            self.CMD_DISPLAY_OFF,
            self.CMD_SET_DISPLAY_CLOCK_DIV, 0x80,
            self.CMD_SET_MULTIPLEX, self._height - 1,
            self.CMD_SET_DISPLAY_OFFSET, 0x00,
            self.CMD_SET_START_LINE | 0x00,
            self.CMD_CHARGE_PUMP, 0x14,  # Enable charge pump
            self.CMD_MEMORY_MODE, 0x00,  # Horizontal addressing mode
            self.CMD_SEG_REMAP | 0x01,
            self.CMD_COM_SCAN_DEC,
            self.CMD_SET_COM_PINS, 0x12 if self._height == 64 else 0x02,
            self.CMD_SET_CONTRAST, 0xCF,
            self.CMD_SET_PRECHARGE, 0xF1,
            self.CMD_SET_VCOM_DETECT, 0x40,
            self.CMD_DISPLAY_ALL_ON_RESUME,
            self.CMD_NORMAL_DISPLAY,
            self.CMD_DISPLAY_ON,
        ]
        
        for cmd in init_cmds:
            self._command(cmd)
    
    def _command(self, cmd: int) -> None:
        """Send command to display."""
        if not self._bus.is_simulation:
            self._bus.write_to(self._address, bytes([0x00, cmd]))
    
    def disconnect(self) -> None:
        """Disconnect from display."""
        self._command(self.CMD_DISPLAY_OFF)
        self._connected = False
    
    def get_info(self) -> DeviceInfo:
        """Get device information."""
        return DeviceInfo(
            device_type="display",
            name=self._name,
            model="SSD1306",
            address=self._address,
            bus_type="I2C",
            capabilities=["pixel", "text", "line", "rect", "fill"],
            properties={"width": self._width, "height": self._height}
        )
    
    def clear(self) -> None:
        """Clear the display buffer."""
        for i in range(len(self._buffer)):
            self._buffer[i] = 0
    
    def fill(self, color: int = 1) -> None:
        """Fill the display with a color."""
        val = 0xFF if color else 0x00
        for i in range(len(self._buffer)):
            self._buffer[i] = val
    
    def pixel(self, x: int, y: int, color: int = 1) -> None:
        """
        Set a pixel.
        
        Args:
            x: X coordinate
            y: Y coordinate
            color: 0=off, 1=on
        """
        if 0 <= x < self._width and 0 <= y < self._height:
            page = y // 8
            bit = y % 8
            idx = x + page * self._width
            
            if color:
                self._buffer[idx] |= (1 << bit)
            else:
                self._buffer[idx] &= ~(1 << bit)
    
    def line(self, x0: int, y0: int, x1: int, y1: int, color: int = 1) -> None:
        """Draw a line using Bresenham's algorithm."""
        dx = abs(x1 - x0)
        dy = abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy
        
        while True:
            self.pixel(x0, y0, color)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x0 += sx
            if e2 < dx:
                err += dx
                y0 += sy
    
    def rect(self, x: int, y: int, w: int, h: int, color: int = 1) -> None:
        """Draw a rectangle outline."""
        self.line(x, y, x + w - 1, y, color)
        self.line(x, y + h - 1, x + w - 1, y + h - 1, color)
        self.line(x, y, x, y + h - 1, color)
        self.line(x + w - 1, y, x + w - 1, y + h - 1, color)
    
    def fill_rect(self, x: int, y: int, w: int, h: int, color: int = 1) -> None:
        """Draw a filled rectangle."""
        for i in range(w):
            for j in range(h):
                self.pixel(x + i, y + j, color)
    
    def text(self, text: str, x: int, y: int, color: int = 1) -> None:
        """
        Draw text (requires framebuf).
        
        Args:
            text: Text to draw
            x: X position
            y: Y position
            color: Text color
        """
        if self._fb:
            self._fb.text(text, x, y, color)
        else:
            # Basic text rendering without framebuf
            # (simplified, just for simulation display)
            pass
    
    def write(self, text: str, x: int = 0, y: int = 0) -> None:
        """Write text to display (Display interface)."""
        self.text(text, x, y)
        self.show()
    
    def show(self) -> None:
        """Update the display with buffer contents."""
        if self._bus.is_simulation:
            return
        
        # Set column and page address
        self._command(self.CMD_COLUMN_ADDR)
        self._command(0)
        self._command(self._width - 1)
        self._command(self.CMD_PAGE_ADDR)
        self._command(0)
        self._command(self._pages - 1)
        
        # Send buffer data
        # Split into chunks for I2C
        chunk_size = 32
        for i in range(0, len(self._buffer), chunk_size):
            chunk = bytes([0x40]) + self._buffer[i:i + chunk_size]
            self._bus.write_to(self._address, chunk)
    
    @property
    def width(self) -> int:
        """Get display width."""
        return self._width
    
    @property
    def height(self) -> int:
        """Get display height."""
        return self._height
    
    def invert(self, value: bool) -> None:
        """Invert display colors."""
        self._command(self.CMD_INVERT_DISPLAY if value else self.CMD_NORMAL_DISPLAY)
    
    def contrast(self, value: int) -> None:
        """Set display contrast (0-255)."""
        self._command(self.CMD_SET_CONTRAST)
        self._command(value & 0xFF)
    
    def read_all(self) -> Dict[str, Any]:
        """Read all values."""
        return {
            "width": self._width,
            "height": self._height,
            "buffer_size": len(self._buffer)
        }
