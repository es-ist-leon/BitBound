"""
Buzzer actuator.
"""

from typing import Any, Dict, List, Tuple, Optional
import time
from ...device import Actuator, DeviceInfo


class Buzzer(Actuator):
    """
    Piezo Buzzer with tone generation.
    
    Example:
        from bitbound import Hardware
        
        hw = Hardware()
        buzzer = hw.attach("GPIO", type="Buzzer", pin=15)
        
        buzzer.beep()
        buzzer.tone(440, duration=0.5)   # A4 note for 0.5s
        buzzer.play_melody([(262, 0.5), (294, 0.5), (330, 0.5)])  # C, D, E
    """
    
    # Note frequencies (Hz)
    NOTES = {
        "C3": 131, "D3": 147, "E3": 165, "F3": 175, "G3": 196, "A3": 220, "B3": 247,
        "C4": 262, "D4": 294, "E4": 330, "F4": 349, "G4": 392, "A4": 440, "B4": 494,
        "C5": 523, "D5": 587, "E5": 659, "F5": 698, "G5": 784, "A5": 880, "B5": 988,
        "C6": 1047, "D6": 1175, "E6": 1319, "F6": 1397, "G6": 1568, "A6": 1760, "B6": 1976,
        "REST": 0, "R": 0, "_": 0,
    }
    
    # Common melodies
    MELODIES = {
        "startup": [("C4", 0.1), ("E4", 0.1), ("G4", 0.2)],
        "success": [("C5", 0.1), ("E5", 0.1), ("G5", 0.3)],
        "error": [("G4", 0.1), ("REST", 0.05), ("G4", 0.1), ("REST", 0.05), ("E4", 0.3)],
        "alert": [("A5", 0.1), ("REST", 0.1)] * 3,
    }
    
    def __init__(
        self,
        bus,
        pin: int,
        active_buzzer: bool = False,
        name: str = "Buzzer"
    ):
        """
        Initialize buzzer.
        
        Args:
            bus: GPIO bus instance
            pin: Control pin
            active_buzzer: True for active buzzer (no PWM needed)
            name: Device name
        """
        super().__init__(bus, pin, name)
        
        self._pin = pin
        self._active_buzzer = active_buzzer
        self._gpio_pin = None
        self._pwm = None
        self._playing = False
    
    def connect(self) -> bool:
        """Connect to buzzer."""
        try:
            if self._active_buzzer:
                if hasattr(self._bus, 'output'):
                    self._gpio_pin = self._bus.output(self._pin)
            else:
                try:
                    from machine import Pin, PWM
                    self._pwm = PWM(Pin(self._pin))
                    self._pwm.duty_u16(0)
                except ImportError:
                    pass
            
            self._connected = True
            return True
        except Exception as e:
            print(f"Buzzer connect error: {e}")
            return False
    
    def disconnect(self) -> None:
        """Disconnect from buzzer."""
        self.off()
        if self._pwm:
            self._pwm.deinit()
        self._connected = False
    
    def get_info(self) -> DeviceInfo:
        """Get device information."""
        return DeviceInfo(
            device_type="actuator",
            name=self._name,
            model="Buzzer",
            address=self._pin,
            bus_type="GPIO",
            capabilities=["beep", "tone", "melody"]
        )
    
    def on(self) -> None:
        """Turn buzzer ON (for active buzzer or continuous tone)."""
        if self._active_buzzer:
            if self._gpio_pin:
                self._gpio_pin.on()
        else:
            self.tone(1000)  # Default 1kHz tone
        self._playing = True
    
    def off(self) -> None:
        """Turn buzzer OFF."""
        if self._active_buzzer:
            if self._gpio_pin:
                self._gpio_pin.off()
        elif self._pwm:
            self._pwm.duty_u16(0)
        self._playing = False
    
    def beep(self, duration: float = 0.1, freq: int = 1000) -> None:
        """
        Short beep.
        
        Args:
            duration: Beep duration in seconds
            freq: Frequency in Hz
        """
        self.tone(freq, duration)
    
    def tone(self, freq: int, duration: Optional[float] = None) -> None:
        """
        Play a tone.
        
        Args:
            freq: Frequency in Hz (0 for silence)
            duration: Duration in seconds (None for continuous)
        """
        if self._active_buzzer:
            if freq > 0:
                if self._gpio_pin:
                    self._gpio_pin.on()
                self._playing = True
            else:
                self.off()
        elif self._pwm:
            if freq > 0:
                self._pwm.freq(freq)
                self._pwm.duty_u16(32768)  # 50% duty
                self._playing = True
            else:
                self._pwm.duty_u16(0)
                self._playing = False
        
        if duration is not None:
            time.sleep(duration)
            self.off()
    
    def note(self, note_name: str, duration: float = 0.25) -> None:
        """
        Play a musical note.
        
        Args:
            note_name: Note name (e.g., "C4", "A4")
            duration: Duration in seconds
        """
        freq = self.NOTES.get(note_name.upper(), 0)
        self.tone(freq, duration)
    
    def play_melody(
        self,
        melody: List[Tuple[Any, float]],
        tempo: float = 1.0
    ) -> None:
        """
        Play a melody.
        
        Args:
            melody: List of (note/freq, duration) tuples
            tempo: Tempo multiplier
        """
        for item, duration in melody:
            duration = duration / tempo
            
            if isinstance(item, str):
                # Note name
                freq = self.NOTES.get(item.upper(), 0)
            else:
                # Frequency
                freq = item
            
            if freq > 0:
                self.tone(freq, duration * 0.9)
                time.sleep(duration * 0.1)  # Small gap between notes
            else:
                time.sleep(duration)
    
    def play_preset(self, name: str, tempo: float = 1.0) -> None:
        """
        Play a preset melody.
        
        Args:
            name: Preset name ("startup", "success", "error", "alert")
            tempo: Tempo multiplier
        """
        if name in self.MELODIES:
            self.play_melody(self.MELODIES[name], tempo)
    
    @property
    def playing(self) -> bool:
        """Check if buzzer is currently playing."""
        return self._playing
    
    def read_all(self) -> Dict[str, Any]:
        """Read all values."""
        return {"playing": self._playing}
