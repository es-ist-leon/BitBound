"""Tests for Power Management."""

import pytest
from bitbound.power import PowerManager, SleepMode, WakeReason


class TestPowerManager:
    def test_create_manager(self):
        pm = PowerManager()
        assert pm is not None

    def test_simulation_mode(self):
        pm = PowerManager()
        assert pm._simulation is True

    def test_battery_voltage(self):
        pm = PowerManager()
        voltage = pm.battery_voltage
        assert isinstance(voltage, float)
        assert voltage > 0

    def test_battery_percent(self):
        pm = PowerManager()
        percent = pm.battery_percent
        assert 0 <= percent <= 100

    def test_cpu_frequency(self):
        pm = PowerManager()
        freq = pm.get_cpu_frequency()
        assert freq > 0

    def test_set_cpu_frequency(self):
        pm = PowerManager()
        pm.set_cpu_frequency(80)  # Should not raise in simulation

    def test_wake_reason(self):
        pm = PowerManager()
        reason = pm.get_wake_reason()
        assert isinstance(reason, WakeReason)

    def test_reset_cause(self):
        pm = PowerManager()
        cause = pm.reset_cause
        assert isinstance(cause, str)

    def test_set_wake_pin(self):
        pm = PowerManager()
        pm.set_wake_pin(pin=4, level=0)
        assert len(pm._wake_pins) == 1
        pm.clear_wake_pins()
        assert len(pm._wake_pins) == 0

    def test_watchdog(self):
        pm = PowerManager()
        pm.start_watchdog(timeout_ms=5000)
        pm.feed_watchdog()  # Should not raise

    def test_deep_sleep_simulation(self):
        pm = PowerManager()
        pm.deep_sleep(duration_ms=10)  # Short sleep in sim

    def test_light_sleep_simulation(self):
        pm = PowerManager()
        pm.light_sleep(duration_ms=10)

    def test_before_sleep_callback(self):
        pm = PowerManager()
        called = []
        pm.before_sleep(lambda: called.append(True))
        pm.light_sleep(duration_ms=10)
        assert len(called) == 1

    def test_after_wake_callback(self):
        pm = PowerManager()
        called = []
        pm.after_wake(lambda: called.append(True))
        pm.light_sleep(duration_ms=10)
        assert len(called) == 1

    def test_is_charging(self):
        pm = PowerManager()
        assert pm.is_charging is False

    def test_repr(self):
        pm = PowerManager()
        assert "PowerManager" in repr(pm)
