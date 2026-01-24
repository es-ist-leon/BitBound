# BitBound – High-Level Embedded Python Library

> Hardware abstraction for MicroPython that makes embedded development as simple as working with modern web APIs.

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

## 📦 Installation

### Standard Python (for development/simulation)

```bash
pip install bitbound
```

### MicroPython

Copy the `bitbound` folder to your device's filesystem:

```bash
mpremote cp -r bitbound :
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

## 📁 Project Structure

```
bitbound/
├── __init__.py          # Main exports
├── hardware.py          # Hardware manager
├── device.py            # Device base classes
├── event.py             # Event system
├── expression.py        # Expression parser
├── units.py             # Unit handling
├── buses/
│   ├── base.py          # Bus abstraction
│   ├── i2c.py           # I2C implementation
│   ├── spi.py           # SPI implementation
│   ├── gpio.py          # GPIO implementation
│   ├── uart.py          # UART implementation
│   └── onewire.py       # OneWire implementation
└── devices/
    ├── sensors/         # Sensor implementations
    ├── actuators/       # Actuator implementations
    └── displays/        # Display implementations
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

## 🙏 Acknowledgments

- Inspired by modern web frameworks and their declarative approaches
- Built on top of the excellent MicroPython/CircuitPython ecosystems
- Thanks to all the open-source hardware driver contributors
