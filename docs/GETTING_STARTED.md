# Getting Started with BitBound

This guide will help you get up and running with BitBound in minutes.

## Installation

```bash
pip install bitbound
```

## Your First Project

### 1. Basic Sensor Reading

```python
from bitbound import Hardware

# Create hardware manager
hw = Hardware()

# Attach a BME280 temperature sensor (I2C)
sensor = hw.attach("I2C", type="BME280")

# Read values - it's that simple!
print(f"Temperature: {sensor.temperature}°C")
print(f"Humidity: {sensor.humidity}%")
print(f"Pressure: {sensor.pressure} hPa")
```

### 2. LED Control

```python
from bitbound import Hardware

hw = Hardware()

# Attach LED on GPIO pin 2
led = hw.attach("GPIO", type="LED", pin=2)

# Control it
led.on()
led.off()
led.blink(times=5)
```

### 3. Event-Driven Programming

This is where BitBound shines. Instead of writing polling loops, you declare what should happen:

```python
from bitbound import Hardware

hw = Hardware()

# Attach devices
sensor = hw.attach("I2C", type="BME280")
fan = hw.attach("GPIO", type="Relay", pin=5)

# Declare behavior with natural expressions
sensor.on_threshold("temperature > 25°C", lambda e: fan.on())
sensor.on_threshold("temperature < 23°C", lambda e: fan.off())

# Run the event loop
hw.run()
```

That's it! BitBound handles all the polling, debouncing, and state management.

## Understanding Buses

BitBound supports multiple communication protocols:

| Bus | Use Case | Example Devices |
|-----|----------|-----------------|
| **I2C** | Multi-device, short distance | Sensors, displays, EEPROMs |
| **SPI** | High-speed, single device | SD cards, high-res displays |
| **GPIO** | Digital I/O | LEDs, buttons, relays |
| **UART** | Serial communication | GPS, Bluetooth modules |
| **OneWire** | Single-wire protocol | DS18B20 temperature sensors |

### Pin Configuration

```python
# I2C with custom pins (ESP32)
sensor = hw.attach("I2C", type="BME280", scl=22, sda=21)

# GPIO with specific pin
led = hw.attach("GPIO", type="LED", pin=2)

# Multiple devices on same bus share pins automatically
sensor1 = hw.attach("I2C", type="BME280", address=0x76)
sensor2 = hw.attach("I2C", type="BH1750", address=0x23)  # Same I2C bus
```

## Simulation Mode

BitBound automatically runs in simulation mode on desktop computers. This lets you develop and test your code without hardware:

```python
from bitbound import Hardware

hw = Hardware()
sensor = hw.attach("I2C", type="BME280")

# Works on your laptop!
print(sensor.temperature)  # Returns simulated value: 23.5°C
```

## Common Patterns

### Smart Thermostat

```python
from bitbound import Hardware

hw = Hardware()

sensor = hw.attach("I2C", type="BME280")
heater = hw.attach("GPIO", type="Relay", pin=5)
cooler = hw.attach("GPIO", type="Relay", pin=6)
lcd = hw.attach("I2C", type="LCD1602")

TARGET = 22

sensor.on_threshold(f"temperature > {TARGET + 2}°C", lambda e: (
    heater.off(),
    cooler.on()
))

sensor.on_threshold(f"temperature < {TARGET - 2}°C", lambda e: (
    cooler.off(),
    heater.on()
))

sensor.on_change("temperature", lambda e: (
    lcd.clear(),
    lcd.write(f"Temp: {e.new_value:.1f}C", y=0),
    lcd.write(f"Target: {TARGET}C", y=1)
))

hw.run()
```

### Motion-Activated Light

```python
from bitbound import Hardware

hw = Hardware()

pir = hw.attach("GPIO", type="PIR", pin=14)
light = hw.attach("GPIO", type="Relay", pin=5)

pir.on_change("motion", lambda e: (
    light.on() if e.new_value else light.off()
))

hw.run()
```

### Data Logger

```python
from bitbound import Hardware
import time

hw = Hardware()

sensor = hw.attach("I2C", type="BME280")

def log_data(event):
    data = sensor.read_all()
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    print(f"{timestamp}, {data['temperature']}, {data['humidity']}, {data['pressure']}")

# Log every 60 seconds
sensor.on_interval(60000, log_data)

hw.run()
```

## Next Steps

- 📖 Read the [API Reference](API.md)
- 🔧 Check out the [Examples](../examples/)
- 🤝 [Contribute](../CONTRIBUTING.md) to BitBound
