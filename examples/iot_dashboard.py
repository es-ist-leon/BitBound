"""
IoT Dashboard Example

Runs a web server on the device that serves sensor data
as a REST API and a simple HTML dashboard.
"""

from bitbound import Hardware
from bitbound.network import WiFiManager, HTTPServer

# Connect to WiFi
wifi = WiFiManager()
wifi.connect("MyNetwork", "password123")

# Setup hardware
hw = Hardware()
sensor = hw.attach("I2C", type="BME280")
led = hw.attach("GPIO", type="LED", pin=2)

# Create HTTP server
server = HTTPServer(port=80)


@server.route("/")
def index(request):
    return """
    <html>
    <head><title>BitBound Dashboard</title></head>
    <body>
        <h1>Sensor Dashboard</h1>
        <div id="data"></div>
        <script>
            setInterval(() => {
                fetch('/api/sensors')
                    .then(r => r.json())
                    .then(d => {
                        document.getElementById('data').innerHTML = 
                            `<p>Temperature: ${d.temperature}°C</p>
                             <p>Humidity: ${d.humidity}%</p>
                             <p>Pressure: ${d.pressure} hPa</p>`;
                    });
            }, 2000);
        </script>
    </body>
    </html>
    """


@server.route("/api/sensors")
def api_sensors(request):
    data = sensor.read_all()
    return {
        "temperature": data["temperature"],
        "humidity": data["humidity"],
        "pressure": data["pressure"],
    }


@server.route("/api/led", methods=["POST"])
def api_led(request):
    action = request.get("action", "toggle")
    if action == "on":
        led.on()
    elif action == "off":
        led.off()
    else:
        led.toggle()
    return {"status": "ok", "led": led.state}


server.start()
print(f"Dashboard running at http://{wifi.ip}/")
