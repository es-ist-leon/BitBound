"""Tests for bus implementations."""

import pytest
from bitbound.buses.base import Bus, BusFactory, BusType, BusConfig
from bitbound.buses.i2c import I2CBus
from bitbound.buses.spi import SPIBus
from bitbound.buses.gpio import GPIOBus, GPIOPin, PinMode
from bitbound.buses.uart import UARTBus
from bitbound.buses.onewire import OneWireBus


class TestI2CBus:
    def test_create(self):
        bus = I2CBus(scl=22, sda=21)
        assert bus is not None

    def test_init(self):
        bus = I2CBus()
        assert bus.init() is True
        assert bus.is_simulation is True

    def test_scan(self):
        bus = I2CBus()
        bus.init()
        addresses = bus.scan()
        assert isinstance(addresses, list)
        assert 0x76 in addresses  # Simulated BME280

    def test_read_register(self):
        bus = I2CBus()
        bus.init()
        data = bus.read_register(0x76, 0xD0, 1)
        assert len(data) == 1
        assert data[0] == 0x60  # BME280 chip ID

    def test_write_register(self):
        bus = I2CBus()
        bus.init()
        bus.write_register(0x76, 0xF2, bytes([0x01]))

    def test_read_byte(self):
        bus = I2CBus()
        bus.init()
        val = bus.read_byte(0x76, 0xD0)
        assert val == 0x60

    def test_read_nonexistent(self):
        bus = I2CBus()
        bus.init()
        with pytest.raises(OSError):
            bus.read_from(0x99, 1)

    def test_add_simulated_device(self):
        bus = I2CBus()
        bus.init()
        bus.add_simulated_device(0x48, "ADS1115", {0x00: [0x01, 0x02]})
        assert 0x48 in bus.scan()

    def test_repr(self):
        bus = I2CBus()
        assert "I2CBus" in repr(bus)

    def test_deinit(self):
        bus = I2CBus()
        bus.init()
        bus.deinit()


class TestSPIBus:
    def test_create(self):
        bus = SPIBus()
        assert bus is not None

    def test_init(self):
        bus = SPIBus()
        assert bus.init() is True
        assert bus.is_simulation is True

    def test_scan_empty(self):
        bus = SPIBus()
        bus.init()
        assert bus.scan() == []

    def test_transfer(self):
        bus = SPIBus()
        bus.init()
        result = bus.transfer(bytes([0x9F]))
        assert len(result) == 1

    def test_write(self):
        bus = SPIBus()
        bus.init()
        bus.write(bytes([0x01, 0x02]))

    def test_read(self):
        bus = SPIBus()
        bus.init()
        data = bus.read(4)
        assert len(data) == 4

    def test_repr(self):
        bus = SPIBus()
        assert "SPIBus" in repr(bus)


class TestGPIOBus:
    def test_create(self):
        bus = GPIOBus()
        assert bus is not None

    def test_init(self):
        bus = GPIOBus()
        assert bus.init() is True

    def test_pin_output(self):
        bus = GPIOBus()
        bus.init()
        pin = bus.output(13)
        assert isinstance(pin, GPIOPin)
        pin.on()
        assert pin.value == 1
        pin.off()
        assert pin.value == 0

    def test_pin_toggle(self):
        bus = GPIOBus()
        bus.init()
        pin = bus.output(5)
        pin.off()
        pin.toggle()
        assert pin.value == 1
        pin.toggle()
        assert pin.value == 0

    def test_pin_input(self):
        bus = GPIOBus()
        bus.init()
        pin = bus.input(14, pullup=True)
        val = pin.read()
        assert val == 0

    def test_pin_callback(self):
        bus = GPIOBus()
        bus.init()
        pin = bus.output(10)
        events = []
        pin.on_change(lambda: events.append(True))
        pin.on()
        assert len(events) == 1

    def test_scan(self):
        bus = GPIOBus()
        bus.init()
        bus.pin(1)
        bus.pin(2)
        pins = bus.scan()
        assert 1 in pins
        assert 2 in pins

    def test_deinit(self):
        bus = GPIOBus()
        bus.init()
        bus.pin(5)
        bus.deinit()
        assert len(bus._pins) == 0

    def test_repr(self):
        bus = GPIOBus()
        assert "GPIOBus" in repr(bus)


class TestUARTBus:
    def test_create(self):
        bus = UARTBus()
        assert bus is not None

    def test_init(self):
        bus = UARTBus()
        assert bus.init() is True
        assert bus.is_simulation is True

    def test_write(self):
        bus = UARTBus()
        bus.init()
        written = bus.write(b"Hello")
        assert written == 5

    def test_read(self):
        bus = UARTBus()
        bus.init()
        bus.sim_receive(b"test data")
        data = bus.read(4)
        assert data == b"test"
        remaining = bus.read()
        assert remaining == b" data"

    def test_any(self):
        bus = UARTBus()
        bus.init()
        assert bus.any() == 0
        bus.sim_receive(b"abc")
        assert bus.any() == 3

    def test_flush(self):
        bus = UARTBus()
        bus.init()
        bus.sim_receive(b"data")
        bus.flush()
        assert bus.any() == 0

    def test_scan_empty(self):
        bus = UARTBus()
        assert bus.scan() == []

    def test_repr(self):
        bus = UARTBus()
        assert "UARTBus" in repr(bus)


class TestOneWireBus:
    def test_create(self):
        bus = OneWireBus(pin=4)
        assert bus is not None

    def test_init(self):
        bus = OneWireBus()
        assert bus.init() is True
        assert bus.is_simulation is True

    def test_scan(self):
        bus = OneWireBus()
        bus.init()
        devices = bus.scan()
        assert len(devices) > 0  # Simulated DS18B20

    def test_read_ds18b20(self):
        bus = OneWireBus()
        bus.init()
        roms = bus.scan()
        temp = bus.read_ds18b20(roms[0])
        assert isinstance(temp, float)
        assert 15 < temp < 40

    def test_set_simulated_temp(self):
        bus = OneWireBus()
        bus.init()
        roms = bus.scan()
        bus.set_simulated_temp(roms[0], 42.0)
        temp = bus.read_ds18b20(roms[0])
        assert temp == 42.0

    def test_read_all_ds18b20(self):
        bus = OneWireBus()
        bus.init()
        temps = bus.read_all_ds18b20()
        assert len(temps) > 0

    def test_reset(self):
        bus = OneWireBus()
        bus.init()
        assert bus.reset() is True

    def test_repr(self):
        bus = OneWireBus()
        assert "OneWireBus" in repr(bus)


class TestBusFactory:
    def test_create_i2c(self):
        bus = BusFactory.create("I2C")
        assert isinstance(bus, I2CBus)

    def test_create_spi(self):
        bus = BusFactory.create("SPI")
        assert isinstance(bus, SPIBus)

    def test_create_gpio(self):
        bus = BusFactory.create("GPIO")
        assert isinstance(bus, GPIOBus)

    def test_create_uart(self):
        bus = BusFactory.create("UART")
        assert isinstance(bus, UARTBus)

    def test_create_onewire(self):
        bus = BusFactory.create("ONEWIRE")
        assert isinstance(bus, OneWireBus)

    def test_create_unknown(self):
        with pytest.raises(ValueError):
            BusFactory.create("UNKNOWN_BUS")

    def test_available_types(self):
        types = BusFactory.available_types()
        assert "I2C" in types
        assert "SPI" in types
        assert "GPIO" in types
