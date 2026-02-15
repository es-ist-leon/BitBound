"""
MQTT Sensor Network Example

Reads sensor data and publishes it to an MQTT broker.
Subscribes to commands for remote control.
"""

from bitbound import Hardware
from bitbound.network import WiFiManager, MQTTClient

# Connect to WiFi
wifi = WiFiManager()
wifi.connect("MyNetwork", "password123")

# Setup MQTT
mqtt = MQTTClient("sensor-node-1", broker="mqtt.example.com", port=1883)
mqtt.connect()

# Setup hardware
hw = Hardware()
sensor = hw.attach("I2C", type="BME280")
relay = hw.attach("GPIO", type="Relay", pin=5)

# Handle commands
def on_command(topic, message):
    if topic == "commands/relay":
        if message == "on":
            relay.on()
        elif message == "off":
            relay.off()

mqtt.subscribe("commands/#", callback=on_command)

# Publish sensor data periodically
def publish_readings(event):
    data = sensor.read_all()
    mqtt.publish("sensors/temperature", str(data["temperature"]))
    mqtt.publish("sensors/humidity", str(data["humidity"]))
    mqtt.publish("sensors/pressure", str(data["pressure"]))

sensor.on_interval(10000, publish_readings)  # Every 10 seconds

hw.run()
