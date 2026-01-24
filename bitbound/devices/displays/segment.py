"""
7-Segment Display.
"""

from typing import Any, Dict, List
from ...device import Display, DeviceInfo


class SevenSegmentDisplay(Display):
    """
    7-Segment LED Display.
    
    Example:
        from bitbound import Hardware
        
        hw = Hardware()
        seg = hw.attach("GPIO", type="7Segment",
                       pins=[2,3,4,5,6,7,8], common_cathode=True)
        
        seg.digit(5)        # Display "5"
        seg.number(1234)    # Display "1234" (if 4-digit)
    """
    
    # Segment patterns for digits (a,b,c,d,e,f,g)
    DIGITS = {
        0: 0b0111111,  # 0
        1: 0b0000110,  # 1
        2: 0b1011011,  # 2
        3: 0b1001111,  # 3
        4: 0b1100110,  # 4
        5: 0b1101101,  # 5
        6: 0b1111101,  # 6
        7: 0b0000111,  # 7
        8: 0b1111111,  # 8
        9: 0b1101111,  # 9
        'A': 0b1110111,
        'b': 0b1111100,
        'C': 0b0111001,
        'd': 0b1011110,
        'E': 0b1111001,
        'F': 0b1110001,
        '-': 0b1000000,
        '_': 0b0001000,
        ' ': 0b0000000,
    }
    
    def __init__(
        self,
        bus,
        pins: List[int],
        common_cathode: bool = True,
        num_digits: int = 1,
        digit_pins: List[int] = None,
        name: str = "7Segment"
    ):
        """
        Initialize 7-segment display.
        
        Args:
            bus: GPIO bus instance
            pins: List of 7 segment pins [a,b,c,d,e,f,g]
            common_cathode: True for common cathode, False for common anode
            num_digits: Number of digits (for multi-digit displays)
            digit_pins: Pins for digit selection (multi-digit)
            name: Device name
        """
        super().__init__(bus, None, name)
        
        self._pins = pins
        self._common_cathode = common_cathode
        self._num_digits = num_digits
        self._digit_pins = digit_pins or []
        
        self._gpio_pins = []
        self._gpio_digits = []
        self._current_value = 0
    
    def connect(self) -> bool:
        """Connect to display."""
        try:
            if hasattr(self._bus, 'output'):
                # Segment pins
                for pin in self._pins:
                    self._gpio_pins.append(self._bus.output(pin))
                
                # Digit select pins
                for pin in self._digit_pins:
                    self._gpio_digits.append(self._bus.output(pin))
            
            self.clear()
            self._connected = True
            return True
        except Exception as e:
            print(f"7Segment connect error: {e}")
            return False
    
    def disconnect(self) -> None:
        """Disconnect from display."""
        self.clear()
        self._connected = False
    
    def get_info(self) -> DeviceInfo:
        """Get device information."""
        return DeviceInfo(
            device_type="display",
            name=self._name,
            model="7-Segment",
            bus_type="GPIO",
            capabilities=["digit", "number"],
            properties={"num_digits": self._num_digits}
        )
    
    def clear(self) -> None:
        """Clear the display."""
        for pin in self._gpio_pins:
            pin.value = 0 if self._common_cathode else 1
    
    def write(self, text: str, x: int = 0, y: int = 0) -> None:
        """Write text to display."""
        # Try to parse as number
        try:
            self.number(int(text))
        except ValueError:
            # Display first character
            if text:
                self.char(text[0])
    
    def _set_segments(self, pattern: int) -> None:
        """Set segment pattern."""
        for i, pin in enumerate(self._gpio_pins):
            bit = (pattern >> i) & 1
            if self._common_cathode:
                pin.value = bit
            else:
                pin.value = 1 - bit
    
    def digit(self, value: int, dp: bool = False) -> None:
        """
        Display a single digit.
        
        Args:
            value: Digit (0-9)
            dp: Show decimal point
        """
        if value in self.DIGITS:
            pattern = self.DIGITS[value]
            if dp and len(self._gpio_pins) > 7:
                pattern |= 0b10000000
            self._set_segments(pattern)
            self._current_value = value
    
    def char(self, c: str) -> None:
        """Display a character."""
        c = c.upper()
        if c in self.DIGITS:
            self._set_segments(self.DIGITS[c])
        elif c.isdigit():
            self.digit(int(c))
    
    def number(self, value: int) -> None:
        """
        Display a number (multi-digit).
        
        Args:
            value: Number to display
        """
        if self._num_digits == 1:
            self.digit(value % 10)
            return
        
        # For multi-digit displays, would need multiplexing
        # This is a simplified version
        self._current_value = value
        self.digit(value % 10)
    
    def read_all(self) -> Dict[str, Any]:
        """Read all values."""
        return {"value": self._current_value}
