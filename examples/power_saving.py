"""
Power Saving Example

Demonstrates deep sleep, battery monitoring,
and watchdog timer for reliable IoT deployments.
"""

from bitbound import Hardware, PowerManager
from bitbound.network import WiFiManager, MQTTClient

pm = PowerManager()
hw = Hardware()
sensor = hw.attach("I2C", type="BME280")

# Enable watchdog (reset if hung for >30s)
pm.watchdog_enable(timeout_ms=30000)

# Check battery
level = pm.battery_level()
print(f"Battery: {level}%")

if level < 10:
    print("Low battery! Entering deep sleep...")
    pm.deep_sleep(duration_ms=3600000)  # Sleep 1 hour

# Quick wake-up: read sensor, send data, go back to sleep
pm.watchdog_feed()

wifi = WiFiManager()
wifi.connect("MyNetwork", "password123")

mqtt = MQTTClient("sensor", broker="mqtt.example.com")
mqtt.connect()

data = sensor.read_all()
mqtt.publish("sensors/data", str(data))

pm.watchdog_feed()

mqtt.disconnect()
wifi.disconnect()

# Sleep for 5 minutes, then wake and repeat
pm.deep_sleep(duration_ms=300000)
