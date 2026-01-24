# Changelog

All notable changes to BitBound will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-01-24

### Added
- Initial release of BitBound
- **Core Framework**
  - `Hardware` class for managing devices and buses
  - `Device` base class with `Sensor`, `Actuator`, `Display` subclasses
  - Event-driven programming with `EventLoop`
  - Expression parser for declarative thresholds (`"temperature > 25°C"`)
  - Unit system with automatic conversion (°C, °F, K, hPa, %, etc.)

- **Bus Protocols**
  - I2C bus with device scanning and simulation
  - SPI bus support
  - GPIO with PWM support
  - UART/Serial communication
  - OneWire protocol (for DS18B20, etc.)

- **Sensors**
  - BME280/BMP280 (temperature, humidity, pressure, altitude)
  - DHT11/DHT22 (temperature, humidity)
  - DS18B20 (OneWire temperature)
  - BH1750 (light/lux sensor)
  - MPU6050 (accelerometer/gyroscope)
  - PIR motion sensor
  - Generic analog sensor (ADC)

- **Actuators**
  - Relay (single and multi-channel boards)
  - DC Motor with H-Bridge (forward, backward, speed control)
  - Servo Motor (angle control, sweep)
  - Stepper Motor (step, rotate)
  - LED (on, off, blink)
  - RGB LED (color control, fade)
  - NeoPixel/WS2812 (addressable LEDs, rainbow effects)
  - Buzzer (tones, melodies)

- **Displays**
  - LCD1602/LCD2004 (I2C character displays)
  - SSD1306 OLED (128x64, 128x32)
  - 7-Segment display

- **Features**
  - Simulation mode for development without hardware
  - Auto-discovery of I2C devices
  - MicroPython and CPython compatible
  - Context manager support
  - Debouncing for event handlers

- **Examples**
  - Smart Thermostat
  - Weather Station
  - LED Effects
  - Motion Alarm

### Notes
- First public release on PyPI
- Tested on ESP32, Raspberry Pi Pico, and desktop Python
