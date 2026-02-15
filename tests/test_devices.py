"""Tests for device implementations."""

import pytest
from bitbound import Hardware


class TestBME280:
    def test_attach(self):
        hw = Hardware()
        sensor = hw.attach("I2C", type="BME280")
        assert sensor is not None
        assert sensor.connected

    def test_read_temperature(self):
        hw = Hardware()
        sensor = hw.attach("I2C", type="BME280")
        temp = sensor.temperature
        assert isinstance(temp, (int, float))

    def test_read_humidity(self):
        hw = Hardware()
        sensor = hw.attach("I2C", type="BME280")
        hum = sensor.humidity
        assert isinstance(hum, (int, float))

    def test_read_pressure(self):
        hw = Hardware()
        sensor = hw.attach("I2C", type="BME280")
        pressure = sensor.pressure
        assert isinstance(pressure, (int, float))

    def test_read_altitude(self):
        hw = Hardware()
        sensor = hw.attach("I2C", type="BME280")
        alt = sensor.altitude
        assert isinstance(alt, (int, float))

    def test_read_all(self):
        hw = Hardware()
        sensor = hw.attach("I2C", type="BME280")
        data = sensor.read_all()
        assert "temperature" in data
        assert "humidity" in data
        assert "pressure" in data


class TestLED:
    def test_attach(self):
        hw = Hardware()
        led = hw.attach("GPIO", type="LED", pin=2)
        assert led is not None

    def test_on_off(self):
        hw = Hardware()
        led = hw.attach("GPIO", type="LED", pin=2)
        led.on()
        led.off()

    def test_toggle(self):
        hw = Hardware()
        led = hw.attach("GPIO", type="LED", pin=2)
        led.toggle()

    def test_blink(self):
        hw = Hardware()
        led = hw.attach("GPIO", type="LED", pin=2)
        led.blink(times=2, on_time=0.01, off_time=0.01)


class TestRelay:
    def test_attach(self):
        hw = Hardware()
        relay = hw.attach("GPIO", type="Relay", pin=5)
        assert relay is not None

    def test_on_off(self):
        hw = Hardware()
        relay = hw.attach("GPIO", type="Relay", pin=5)
        relay.on()
        relay.off()

    def test_toggle(self):
        hw = Hardware()
        relay = hw.attach("GPIO", type="Relay", pin=5)
        relay.toggle()


class TestServo:
    def test_attach(self):
        hw = Hardware()
        servo = hw.attach("GPIO", type="Servo", pin=15)
        assert servo is not None

    def test_angle(self):
        hw = Hardware()
        servo = hw.attach("GPIO", type="Servo", pin=15)
        servo.angle = 90


class TestDCMotor:
    def test_attach(self):
        hw = Hardware()
        motor = hw.attach("GPIO", type="DCMotor", enable_pin=5, in1_pin=6, in2_pin=7)
        assert motor is not None

    def test_forward_backward_stop(self):
        hw = Hardware()
        motor = hw.attach("GPIO", type="DCMotor", enable_pin=5, in1_pin=6, in2_pin=7)
        motor.forward(speed=75)
        motor.backward(speed=50)
        motor.stop()


class TestBuzzer:
    def test_attach(self):
        hw = Hardware()
        buzzer = hw.attach("GPIO", type="Buzzer", pin=15)
        assert buzzer is not None

    def test_beep(self):
        hw = Hardware()
        buzzer = hw.attach("GPIO", type="Buzzer", pin=15)
        buzzer.beep(duration=0.01)


class TestDisplay:
    def test_attach_lcd(self):
        hw = Hardware()
        lcd = hw.attach("I2C", type="LCD1602")
        assert lcd is not None

    def test_lcd_write(self):
        hw = Hardware()
        lcd = hw.attach("I2C", type="LCD1602")
        lcd.write("Hello")
        lcd.clear()

    def test_attach_oled(self):
        hw = Hardware()
        oled = hw.attach("I2C", type="SSD1306")
        assert oled is not None


class TestDeviceDiscovery:
    def test_discover(self):
        hw = Hardware()
        discovered = hw.discover()
        assert isinstance(discovered, dict)
        assert "sensors" in discovered
        assert "actuators" in discovered
        assert "displays" in discovered

    def test_device_list(self):
        hw = Hardware()
        hw.attach("I2C", type="BME280")
        hw.attach("GPIO", type="LED", pin=2)
        assert len(hw.devices) == 2

    def test_context_manager(self):
        with Hardware() as hw:
            hw.attach("I2C", type="BME280")
            assert len(hw.devices) == 1
