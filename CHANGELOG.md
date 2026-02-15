# Changelog

All notable changes to BitBound will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-02-15

### Added
- **Networking & Connectivity**
  - WiFiManager: connect, scan, AP mode, status callbacks, auto-reconnect
  - MQTTClient: publish/subscribe, topic wildcards, QoS, simulation mode
  - HTTPClient: multi-backend (urequests/requests/urllib/simulation), GET/POST/PUT/DELETE
  - HTTPServer: route decorator, threaded socket server, JSON/HTML responses
  - WebSocketClient: real-time communication, event callbacks, simulation mode

- **Data Logging & Persistence**
  - DataLogger: CSV/JSON/JSONL formats, log rotation, device-aware logging
  - Storage/FileStorage: persistent key-value store, text/binary file operations
  - RingBuffer: memory-efficient circular buffer with statistics (avg, min, max)

- **Configuration Management**
  - Config manager with dot-notation access
  - Board profiles: esp32, esp32s3, esp32c3, esp8266, rpi_pico, rpi_pico_w
  - Default pin mappings per board, save/load to JSON

- **Async Support**
  - AsyncEventLoop for cooperative multitasking
  - AsyncDevice wrapper for async sensor readings
  - gather_readings() for concurrent multi-device reads

- **Power Management**
  - Deep sleep / light sleep with timed wake
  - Watchdog timer (enable, feed, disable)
  - Battery level monitoring
  - CPU frequency scaling
  - Simulation mode for desktop development

- **OTA Updates**
  - OTAManager: check for updates, download, verify, install
  - Automatic backup and rollback support
  - Version comparison utilities
  - Status callbacks for progress tracking

- **CLI Tool** (`bitbound` command)
  - `bitbound init <project> --board <board>`: Initialize project with template
  - `bitbound scan`: Scan for connected devices
  - `bitbound config`: View/set configuration
  - `bitbound monitor`: Monitor device readings
  - `bitbound deploy`: Deploy code to device
  - `bitbound boards`: List supported boards
  - `bitbound info`: Show environment information

- **Comprehensive Test Suite**
  - 291 tests covering all modules
  - Tests for networking, logging, config, async, power, OTA, CLI
  - Tests for all bus implementations and device types

### Changed
- Version bumped from 0.1.0 to 1.0.0
- Updated pyproject.toml with CLI entry point, optional dependency groups
- Added pytest-asyncio support for async tests

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
