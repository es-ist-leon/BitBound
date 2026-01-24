"""
Tests for BitBound hardware abstraction.
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from bitbound import Hardware


class TestHardware:
    """Tests for Hardware class."""
    
    def test_create_hardware(self):
        hw = Hardware()
        assert hw is not None
    
    def test_attach_sensor(self):
        hw = Hardware()
        sensor = hw.attach("I2C", type="BME280")
        assert sensor is not None
        assert sensor.connected
    
    def test_sensor_properties(self):
        hw = Hardware()
        sensor = hw.attach("I2C", type="BME280")
        
        # In simulation mode, these return default values
        assert isinstance(sensor.temperature, (int, float))
        assert isinstance(sensor.humidity, (int, float))
        assert isinstance(sensor.pressure, (int, float))
    
    def test_attach_led(self):
        hw = Hardware()
        led = hw.attach("GPIO", type="LED", pin=2)
        assert led is not None
        assert led.connected
    
    def test_led_control(self):
        hw = Hardware()
        led = hw.attach("GPIO", type="LED", pin=2)
        
        led.on()
        assert led.state is True
        
        led.off()
        assert led.state is False
        
        led.toggle()
        assert led.state is True
    
    def test_attach_relay(self):
        hw = Hardware()
        relay = hw.attach("GPIO", type="Relay", pin=5)
        assert relay is not None
        
        relay.on()
        assert relay.is_on is True
        
        relay.off()
        assert relay.is_on is False
    
    def test_attach_servo(self):
        hw = Hardware()
        servo = hw.attach("GPIO", type="Servo", pin=15)
        assert servo is not None
        
        servo.angle = 90
        assert servo.angle == 90
        
        servo.angle = 0
        assert servo.angle == 0
    
    def test_devices_list(self):
        hw = Hardware()
        hw.attach("I2C", type="BME280")
        hw.attach("GPIO", type="LED", pin=2)
        
        assert len(hw.devices) == 2
    
    def test_scan_i2c(self):
        hw = Hardware()
        addresses = hw.scan("I2C")
        # In simulation mode, returns simulated addresses
        assert isinstance(addresses, list)
    
    def test_context_manager(self):
        with Hardware() as hw:
            sensor = hw.attach("I2C", type="BME280")
            assert sensor.connected
        # After context, should be cleaned up
    
    def test_unknown_device_type(self):
        hw = Hardware()
        with pytest.raises(ValueError):
            hw.attach("I2C", type="UnknownDevice")


class TestSensorEvents:
    """Tests for sensor event handling."""
    
    def test_threshold_registration(self):
        hw = Hardware()
        sensor = hw.attach("I2C", type="BME280")
        
        callback_called = [False]
        
        def callback(event):
            callback_called[0] = True
        
        handler = sensor.on_threshold("temperature > 25°C", callback)
        assert handler is not None
    
    def test_change_registration(self):
        hw = Hardware()
        sensor = hw.attach("I2C", type="BME280")
        
        def callback(event):
            pass
        
        handler = sensor.on_change("temperature", callback)
        assert handler is not None
    
    def test_remove_handler(self):
        hw = Hardware()
        sensor = hw.attach("I2C", type="BME280")
        
        handler = sensor.on_threshold("temperature > 25°C", lambda e: None)
        sensor.remove_handler(handler)
        # Should not raise


class TestBME280:
    """Tests specifically for BME280 sensor."""
    
    def test_read_all(self):
        hw = Hardware()
        sensor = hw.attach("I2C", type="BME280")
        
        data = sensor.read_all()
        assert "temperature" in data
        assert "humidity" in data
        assert "pressure" in data
        assert "altitude" in data
    
    def test_sea_level_pressure(self):
        hw = Hardware()
        sensor = hw.attach("I2C", type="BME280")
        
        assert sensor.sea_level_pressure == 1013.25
        
        sensor.sea_level_pressure = 1000.0
        assert sensor.sea_level_pressure == 1000.0


class TestGPIO:
    """Tests for GPIO functionality."""
    
    def test_gpio_bus(self):
        hw = Hardware()
        led1 = hw.attach("GPIO", type="LED", pin=2)
        led2 = hw.attach("GPIO", type="LED", pin=3)
        
        led1.on()
        led2.off()
        
        assert led1.state is True
        assert led2.state is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
