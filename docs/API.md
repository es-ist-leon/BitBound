# BitBound API Reference

## Quick Start

```python
from bitbound import Hardware

hw = Hardware()
sensor = hw.attach("I2C", type="BME280")
print(f"Temperature: {sensor.temperature}°C")
```

## Hardware Class

The main entry point for BitBound.

### Constructor

```python
Hardware(auto_scan=True, simulation=None)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `auto_scan` | bool | True | Auto-scan for devices on attach |
| `simulation` | bool | None | Force simulation mode (None = auto-detect) |

### Methods

#### attach()

```python
hw.attach(bus_type, type, **kwargs) -> Device
```

Attach a hardware device.

| Parameter | Type | Description |
|-----------|------|-------------|
| `bus_type` | str | "I2C", "SPI", "GPIO", "UART", "OneWire" |
| `type` | str | Device type ("BME280", "LED", etc.) |
| `**kwargs` | | Device-specific options |

**Examples:**
```python
# I2C sensor
sensor = hw.attach("I2C", type="BME280", address=0x76)

# GPIO LED
led = hw.attach("GPIO", type="LED", pin=2)

# Servo motor
servo = hw.attach("GPIO", type="Servo", pin=15, min_angle=0, max_angle=180)
```

#### scan()

```python
hw.scan(bus_type="I2C", **kwargs) -> List[int]
```

Scan for devices on a bus.

```python
addresses = hw.scan("I2C")
print([hex(a) for a in addresses])  # ['0x76', '0x3c']
```

#### discover()

```python
hw.discover() -> Dict[str, List[Device]]
```

Auto-discover and attach known devices.

```python
discovered = hw.discover()
for category, devices in discovered.items():
    print(f"{category}: {len(devices)} devices")
```

#### start() / stop() / run()

```python
hw.start()      # Start event loop in background
hw.stop()       # Stop event loop
hw.run()        # Run event loop (blocking)
```

---

## Device Classes

### Sensors

All sensors have these common methods:

```python
sensor.connect() -> bool      # Connect to device
sensor.disconnect() -> None   # Disconnect
sensor.read_all() -> dict     # Read all properties
sensor.on_threshold(expr, callback, debounce_ms=0)  # Threshold event
sensor.on_change(prop, callback, debounce_ms=0)     # Change event
```

#### BME280Sensor

Temperature, humidity, pressure sensor.

```python
sensor = hw.attach("I2C", type="BME280")

sensor.temperature  # float, °C
sensor.humidity     # float, %
sensor.pressure     # float, hPa
sensor.altitude     # float, meters

sensor.sea_level_pressure = 1013.25  # For altitude calculation
```

#### DHT11 / DHT22

```python
dht = hw.attach("GPIO", type="DHT22", pin=4)

dht.temperature  # float, °C
dht.humidity     # float, %
```

#### DS18B20Sensor

OneWire temperature sensor.

```python
temp = hw.attach("OneWire", type="DS18B20", pin=4)
temp.temperature  # float, °C
```

#### BH1750Sensor

Light sensor.

```python
light = hw.attach("I2C", type="BH1750")
light.lux  # float, lux
```

#### MPU6050Sensor

6-axis accelerometer/gyroscope.

```python
imu = hw.attach("I2C", type="MPU6050")

imu.acceleration  # (x, y, z) in g
imu.gyroscope     # (x, y, z) in °/s
imu.temperature   # float, °C
```

---

### Actuators

#### Relay

```python
relay = hw.attach("GPIO", type="Relay", pin=5, active_low=True)

relay.on()
relay.off()
relay.toggle()
relay.state      # bool
relay.is_on      # bool

# Context manager
with relay:
    # Relay is ON
    pass
# Relay is OFF
```

#### LED

```python
led = hw.attach("GPIO", type="LED", pin=2)

led.on()
led.off()
led.toggle()
led.blink(times=3, on_time=0.5, off_time=0.5)
```

#### RGBLed

```python
rgb = hw.attach("GPIO", type="RGB", pins={"r": 12, "g": 13, "b": 14})

rgb.color = (255, 0, 0)      # Tuple
rgb.color = "#00FF00"        # Hex
rgb.color = "blue"           # Name
rgb.fade((255, 0, 0), (0, 0, 255), duration=2.0)
```

#### NeoPixel

```python
strip = hw.attach("GPIO", type="NeoPixel", pin=16, num_leds=30)

strip.fill((255, 0, 0))      # All red
strip[0] = (0, 255, 0)       # First LED green
strip.brightness = 0.5       # 50% brightness
strip.rainbow(delay_ms=20)   # Rainbow effect
strip.clear()
```

#### DCMotor

```python
motor = hw.attach("GPIO", type="DCMotor",
                  enable_pin=5, in1_pin=6, in2_pin=7)

motor.forward(speed=75)      # 75% speed
motor.backward(speed=50)
motor.stop()
motor.brake()
motor.set_speed(100)
motor.speed      # int, 0-100
motor.direction  # int, -1/0/1
```

#### ServoMotor

```python
servo = hw.attach("GPIO", type="Servo", pin=15,
                  min_angle=0, max_angle=180)

servo.angle = 90             # Move to 90°
servo.sweep(0, 180, step=1, delay_ms=15)
```

#### StepperMotor

```python
stepper = hw.attach("GPIO", type="Stepper",
                    pins=[12, 13, 14, 15], steps_per_rev=2048)

stepper.step(100)            # 100 steps forward
stepper.step(-50)            # 50 steps backward
stepper.rotate(90)           # Rotate 90°
stepper.release()            # Release holding torque
stepper.position             # int, current step count
```

#### Buzzer

```python
buzzer = hw.attach("GPIO", type="Buzzer", pin=15)

buzzer.beep(duration=0.1, freq=1000)
buzzer.tone(440, duration=0.5)       # A4 note
buzzer.note("C4", duration=0.25)
buzzer.play_melody([("C4", 0.5), ("E4", 0.5), ("G4", 0.5)])
buzzer.play_preset("startup")        # Built-in melody
```

---

### Displays

#### LCD1602 / LCD2004

```python
lcd = hw.attach("I2C", type="LCD1602")  # or LCD2004

lcd.write("Hello World!", x=0, y=0)
lcd.write("Line 2", y=1)
lcd.clear()
lcd.home()
lcd.set_cursor(x=5, y=0)

lcd.backlight = True         # On/off
lcd.cursor = True            # Show cursor
lcd.blink = True             # Blinking cursor
```

#### SSD1306Display

OLED display (128x64 or 128x32).

```python
oled = hw.attach("I2C", type="SSD1306", width=128, height=64)

oled.text("Hello", x=0, y=0)
oled.pixel(x=10, y=10, color=1)
oled.line(x0=0, y0=0, x1=127, y1=63)
oled.rect(x=10, y=10, w=50, h=30)
oled.fill_rect(x=10, y=10, w=50, h=30)
oled.fill(color=0)           # Clear
oled.show()                  # Update display

oled.invert(True)
oled.contrast(200)
```

---

## Event System

### Threshold Events

```python
sensor.on_threshold("temperature > 25°C", callback, debounce_ms=5000)
sensor.on_threshold("humidity < 40%", callback)
sensor.on_threshold("pressure BETWEEN 1000hPa AND 1020hPa", callback)
sensor.on_threshold("temperature > 25°C AND humidity > 80%", callback)
```

### Change Events

```python
sensor.on_change("temperature", lambda e: print(f"Changed: {e.new_value}"))
```

### Event Object

```python
def callback(event):
    event.event_type   # EventType enum
    event.source       # Device that triggered
    event.property_name
    event.old_value
    event.new_value
    event.timestamp
```

---

## Units

```python
from bitbound.units import parse_value, convert

value, unit = parse_value("25°C")
print(unit.to_si())  # 298.15 (Kelvin)

celsius = convert(77, "°F", "°C")  # 25.0
```

### Supported Units

| Category | Units |
|----------|-------|
| Temperature | °C, °F, K |
| Pressure | Pa, hPa, kPa, bar, mbar, psi, atm |
| Humidity | %, RH, %RH |
| Length | mm, cm, m, km, in, ft |
| Time | ms, s, min, h |
| Voltage | mV, V |
| Current | µA, mA, A |
| Power | mW, W, kW |
| Resistance | Ω, kΩ, MΩ |
| Light | lux, lx |
| Frequency | Hz, kHz, MHz |
