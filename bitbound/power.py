"""
Power management for BitBound.

Provides deep sleep, light sleep, watchdog, and battery monitoring
for MicroPython-based microcontrollers.
"""

import time
from typing import Any, Callable, Dict, Optional
from enum import Enum


class SleepMode(Enum):
    """Sleep mode types."""
    LIGHT = "light"
    DEEP = "deep"


class WakeReason(Enum):
    """Wake-up reasons after deep sleep."""
    POWER_ON = "power_on"
    TIMER = "timer"
    GPIO = "gpio"
    TOUCHPAD = "touchpad"
    ULP = "ulp"
    UNKNOWN = "unknown"


class PowerManager:
    """
    Power management for embedded devices.

    Example:
        from bitbound.power import PowerManager

        pm = PowerManager()

        # Deep sleep for 60 seconds
        pm.deep_sleep(duration_ms=60000)

        # Deep sleep with GPIO wake
        pm.set_wake_pin(pin=4, level=0)
        pm.deep_sleep()

        # Watchdog timer
        pm.start_watchdog(timeout_ms=8000)
        pm.feed_watchdog()

        # Battery monitoring
        print(f"Battery: {pm.battery_percent}%")
    """

    def __init__(self, battery_pin: Optional[int] = None, battery_max_v: float = 4.2):
        """
        Initialize power manager.

        Args:
            battery_pin: ADC pin for battery voltage monitoring
            battery_max_v: Maximum battery voltage (fully charged)
        """
        self._simulation = True
        self._battery_pin = battery_pin
        self._battery_max_v = battery_max_v
        self._battery_min_v = 3.0
        self._adc = None
        self._watchdog = None
        self._wake_pins: list = []
        self._before_sleep_callbacks: list = []
        self._after_wake_callbacks: list = []

        self._detect_platform()

    def _detect_platform(self) -> None:
        """Detect if running on real hardware."""
        try:
            import machine
            self._simulation = False
        except ImportError:
            self._simulation = True

    def deep_sleep(self, duration_ms: int = 0) -> None:
        """
        Enter deep sleep mode.

        Args:
            duration_ms: Sleep duration in ms (0 = sleep until external wake)
        """
        self._fire_before_sleep()

        if self._simulation:
            print(f"[SIM] Deep sleep for {duration_ms}ms")
            if duration_ms > 0:
                time.sleep(duration_ms / 1000.0)
            return

        import machine

        if self._wake_pins:
            for pin_num, level in self._wake_pins:
                try:
                    pin = machine.Pin(pin_num)
                    esp = __import__("esp32")
                    if level:
                        esp.wake_on_ext0(pin, esp.WAKEUP_ANY_HIGH)
                    else:
                        esp.wake_on_ext0(pin, esp.WAKEUP_ALL_LOW)
                except Exception:
                    pass

        if duration_ms > 0:
            machine.deepsleep(duration_ms)
        else:
            machine.deepsleep()

    def light_sleep(self, duration_ms: int = 0) -> None:
        """
        Enter light sleep mode.

        Args:
            duration_ms: Sleep duration in ms (0 = sleep until external wake)
        """
        self._fire_before_sleep()

        if self._simulation:
            print(f"[SIM] Light sleep for {duration_ms}ms")
            if duration_ms > 0:
                time.sleep(duration_ms / 1000.0)
            self._fire_after_wake()
            return

        import machine
        if duration_ms > 0:
            machine.lightsleep(duration_ms)
        else:
            machine.lightsleep()

        self._fire_after_wake()

    def set_wake_pin(self, pin: int, level: int = 0) -> None:
        """
        Set a GPIO pin as wake source.

        Args:
            pin: GPIO pin number
            level: Wake level (0 = low, 1 = high)
        """
        self._wake_pins.append((pin, level))

    def clear_wake_pins(self) -> None:
        """Remove all wake pin configurations."""
        self._wake_pins.clear()

    def get_wake_reason(self) -> WakeReason:
        """
        Get the reason for the last wake-up.

        Returns:
            WakeReason enum value
        """
        if self._simulation:
            return WakeReason.POWER_ON

        try:
            import machine
            reason = machine.wake_reason()
            reason_map = {
                0: WakeReason.POWER_ON,
                2: WakeReason.GPIO,
                4: WakeReason.TIMER,
                5: WakeReason.TOUCHPAD,
                6: WakeReason.ULP,
            }
            return reason_map.get(reason, WakeReason.UNKNOWN)
        except Exception:
            return WakeReason.UNKNOWN

    def start_watchdog(self, timeout_ms: int = 8000) -> None:
        """
        Start the watchdog timer.

        Args:
            timeout_ms: Watchdog timeout in milliseconds
        """
        if self._simulation:
            print(f"[SIM] Watchdog started ({timeout_ms}ms)")
            return

        try:
            from machine import WDT
            self._watchdog = WDT(timeout=timeout_ms)
        except (ImportError, Exception) as e:
            print(f"Watchdog error: {e}")

    def feed_watchdog(self) -> None:
        """Feed/reset the watchdog timer."""
        if self._simulation:
            return

        if self._watchdog:
            self._watchdog.feed()

    def set_cpu_frequency(self, freq_mhz: int) -> None:
        """
        Set CPU frequency for power saving.

        Args:
            freq_mhz: Frequency in MHz (e.g., 80, 160, 240)
        """
        if self._simulation:
            print(f"[SIM] CPU frequency set to {freq_mhz}MHz")
            return

        try:
            import machine
            machine.freq(freq_mhz * 1_000_000)
        except Exception as e:
            print(f"CPU freq error: {e}")

    def get_cpu_frequency(self) -> int:
        """Get current CPU frequency in MHz."""
        if self._simulation:
            return 240

        try:
            import machine
            return machine.freq() // 1_000_000
        except Exception:
            return 0

    @property
    def battery_voltage(self) -> float:
        """
        Read battery voltage.

        Returns:
            Battery voltage in volts
        """
        if self._simulation:
            return 3.8

        if self._battery_pin is None:
            return 0.0

        try:
            from machine import ADC, Pin
            if self._adc is None:
                self._adc = ADC(Pin(self._battery_pin))
                self._adc.atten(ADC.ATTN_11DB)
                self._adc.width(ADC.WIDTH_12BIT)

            raw = self._adc.read()
            # Assume voltage divider (2:1 ratio typical)
            voltage = (raw / 4095.0) * 3.3 * 2
            return round(voltage, 2)
        except Exception:
            return 0.0

    @property
    def battery_percent(self) -> int:
        """
        Get battery percentage.

        Returns:
            Battery level (0-100)
        """
        voltage = self.battery_voltage
        if voltage <= self._battery_min_v:
            return 0
        if voltage >= self._battery_max_v:
            return 100

        percent = ((voltage - self._battery_min_v) /
                   (self._battery_max_v - self._battery_min_v)) * 100
        return max(0, min(100, int(percent)))

    @property
    def is_charging(self) -> bool:
        """Check if battery is charging (requires charging status pin)."""
        if self._simulation:
            return False
        return False  # Requires hardware-specific implementation

    def before_sleep(self, callback: Callable) -> None:
        """Register a callback to run before entering sleep."""
        self._before_sleep_callbacks.append(callback)

    def after_wake(self, callback: Callable) -> None:
        """Register a callback to run after waking up."""
        self._after_wake_callbacks.append(callback)

    def _fire_before_sleep(self) -> None:
        for cb in self._before_sleep_callbacks:
            try:
                cb()
            except Exception as e:
                print(f"Before-sleep callback error: {e}")

    def _fire_after_wake(self) -> None:
        for cb in self._after_wake_callbacks:
            try:
                cb()
            except Exception as e:
                print(f"After-wake callback error: {e}")

    @property
    def reset_cause(self) -> str:
        """Get the cause of the last reset."""
        if self._simulation:
            return "power_on"

        try:
            import machine
            cause = machine.reset_cause()
            causes = {
                0: "power_on",
                1: "hard_reset",
                2: "wdt_reset",
                3: "deepsleep_reset",
                4: "soft_reset",
            }
            return causes.get(cause, "unknown")
        except Exception:
            return "unknown"

    def reset(self) -> None:
        """Perform a soft reset."""
        if self._simulation:
            print("[SIM] Soft reset")
            return

        import machine
        machine.reset()

    def __repr__(self) -> str:
        mode = "SIM" if self._simulation else "HW"
        return f"<PowerManager [{mode}] battery={self.battery_percent}%>"
