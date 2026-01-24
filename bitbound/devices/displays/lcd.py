"""
LCD Character Displays.
"""

from typing import Any, Dict, List
import time
from ...device import Display, DeviceInfo


class LCDDisplay(Display):
    """
    Character LCD Display (HD44780 compatible).
    
    Example:
        from bitbound import Hardware
        
        hw = Hardware()
        lcd = hw.attach("I2C", type="LCD1602")
        
        lcd.write("Hello World!")
        lcd.write("Line 2", y=1)
        lcd.clear()
    """
    
    # HD44780 commands
    CMD_CLEAR = 0x01
    CMD_HOME = 0x02
    CMD_ENTRY_MODE = 0x04
    CMD_DISPLAY_CTRL = 0x08
    CMD_SHIFT = 0x10
    CMD_FUNCTION_SET = 0x20
    CMD_SET_CGRAM = 0x40
    CMD_SET_DDRAM = 0x80
    
    # Flags
    FLAG_ENTRY_LEFT = 0x02
    FLAG_DISPLAY_ON = 0x04
    FLAG_CURSOR_ON = 0x02
    FLAG_BLINK_ON = 0x01
    FLAG_2LINE = 0x08
    FLAG_5x10 = 0x04
    FLAG_8BIT = 0x10
    
    # I2C PCF8574 backpack bits
    PCF_RS = 0x01
    PCF_RW = 0x02
    PCF_EN = 0x04
    PCF_BL = 0x08
    
    # Row offsets for common displays
    ROW_OFFSETS_16x2 = [0x00, 0x40]
    ROW_OFFSETS_20x4 = [0x00, 0x40, 0x14, 0x54]
    
    def __init__(
        self,
        bus,
        address: int = 0x27,
        cols: int = 16,
        rows: int = 2,
        name: str = "LCD"
    ):
        """
        Initialize LCD display.
        
        Args:
            bus: I2C bus instance
            address: I2C address (typically 0x27 or 0x3F)
            cols: Number of columns
            rows: Number of rows
            name: Device name
        """
        super().__init__(bus, address, name)
        
        self._cols = cols
        self._rows = rows
        self._backlight = True
        self._display_on = True
        self._cursor_on = False
        self._blink_on = False
        
        # Text buffer for simulation
        self._buffer = [[" "] * cols for _ in range(rows)]
        
        # Row offsets
        if rows <= 2:
            self._row_offsets = self.ROW_OFFSETS_16x2
        else:
            self._row_offsets = self.ROW_OFFSETS_20x4
    
    def connect(self) -> bool:
        """Connect to LCD."""
        try:
            if not self._bus.is_simulation:
                # Initialize in 4-bit mode
                time.sleep(0.05)
                self._write4bits(0x03 << 4)
                time.sleep(0.005)
                self._write4bits(0x03 << 4)
                time.sleep(0.001)
                self._write4bits(0x03 << 4)
                self._write4bits(0x02 << 4)  # 4-bit mode
                
                # Function set: 4-bit, 2 lines, 5x8 dots
                self._command(self.CMD_FUNCTION_SET | self.FLAG_2LINE)
                
                # Display control: display on, cursor off, blink off
                self._update_display_ctrl()
                
                # Clear display
                self.clear()
                
                # Entry mode: left to right
                self._command(self.CMD_ENTRY_MODE | self.FLAG_ENTRY_LEFT)
            
            self._connected = True
            return True
        except Exception as e:
            print(f"LCD connect error: {e}")
            self._connected = True  # Simulation
            return True
    
    def disconnect(self) -> None:
        """Disconnect from LCD."""
        self._connected = False
    
    def get_info(self) -> DeviceInfo:
        """Get device information."""
        return DeviceInfo(
            device_type="display",
            name=self._name,
            model=f"LCD{self._cols}x{self._rows}",
            address=self._address,
            bus_type="I2C",
            capabilities=["write", "clear", "backlight"],
            properties={"cols": self._cols, "rows": self._rows}
        )
    
    def _write4bits(self, data: int) -> None:
        """Write 4 bits to the LCD."""
        if self._bus.is_simulation:
            return
        
        bl = self.PCF_BL if self._backlight else 0
        self._bus.write_to(self._address, bytes([data | bl]))
        self._pulse_enable(data | bl)
    
    def _pulse_enable(self, data: int) -> None:
        """Pulse the enable pin."""
        self._bus.write_to(self._address, bytes([data | self.PCF_EN]))
        time.sleep(0.000001)
        self._bus.write_to(self._address, bytes([data & ~self.PCF_EN]))
        time.sleep(0.00005)
    
    def _command(self, cmd: int) -> None:
        """Send a command to the LCD."""
        self._send(cmd, 0)
    
    def _data(self, data: int) -> None:
        """Send data to the LCD."""
        self._send(data, self.PCF_RS)
    
    def _send(self, data: int, mode: int) -> None:
        """Send a byte to the LCD."""
        high = (data & 0xF0) | mode
        low = ((data << 4) & 0xF0) | mode
        self._write4bits(high)
        self._write4bits(low)
    
    def _update_display_ctrl(self) -> None:
        """Update display control register."""
        ctrl = self.CMD_DISPLAY_CTRL
        if self._display_on:
            ctrl |= self.FLAG_DISPLAY_ON
        if self._cursor_on:
            ctrl |= self.FLAG_CURSOR_ON
        if self._blink_on:
            ctrl |= self.FLAG_BLINK_ON
        self._command(ctrl)
    
    def clear(self) -> None:
        """Clear the display."""
        self._command(self.CMD_CLEAR)
        time.sleep(0.002)
        self._buffer = [[" "] * self._cols for _ in range(self._rows)]
    
    def home(self) -> None:
        """Move cursor to home position."""
        self._command(self.CMD_HOME)
        time.sleep(0.002)
    
    def write(self, text: str, x: int = 0, y: int = 0) -> None:
        """
        Write text to the display.
        
        Args:
            text: Text to write
            x: Column position (0-based)
            y: Row position (0-based)
        """
        # Set cursor position
        if y < self._rows:
            self._command(self.CMD_SET_DDRAM | (self._row_offsets[y] + x))
        
        # Write characters
        for i, char in enumerate(text):
            if x + i >= self._cols:
                break
            self._data(ord(char))
            
            # Update buffer
            if y < self._rows and x + i < self._cols:
                self._buffer[y][x + i] = char
    
    def set_cursor(self, x: int, y: int) -> None:
        """Set cursor position."""
        if y < self._rows:
            self._command(self.CMD_SET_DDRAM | (self._row_offsets[y] + x))
    
    @property
    def backlight(self) -> bool:
        """Get backlight state."""
        return self._backlight
    
    @backlight.setter
    def backlight(self, value: bool) -> None:
        """Set backlight state."""
        self._backlight = value
        if not self._bus.is_simulation:
            bl = self.PCF_BL if value else 0
            self._bus.write_to(self._address, bytes([bl]))
    
    @property
    def cursor(self) -> bool:
        """Get cursor visibility."""
        return self._cursor_on
    
    @cursor.setter
    def cursor(self, value: bool) -> None:
        """Set cursor visibility."""
        self._cursor_on = value
        self._update_display_ctrl()
    
    @property
    def blink(self) -> bool:
        """Get cursor blink state."""
        return self._blink_on
    
    @blink.setter
    def blink(self, value: bool) -> None:
        """Set cursor blink state."""
        self._blink_on = value
        self._update_display_ctrl()
    
    def create_char(self, location: int, pattern: List[int]) -> None:
        """
        Create a custom character.
        
        Args:
            location: Character location (0-7)
            pattern: 8-byte pattern for 5x8 character
        """
        location &= 0x07
        self._command(self.CMD_SET_CGRAM | (location << 3))
        for byte in pattern[:8]:
            self._data(byte)
    
    def read_all(self) -> Dict[str, Any]:
        """Read all values."""
        return {
            "buffer": ["".join(row) for row in self._buffer],
            "backlight": self._backlight
        }


class LCD1602(LCDDisplay):
    """16x2 Character LCD."""
    
    def __init__(self, bus, address: int = 0x27, name: str = "LCD1602"):
        super().__init__(bus, address, cols=16, rows=2, name=name)


class LCD2004(LCDDisplay):
    """20x4 Character LCD."""
    
    def __init__(self, bus, address: int = 0x27, name: str = "LCD2004"):
        super().__init__(bus, address, cols=20, rows=4, name=name)
