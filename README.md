# BitBound – High-Level Embedded Python Library

> Hardware abstraction for MicroPython that makes embedded development as simple as working with modern web APIs.

[![PyPI version](https://badge.fury.io/py/bitbound.svg)](https://pypi.org/project/bitbound/)
[![PyPI downloads](https://img.shields.io/pypi/dm/bitbound.svg)](https://pypi.org/project/bitbound/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.7+](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/)
[![MicroPython](https://img.shields.io/badge/MicroPython-compatible-green.svg)](https://micropython.org/)

## 🎯 Vision

MicroPython is excellent, but complex hardware interactions often require deep knowledge of bus protocols and register configurations. **BitBound** abstracts hardware components (sensors, motors, displays) with a modern, declarative API—similar to how web frameworks abstract HTTP.

```python
from bitbound import Hardware

# Create hardware manager
hardware = Hardware()

# Attach devices with simple, declarative syntax
sensor = hardware.attach("I2C", type="BME280")
fan = hardware.attach("GPIO", type="Relay", pin=5)

# Use threshold-based events instead of polling loops
sensor.on_threshold("temperature > 25°C", lambda e: fan.on())
sensor.on_threshold("temperature < 23°C", lambda e: fan.off())

# Read values naturally
print(f"Temperature: {sensor.temperature}°C")
print(f"Humidity: {sensor.humidity}%")
print(f"Pressure: {sensor.pressure} hPa")

# Run the event loop
hardware.run()
```

## ✨ Features

- **Declarative Hardware Attachment**: No more manual register configuration
- **Natural Unit Expressions**: `"temperature > 25°C"`, `"pressure < 1000hPa"`
- **Event-Driven Programming**: Threshold callbacks, change detection, interval events
- **Simulation Mode**: Develop and test without physical hardware
- **Wide Device Support**: Sensors, actuators, displays
- **Cross-Platform**: Works on MicroPython, CircuitPython, and standard Python
- **Networking**: WiFi, MQTT, HTTP Client/Server, WebSocket
- **Data Logging**: CSV/JSON/JSONL logging, ring buffers, persistent storage
- **Configuration Management**: Board profiles, dot-notation config, project templates
- **Async Support**: Async device readings, event loops, gather_readings
- **Power Management**: Deep/light sleep, watchdog, battery monitoring
- **OTA Updates**: Version checking, firmware updates, rollback support
- **CLI Tool**: `bitbound` command for scanning, init, config, monitor, deploy

## 📦 Installation

### From PyPI (Recommended)

```bash
pip install bitbound
```

### From Source

```bash
git clone https://github.com/bitbound/bitbound.git
cd bitbound
pip install -e .
```

### MicroPython

Copy the `bitbound` folder to your device's filesystem:

```bash
# Using mpremote
mpremote cp -r bitbound :

# Or using ampy
ampy -p /dev/ttyUSB0 put bitbound

# Or using Thonny IDE - just copy the bitbound folder to your device
```

## 🚀 Quick Start

### Basic Sensor Reading

```python
from bitbound import Hardware

hw = Hardware()

# BME280 temperature/humidity/pressure sensor
sensor = hw.attach("I2C", type="BME280")

# Read all values
data = sensor.read_all()
print(f"Temperature: {data['temperature']}°C")
print(f"Humidity: {data['humidity']}%")
print(f"Pressure: {data['pressure']} hPa")
print(f"Altitude: {data['altitude']} m")
```

### LED Control

```python
from bitbound import Hardware

hw = Hardware()

# Simple LED
led = hw.attach("GPIO", type="LED", pin=2)
led.on()
led.off()
led.blink(times=5)

# RGB LED
rgb = hw.attach("GPIO", type="RGB", pins={"r": 12, "g": 13, "b": 14})
rgb.color = (255, 0, 0)      # Red
rgb.color = "#00FF00"        # Green (hex)
rgb.color = "blue"           # Named color
```

### Motor Control

```python
from bitbound import Hardware

hw = Hardware()

# DC Motor with H-Bridge
motor = hw.attach("GPIO", type="DCMotor",
                  enable_pin=5, in1_pin=6, in2_pin=7)
motor.forward(speed=75)   # 75% speed
motor.backward(speed=50)
motor.stop()

# Servo Motor
servo = hw.attach("GPIO", type="Servo", pin=15)
servo.angle = 90  # Move to 90 degrees
servo.sweep(0, 180)  # Sweep from 0 to 180
```

### Display Output

```python
from bitbound import Hardware

hw = Hardware()

# Character LCD
lcd = hw.attach("I2C", type="LCD1602")
lcd.write("Hello World!")
lcd.write("Line 2", y=1)

# OLED Display
oled = hw.attach("I2C", type="SSD1306")
oled.text("BitBound", 0, 0)
oled.line(0, 10, 127, 10)
oled.show()
```

### Event-Driven Programming

```python
from bitbound import Hardware

hw = Hardware()

sensor = hw.attach("I2C", type="BME280")
fan = hw.attach("GPIO", type="Relay", pin=5)
led = hw.attach("GPIO", type="LED", pin=2)
buzzer = hw.attach("GPIO", type="Buzzer", pin=15)

# Temperature thresholds
sensor.on_threshold("temperature > 30°C", lambda e: (
    fan.on(),
    buzzer.beep()
))

sensor.on_threshold("temperature < 25°C", lambda e: fan.off())

# Humidity alert
sensor.on_threshold("humidity > 80%", lambda e: led.blink(3))

# Value change detection
sensor.on_change("temperature", lambda e: 
    print(f"Temp changed: {e.old_value} -> {e.new_value}")
)

# Run event loop
hw.run()
```

### Complex Expressions

```python
# Compound conditions
sensor.on_threshold(
    "temperature > 25°C AND humidity < 40%",
    lambda e: humidifier.on()
)

# Range check
sensor.on_threshold(
    "temperature BETWEEN 20°C AND 25°C",
    lambda e: print("Optimal temperature!")
)

# Pressure monitoring
sensor.on_threshold(
    "pressure < 1000hPa OR pressure > 1030hPa",
    lambda e: alert()
)
```

## 📖 Supported Devices

### Sensors

| Device | Bus | Properties |
|--------|-----|------------|
| BME280/BMP280 | I2C | temperature, humidity, pressure, altitude |
| DHT11/DHT22 | GPIO | temperature, humidity |
| DS18B20 | OneWire | temperature |
| BH1750 | I2C | lux |
| MPU6050 | I2C | acceleration, gyroscope, temperature |
| PIR | GPIO | motion |
| Analog | ADC | value, voltage, percent |

### Actuators

| Device | Bus | Methods |
|--------|-----|---------|
| Relay | GPIO | on(), off(), toggle() |
| LED | GPIO | on(), off(), blink() |
| RGB LED | GPIO | color property |
| NeoPixel | GPIO | fill(), pixel[], rainbow() |
| DC Motor | GPIO | forward(), backward(), stop() |
| Servo | GPIO | angle property, sweep() |
| Stepper | GPIO | step(), rotate() |
| Buzzer | GPIO | beep(), tone(), melody() |

### Displays

| Device | Bus | Methods |
|--------|-----|---------|
| LCD1602/LCD2004 | I2C | write(), clear(), backlight |
| SSD1306 OLED | I2C | text(), line(), rect(), pixel() |
| 7-Segment | GPIO | digit(), number() |

## 🔧 Configuration

### Custom Pin Configuration

```python
hw = Hardware()

# I2C with custom pins
sensor = hw.attach("I2C", type="BME280", scl=22, sda=21, freq=400000)

# SPI with all pins specified
device = hw.attach("SPI", type="...", sck=18, mosi=23, miso=19, cs=5)

# UART with custom settings
gps = hw.attach("UART", type="...", tx=17, rx=16, baudrate=9600)
```

### Device Discovery

```python
hw = Hardware()

# Scan I2C bus
addresses = hw.scan("I2C")
print(f"Found devices at: {[hex(a) for a in addresses]}")

# Auto-discover devices
discovered = hw.discover()
for category, devices in discovered.items():
    print(f"{category}: {devices}")
```

## 🧪 Simulation Mode

BitBound automatically runs in simulation mode when no hardware is detected. This allows development and testing on any computer:

```python
from bitbound import Hardware

# Simulation mode is automatic on desktop
hw = Hardware()

# All devices work in simulation
sensor = hw.attach("I2C", type="BME280")
print(sensor.temperature)  # Returns simulated value: 23.5

led = hw.attach("GPIO", type="LED", pin=2)
led.on()  # Works without hardware
```

## 🔌 Unit System

BitBound understands physical units:

```python
from bitbound.units import parse_value, convert

# Parse values with units
value, unit = parse_value("25°C")
print(unit.to_si())  # 298.15 (Kelvin)

# Convert between units
celsius = convert(77, "°F", "°C")  # 25.0
```

Supported units:
- Temperature: °C, °F, K
- Pressure: Pa, hPa, kPa, bar, mbar, psi, atm
- Humidity: %, RH, %RH
- Length: mm, cm, m, km, in, ft
- Time: ms, s, min, h
- Electrical: V, mV, A, mA, µA, W, Ω, kΩ, MΩ
- Light: lux, lx
- Frequency: Hz, kHz, MHz

## 🌐 Networking

### WiFi Management

```python
from bitbound.network import WiFiManager

wifi = WiFiManager()
wifi.connect("MyNetwork", "password123")

# Scan for networks
networks = wifi.scan()
for net in networks:
    print(f"{net['ssid']} ({net['rssi']} dBm)")

# AP mode
wifi.start_ap("BitBound-AP", "ap-password")
```

### MQTT

```python
from bitbound.network import MQTTClient

mqtt = MQTTClient("my-device", broker="mqtt.example.com")
mqtt.connect()

# Publish sensor data
mqtt.publish("sensors/temp", '{"value": 23.5}')

# Subscribe to commands
mqtt.subscribe("commands/#", callback=lambda topic, msg: print(f"{topic}: {msg}"))
```

### HTTP Client & Server

```python
from bitbound.network import HTTPClient, HTTPServer

# Client
http = HTTPClient()
response = http.get("http://api.example.com/data")
print(response.json())

http.post("http://api.example.com/data", json_data={"temp": 23.5})

# Server
server = HTTPServer(port=80)

@server.route("/api/temperature")
def get_temp(request):
    return {"temperature": 23.5}

server.start()
```

### WebSocket

```python
from bitbound.network import WebSocketClient

ws = WebSocketClient("ws://server.local/ws")
ws.on_message(lambda msg: print(f"Received: {msg}"))
ws.connect()
ws.send({"temperature": 23.5})
```

## 📊 Data Logging

```python
from bitbound.logging import DataLogger, RingBuffer, Storage

# CSV/JSON data logging with rotation
logger = DataLogger("sensor_data", format="csv", max_entries=1000)
logger.log({"temperature": 23.5, "humidity": 65.0})

# Ring buffer for memory-constrained devices
buffer = RingBuffer(100)
buffer.append(23.5)
print(f"Average: {buffer.average()}, Min: {buffer.min()}, Max: {buffer.max()}")

# Persistent key-value storage
storage = Storage()
storage.set("wifi_ssid", "MyNetwork")
print(storage.get("wifi_ssid"))
```

## ⚙️ Configuration Management

```python
from bitbound import Config

# Load config with board profiles
config = Config(board="esp32")

# Dot-notation access
config.set("mqtt.broker", "mqtt.example.com")
config.set("mqtt.port", 1883)
print(config.get("mqtt.broker"))

# Board-specific pin mappings included
print(config.get("pins.i2c_sda"))  # Board-specific default
```

Available board profiles: `esp32`, `esp32s3`, `esp32c3`, `esp8266`, `rpi_pico`, `rpi_pico_w`

## ⚡ Async Support

```python
from bitbound.async_support import AsyncDevice, gather_readings

# Async device readings
async_sensor = AsyncDevice(sensor)
temp = await async_sensor.read("temperature")

# Gather multiple readings concurrently
results = await gather_readings([sensor1, sensor2, sensor3], "temperature")
```

## 🔋 Power Management

```python
from bitbound import PowerManager

pm = PowerManager()

# Deep sleep with timed wake
pm.deep_sleep(duration_ms=60000)

# Light sleep
pm.light_sleep(duration_ms=5000)

# Battery monitoring
level = pm.battery_level()
print(f"Battery: {level}%")

# Watchdog timer
pm.watchdog_enable(timeout_ms=8000)
pm.watchdog_feed()
```

## 🔄 OTA Updates

```python
from bitbound.ota import OTAManager

ota = OTAManager(
    update_url="https://api.example.com/firmware",
    current_version="1.0.0"
)

# Check for updates
if ota.check_update():
    print(f"New version: {ota.available_version}")
    ota.update()

# Rollback support
ota.rollback()
```

## 🖥️ CLI Tool

```bash
# Install with CLI support
pip install bitbound

# Initialize a new project
bitbound init my-project --board esp32

# List supported boards
bitbound boards

# Scan for connected devices
bitbound scan

# Monitor device readings
bitbound monitor --port COM3

# Deploy to device
bitbound deploy --port COM3
```

## 📁 Project Structure

```
bitbound/
├── __init__.py          # Main exports
├── hardware.py          # Hardware manager
├── device.py            # Device base classes
├── event.py             # Event system
├── expression.py        # Expression parser
├── units.py             # Unit handling
├── config.py            # Configuration management
├── power.py             # Power management
├── ota.py               # OTA update manager
├── async_support.py     # Async device support
├── cli.py               # CLI tool
├── buses/
│   ├── base.py          # Bus abstraction
│   ├── i2c.py           # I2C implementation
│   ├── spi.py           # SPI implementation
│   ├── gpio.py          # GPIO implementation
│   ├── uart.py          # UART implementation
│   └── onewire.py       # OneWire implementation
├── devices/
│   ├── sensors/         # Sensor implementations
│   ├── actuators/       # Actuator implementations
│   └── displays/        # Display implementations
├── network/
│   ├── wifi.py          # WiFi management
│   ├── mqtt.py          # MQTT client
│   ├── http.py          # HTTP client/server
│   └── websocket.py     # WebSocket client
└── logging/
    ├── datalogger.py    # Data logging (CSV/JSON/JSONL)
    ├── storage.py       # Persistent storage
    └── ringbuffer.py    # Memory-efficient ring buffer
```

## 🛠️ Supported Hardware

### Microcontrollers
- **ESP32** / ESP32-S2 / ESP32-S3 / ESP32-C3
- **Raspberry Pi Pico** (RP2040)
- **ESP8266** (limited memory)
- **STM32** with MicroPython
- Any board running **MicroPython** or **CircuitPython**

### Development/Simulation
- **Windows**, **macOS**, **Linux** with Python 3.7+
- Full simulation mode for development without hardware

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

### Development Setup

```bash
git clone https://github.com/bitbound/bitbound.git
cd bitbound
pip install -e ".[dev]"
pytest tests/
```

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

## 🔗 Links

- **PyPI:** https://pypi.org/project/bitbound/
- **Documentation:** https://bitbound.readthedocs.io/
- **GitHub:** https://github.com/bitbound/bitbound
- **Issues:** https://github.com/bitbound/bitbound/issues

## 🙏 Acknowledgments

- Inspired by modern web frameworks and their declarative approaches
- Built on top of the excellent MicroPython/CircuitPython ecosystems
- Thanks to all the open-source hardware driver contributors

---

**Made with ❤️ for the Maker community**
