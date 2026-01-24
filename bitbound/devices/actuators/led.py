"""
LED actuators.
"""

from typing import Any, Dict, List, Tuple, Optional
import time
from ...device import Actuator, DeviceInfo


class LED(Actuator):
    """
    Single LED.
    
    Example:
        from bitbound import Hardware
        
        hw = Hardware()
        led = hw.attach("GPIO", type="LED", pin=2)
        
        led.on()
        led.off()
        led.blink(times=3)
    """
    
    def __init__(self, bus, pin: int, active_low: bool = False, name: str = "LED"):
        """
        Initialize LED.
        
        Args:
            bus: GPIO bus instance
            pin: Control pin
            active_low: True if LED is active on LOW
            name: Device name
        """
        super().__init__(bus, pin, name)
        
        self._pin = pin
        self._active_low = active_low
        self._gpio_pin = None
        self._state = False
    
    def connect(self) -> bool:
        """Connect to LED."""
        try:
            if hasattr(self._bus, 'output'):
                self._gpio_pin = self._bus.output(self._pin)
                self.off()
            
            self._connected = True
            return True
        except Exception as e:
            print(f"LED connect error: {e}")
            return False
    
    def disconnect(self) -> None:
        """Disconnect from LED."""
        self.off()
        self._connected = False
    
    def get_info(self) -> DeviceInfo:
        """Get device information."""
        return DeviceInfo(
            device_type="actuator",
            name=self._name,
            model="LED",
            address=self._pin,
            bus_type="GPIO",
            capabilities=["on", "off", "toggle", "blink"]
        )
    
    def on(self) -> None:
        """Turn LED ON."""
        if self._gpio_pin:
            self._gpio_pin.value = 0 if self._active_low else 1
        self._state = True
    
    def off(self) -> None:
        """Turn LED OFF."""
        if self._gpio_pin:
            self._gpio_pin.value = 1 if self._active_low else 0
        self._state = False
    
    def toggle(self) -> None:
        """Toggle LED state."""
        if self._state:
            self.off()
        else:
            self.on()
    
    def blink(self, times: int = 1, on_time: float = 0.5, off_time: float = 0.5) -> None:
        """
        Blink LED.
        
        Args:
            times: Number of blinks
            on_time: ON time in seconds
            off_time: OFF time in seconds
        """
        for _ in range(times):
            self.on()
            time.sleep(on_time)
            self.off()
            time.sleep(off_time)
    
    @property
    def state(self) -> bool:
        """Get current state."""
        return self._state
    
    def read_all(self) -> Dict[str, Any]:
        """Read all values."""
        return {"state": self._state}


class RGBLed(Actuator):
    """
    RGB LED (common cathode or anode).
    
    Example:
        from bitbound import Hardware
        
        hw = Hardware()
        rgb = hw.attach("GPIO", type="RGB", pins={"r": 12, "g": 13, "b": 14})
        
        rgb.color = (255, 0, 0)    # Red
        rgb.color = "#00FF00"      # Green
        rgb.color = "blue"         # Blue
    """
    
    # Named colors
    COLORS = {
        "red": (255, 0, 0),
        "green": (0, 255, 0),
        "blue": (0, 0, 255),
        "white": (255, 255, 255),
        "yellow": (255, 255, 0),
        "cyan": (0, 255, 255),
        "magenta": (255, 0, 255),
        "orange": (255, 165, 0),
        "purple": (128, 0, 128),
        "off": (0, 0, 0),
    }
    
    def __init__(
        self,
        bus,
        pins: Dict[str, int],
        common_anode: bool = False,
        freq: int = 1000,
        name: str = "RGB"
    ):
        """
        Initialize RGB LED.
        
        Args:
            bus: GPIO bus instance
            pins: Dict with "r", "g", "b" pins
            common_anode: True if common anode
            freq: PWM frequency
            name: Device name
        """
        super().__init__(bus, None, name)
        
        self._pins = pins
        self._common_anode = common_anode
        self._freq = freq
        
        self._color = (0, 0, 0)
    
    def connect(self) -> bool:
        """Connect to RGB LED."""
        try:
            if hasattr(self._bus, 'pwm'):
                self._bus.pwm(self._pins["r"], self._freq, 0)
                self._bus.pwm(self._pins["g"], self._freq, 0)
                self._bus.pwm(self._pins["b"], self._freq, 0)
            
            self._connected = True
            return True
        except Exception as e:
            print(f"RGB connect error: {e}")
            return False
    
    def disconnect(self) -> None:
        """Disconnect from RGB LED."""
        self.off()
        self._connected = False
    
    def get_info(self) -> DeviceInfo:
        """Get device information."""
        return DeviceInfo(
            device_type="actuator",
            name=self._name,
            model="RGB LED",
            bus_type="GPIO",
            capabilities=["color", "on", "off"]
        )
    
    def on(self) -> None:
        """Turn on (white)."""
        self.color = (255, 255, 255)
    
    def off(self) -> None:
        """Turn off."""
        self.color = (0, 0, 0)
    
    @property
    def color(self) -> Tuple[int, int, int]:
        """Get current color."""
        return self._color
    
    @color.setter
    def color(self, value) -> None:
        """
        Set color.
        
        Args:
            value: Color name, hex string, or (r, g, b) tuple
        """
        if isinstance(value, str):
            if value.lower() in self.COLORS:
                value = self.COLORS[value.lower()]
            elif value.startswith("#"):
                # Parse hex color
                value = value.lstrip("#")
                value = tuple(int(value[i:i+2], 16) for i in (0, 2, 4))
            else:
                value = (0, 0, 0)
        
        r, g, b = value
        
        # Invert for common anode
        if self._common_anode:
            r, g, b = 255 - r, 255 - g, 255 - b
        
        # Convert 0-255 to 0-100 for PWM
        if hasattr(self._bus, 'set_pwm_duty'):
            self._bus.set_pwm_duty(self._pins["r"], r * 100 // 255)
            self._bus.set_pwm_duty(self._pins["g"], g * 100 // 255)
            self._bus.set_pwm_duty(self._pins["b"], b * 100 // 255)
        
        self._color = (r, g, b) if not self._common_anode else value
    
    def fade(
        self,
        from_color: Tuple[int, int, int],
        to_color: Tuple[int, int, int],
        duration: float = 1.0,
        steps: int = 50
    ) -> None:
        """
        Fade from one color to another.
        
        Args:
            from_color: Start color
            to_color: End color
            duration: Fade duration in seconds
            steps: Number of steps
        """
        delay = duration / steps
        
        for i in range(steps + 1):
            t = i / steps
            r = int(from_color[0] + (to_color[0] - from_color[0]) * t)
            g = int(from_color[1] + (to_color[1] - from_color[1]) * t)
            b = int(from_color[2] + (to_color[2] - from_color[2]) * t)
            self.color = (r, g, b)
            time.sleep(delay)
    
    def read_all(self) -> Dict[str, Any]:
        """Read all values."""
        return {"color": self._color}


class NeoPixel(Actuator):
    """
    WS2812/NeoPixel LED strip.
    
    Example:
        from bitbound import Hardware
        
        hw = Hardware()
        strip = hw.attach("GPIO", type="NeoPixel", pin=16, num_leds=30)
        
        strip.fill((255, 0, 0))         # All red
        strip[0] = (0, 255, 0)          # First LED green
        strip.rainbow()                  # Rainbow effect
    """
    
    def __init__(
        self,
        bus,
        pin: int,
        num_leds: int = 8,
        brightness: float = 0.5,
        name: str = "NeoPixel"
    ):
        """
        Initialize NeoPixel strip.
        
        Args:
            bus: GPIO bus instance
            pin: Data pin
            num_leds: Number of LEDs
            brightness: Brightness (0.0 - 1.0)
            name: Device name
        """
        super().__init__(bus, pin, name)
        
        self._pin = pin
        self._num_leds = num_leds
        self._brightness = brightness
        
        self._np = None
        self._pixels: List[Tuple[int, int, int]] = [(0, 0, 0)] * num_leds
    
    def connect(self) -> bool:
        """Connect to NeoPixel strip."""
        try:
            try:
                from machine import Pin
                from neopixel import NeoPixel as NP
                
                self._np = NP(Pin(self._pin), self._num_leds)
                self._connected = True
            except ImportError:
                # Simulation mode
                self._connected = True
            return True
        except Exception as e:
            print(f"NeoPixel connect error: {e}")
            return False
    
    def disconnect(self) -> None:
        """Disconnect from strip."""
        self.off()
        self._connected = False
    
    def get_info(self) -> DeviceInfo:
        """Get device information."""
        return DeviceInfo(
            device_type="actuator",
            name=self._name,
            model="NeoPixel",
            address=self._pin,
            bus_type="GPIO",
            capabilities=["fill", "pixel", "rainbow"],
            properties={"num_leds": self._num_leds}
        )
    
    def on(self) -> None:
        """Turn on (white)."""
        self.fill((255, 255, 255))
    
    def off(self) -> None:
        """Turn off."""
        self.fill((0, 0, 0))
    
    def _apply_brightness(self, color: Tuple[int, int, int]) -> Tuple[int, int, int]:
        """Apply brightness to color."""
        return tuple(int(c * self._brightness) for c in color)
    
    def _write(self) -> None:
        """Write pixels to hardware."""
        if self._np:
            for i, color in enumerate(self._pixels):
                self._np[i] = self._apply_brightness(color)
            self._np.write()
    
    def fill(self, color: Tuple[int, int, int]) -> None:
        """Fill all LEDs with a color."""
        self._pixels = [color] * self._num_leds
        self._write()
    
    def clear(self) -> None:
        """Clear all LEDs."""
        self.fill((0, 0, 0))
    
    def __getitem__(self, index: int) -> Tuple[int, int, int]:
        """Get pixel color."""
        return self._pixels[index]
    
    def __setitem__(self, index: int, color: Tuple[int, int, int]) -> None:
        """Set pixel color."""
        self._pixels[index] = color
        self._write()
    
    def __len__(self) -> int:
        """Get number of LEDs."""
        return self._num_leds
    
    @property
    def brightness(self) -> float:
        """Get brightness."""
        return self._brightness
    
    @brightness.setter
    def brightness(self, value: float) -> None:
        """Set brightness."""
        self._brightness = max(0.0, min(1.0, value))
        self._write()
    
    def rainbow(self, delay_ms: int = 20) -> None:
        """Display rainbow effect."""
        for j in range(256):
            for i in range(self._num_leds):
                pos = (i * 256 // self._num_leds + j) & 255
                self._pixels[i] = self._wheel(pos)
            self._write()
            time.sleep(delay_ms / 1000.0)
    
    def _wheel(self, pos: int) -> Tuple[int, int, int]:
        """Generate rainbow colors."""
        if pos < 85:
            return (255 - pos * 3, pos * 3, 0)
        elif pos < 170:
            pos -= 85
            return (0, 255 - pos * 3, pos * 3)
        else:
            pos -= 170
            return (pos * 3, 0, 255 - pos * 3)
    
    def read_all(self) -> Dict[str, Any]:
        """Read all values."""
        return {"pixels": self._pixels.copy(), "brightness": self._brightness}
