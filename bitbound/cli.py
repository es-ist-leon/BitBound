"""
CLI Tool for BitBound.

Provides command-line interface for device scanning, configuration,
deployment, and monitoring.
"""

import argparse
import json
import sys
import time
from typing import List, Optional


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser."""
    parser = argparse.ArgumentParser(
        prog="bitbound",
        description="BitBound - High-Level Embedded Python Library CLI",
    )
    parser.add_argument(
        "--version", action="version", version="%(prog)s 1.0.0"
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # --- scan ---
    scan_parser = subparsers.add_parser("scan", help="Scan for connected devices")
    scan_parser.add_argument(
        "--bus", choices=["i2c", "spi", "gpio", "uart", "onewire", "all"],
        default="all", help="Bus type to scan"
    )
    scan_parser.add_argument("--scl", type=int, default=22, help="I2C SCL pin")
    scan_parser.add_argument("--sda", type=int, default=21, help="I2C SDA pin")
    scan_parser.add_argument("--json", action="store_true", help="Output as JSON")

    # --- init ---
    init_parser = subparsers.add_parser("init", help="Initialize a new BitBound project")
    init_parser.add_argument("name", nargs="?", default="bitbound_project", help="Project name")
    init_parser.add_argument(
        "--board", choices=["esp32", "esp32s3", "esp32c3", "esp8266", "rpi_pico", "rpi_pico_w"],
        default="esp32", help="Target board"
    )
    init_parser.add_argument(
        "--template", choices=["basic", "weather", "thermostat", "alarm"],
        default="basic", help="Project template"
    )

    # --- config ---
    config_parser = subparsers.add_parser("config", help="Manage configuration")
    config_sub = config_parser.add_subparsers(dest="config_action")

    config_show = config_sub.add_parser("show", help="Show current configuration")
    config_show.add_argument("--file", default="config.json", help="Config file path")

    config_set = config_sub.add_parser("set", help="Set a configuration value")
    config_set.add_argument("key", help="Config key (dot notation)")
    config_set.add_argument("value", help="Config value")
    config_set.add_argument("--file", default="config.json", help="Config file path")

    config_get = config_sub.add_parser("get", help="Get a configuration value")
    config_get.add_argument("key", help="Config key (dot notation)")
    config_get.add_argument("--file", default="config.json", help="Config file path")

    # --- monitor ---
    monitor_parser = subparsers.add_parser("monitor", help="Monitor device values")
    monitor_parser.add_argument("--device", help="Device type to monitor")
    monitor_parser.add_argument("--interval", type=float, default=1.0, help="Poll interval (seconds)")
    monitor_parser.add_argument("--count", type=int, default=0, help="Number of readings (0=unlimited)")
    monitor_parser.add_argument("--json", action="store_true", help="Output as JSON")

    # --- deploy ---
    deploy_parser = subparsers.add_parser("deploy", help="Deploy project to device")
    deploy_parser.add_argument("--port", help="Serial port (e.g., COM3, /dev/ttyUSB0)")
    deploy_parser.add_argument("--baud", type=int, default=115200, help="Baud rate")
    deploy_parser.add_argument("--path", default=".", help="Project path")

    # --- boards ---
    subparsers.add_parser("boards", help="List supported boards")

    # --- info ---
    info_parser = subparsers.add_parser("info", help="Show system/device information")

    return parser


def cmd_scan(args) -> None:
    """Execute scan command."""
    from bitbound import Hardware

    hw = Hardware()
    print("🔍 Scanning for devices...\n")

    results = {}

    if args.bus in ("i2c", "all"):
        addresses = hw.scan("I2C", scl=args.scl, sda=args.sda)
        results["i2c"] = addresses
        print("I2C Bus:")
        if addresses:
            for addr in addresses:
                name = _identify_i2c_device(addr)
                print(f"  0x{addr:02X} - {name}")
        else:
            print("  No devices found")
        print()

    if args.bus in ("all",):
        discovered = hw.discover()
        results["discovered"] = {
            k: [str(d) for d in v] for k, v in discovered.items() if v
        }

    if getattr(args, "json", False):
        print(json.dumps(results, indent=2))


def cmd_init(args) -> None:
    """Execute init command."""
    import os

    project_name = args.name
    board = args.board
    template = args.template

    print(f"📦 Initializing BitBound project: {project_name}")
    print(f"   Board: {board}")
    print(f"   Template: {template}\n")

    # Create project directory
    os.makedirs(project_name, exist_ok=True)

    # Create config
    from bitbound.config import Config
    config = Config(board=board)
    config.set("project.name", project_name)
    config.set("project.template", template)
    config.save(f"{project_name}/config.json")

    # Create main.py based on template
    templates = {
        "basic": _template_basic(board),
        "weather": _template_weather(board),
        "thermostat": _template_thermostat(board),
        "alarm": _template_alarm(board),
    }

    main_code = templates.get(template, templates["basic"])
    with open(f"{project_name}/main.py", "w") as f:
        f.write(main_code)

    # Create boot.py
    with open(f"{project_name}/boot.py", "w") as f:
        f.write("# boot.py - runs on boot\nimport gc\ngc.collect()\n")

    print(f"✅ Project created at ./{project_name}/")
    print(f"   - main.py ({template} template)")
    print(f"   - config.json")
    print(f"   - boot.py")
    print(f"\n💡 Next: cd {project_name} && bitbound deploy")


def cmd_config(args) -> None:
    """Execute config command."""
    from bitbound.config import Config

    config_file = args.file if hasattr(args, "file") else "config.json"

    if args.config_action == "show":
        config = Config.from_file(config_file)
        print(json.dumps(config.to_dict(), indent=2))

    elif args.config_action == "set":
        config = Config.from_file(config_file)
        try:
            value = json.loads(args.value)
        except (json.JSONDecodeError, ValueError):
            value = args.value
        config.set(args.key, value)
        config.save(config_file)
        print(f"✅ Set {args.key} = {value}")

    elif args.config_action == "get":
        config = Config.from_file(config_file)
        value = config.get(args.key)
        if value is not None:
            print(value)
        else:
            print(f"Key not found: {args.key}")
            sys.exit(1)

    else:
        print("Usage: bitbound config {show|set|get}")


def cmd_monitor(args) -> None:
    """Execute monitor command."""
    from bitbound import Hardware

    hw = Hardware()
    device_type = args.device or "BME280"

    print(f"📊 Monitoring {device_type} (interval: {args.interval}s)")
    print(f"   Press Ctrl+C to stop\n")

    try:
        bus_type = "I2C"
        if device_type.upper() in ("DHT11", "DHT22", "PIR", "LED"):
            bus_type = "GPIO"
            sensor = hw.attach(bus_type, type=device_type, pin=4)
        else:
            sensor = hw.attach(bus_type, type=device_type)

        count = 0
        while args.count == 0 or count < args.count:
            values = sensor.read_all()
            if getattr(args, "json", False):
                print(json.dumps({"timestamp": time.time(), **values}))
            else:
                parts = [f"{k}: {v}" for k, v in values.items()
                         if not k.startswith("_") and v is not None
                         and k not in ("name", "address", "connected", "properties")]
                print(f"[{time.strftime('%H:%M:%S')}] {' | '.join(parts)}")

            count += 1
            if args.count == 0 or count < args.count:
                time.sleep(args.interval)

    except KeyboardInterrupt:
        print("\n\n📊 Monitoring stopped.")


def cmd_deploy(args) -> None:
    """Execute deploy command."""
    port = args.port
    baud = args.baud
    path = args.path

    if not port:
        # Auto-detect serial port
        ports = _detect_serial_ports()
        if ports:
            port = ports[0]
            print(f"🔌 Auto-detected port: {port}")
        else:
            print("❌ No serial port detected. Use --port to specify.")
            sys.exit(1)

    print(f"🚀 Deploying from {path} to {port} ({baud} baud)")
    print("   Using mpremote...\n")

    import subprocess
    try:
        result = subprocess.run(
            ["mpremote", "connect", port, "cp", "-r", f"{path}/.", ":"],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            print("✅ Deployment successful!")
        else:
            print(f"❌ Deployment failed: {result.stderr}")
    except FileNotFoundError:
        print("❌ mpremote not found. Install with: pip install mpremote")
        sys.exit(1)


def cmd_boards(args) -> None:
    """Execute boards command."""
    from bitbound.config import Config
    boards = Config.available_boards()

    print("📋 Supported Boards:\n")
    for board in boards:
        profile = Config.get_board_profile(board)
        name = profile.get("board", board) if profile else board
        i2c = profile.get("i2c", {}) if profile else {}
        print(f"  {board:15s} - {name}")
        if i2c:
            print(f"  {'':15s}   I2C: SCL={i2c.get('scl')}, SDA={i2c.get('sda')}")


def cmd_info(args) -> None:
    """Execute info command."""
    import platform

    print("ℹ️  BitBound System Info\n")
    print(f"  Python:     {platform.python_version()}")
    print(f"  Platform:   {platform.platform()}")
    print(f"  Arch:       {platform.machine()}")

    try:
        from bitbound import __version__
        print(f"  BitBound:   {__version__}")
    except Exception:
        print("  BitBound:   unknown")

    # Check for MicroPython tools
    import shutil
    tools = {
        "mpremote": shutil.which("mpremote"),
        "ampy": shutil.which("ampy"),
        "esptool": shutil.which("esptool.py") or shutil.which("esptool"),
    }
    print("\n  Available tools:")
    for name, path in tools.items():
        status = "✅" if path else "❌"
        print(f"    {status} {name}")


def _identify_i2c_device(address: int) -> str:
    """Identify a device by its I2C address."""
    known = {
        0x20: "PCF8574 (I/O Expander)",
        0x23: "BH1750 (Light Sensor)",
        0x27: "LCD I2C",
        0x3C: "SSD1306 (OLED 128x64)",
        0x3D: "SSD1306 (OLED 128x32)",
        0x3F: "LCD I2C (alt)",
        0x48: "ADS1115 (ADC)",
        0x50: "AT24C (EEPROM)",
        0x5C: "BH1750 (alt)",
        0x68: "MPU6050 / DS3231 (RTC)",
        0x69: "MPU6050 (alt)",
        0x76: "BME280 / BMP280",
        0x77: "BME280 / BMP280 (alt)",
    }
    return known.get(address, "Unknown device")


def _detect_serial_ports() -> List[str]:
    """Detect available serial ports."""
    try:
        import serial.tools.list_ports
        ports = list(serial.tools.list_ports.comports())
        return [p.device for p in ports if "USB" in p.description or "UART" in p.description]
    except ImportError:
        return []


def _template_basic(board: str) -> str:
    return '''"""BitBound Basic Template"""
from bitbound import Hardware

hw = Hardware()

# Attach a sensor (simulation mode on desktop)
sensor = hw.attach("I2C", type="BME280")
led = hw.attach("GPIO", type="LED", pin=2)

# Read sensor
data = sensor.read_all()
print(f"Temperature: {data.get('temperature')}°C")
print(f"Humidity: {data.get('humidity')}%")
print(f"Pressure: {data.get('pressure')} hPa")

# Blink LED
led.blink(times=3)
'''


def _template_weather(board: str) -> str:
    return '''"""BitBound Weather Station Template"""
from bitbound import Hardware
from bitbound.logging import DataLogger, LogFormat

hw = Hardware()

sensor = hw.attach("I2C", type="BME280")
oled = hw.attach("I2C", type="SSD1306")
logger = DataLogger("weather", format=LogFormat.CSV)
logger.add_device(sensor, properties=["temperature", "humidity", "pressure"])

def update_display(e):
    data = sensor.read_all()
    oled.clear()
    oled.text(f"T: {data.get('temperature', 0):.1f}C", 0, 0)
    oled.text(f"H: {data.get('humidity', 0):.1f}%", 0, 16)
    oled.text(f"P: {data.get('pressure', 0):.0f}hPa", 0, 32)
    oled.show()

sensor.on_interval(5000, update_display)
logger.start(interval_ms=60000)

hw.run()
'''


def _template_thermostat(board: str) -> str:
    return '''"""BitBound Smart Thermostat Template"""
from bitbound import Hardware

hw = Hardware()

sensor = hw.attach("I2C", type="BME280")
fan = hw.attach("GPIO", type="Relay", pin=5)
heater = hw.attach("GPIO", type="Relay", pin=6)

sensor.on_threshold("temperature > 28°C", lambda e: (fan.on(), heater.off()))
sensor.on_threshold("temperature < 20°C", lambda e: (heater.on(), fan.off()))
sensor.on_threshold("temperature BETWEEN 20°C AND 28°C", lambda e: (fan.off(), heater.off()))

sensor.on_change("temperature", lambda e:
    print(f"Temperature: {e.old_value} -> {e.new_value}°C")
)

hw.run()
'''


def _template_alarm(board: str) -> str:
    return '''"""BitBound Motion Alarm Template"""
from bitbound import Hardware

hw = Hardware()

pir = hw.attach("GPIO", type="PIR", pin=4)
buzzer = hw.attach("GPIO", type="Buzzer", pin=15)
led = hw.attach("GPIO", type="LED", pin=2)

armed = True

def on_motion(e):
    if armed:
        print("⚠️ Motion detected!")
        buzzer.beep(duration_ms=1000)
        led.blink(times=5)

pir.on_change("motion", on_motion)
hw.run()
'''


def main() -> None:
    """Main entry point for the CLI."""
    parser = create_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    commands = {
        "scan": cmd_scan,
        "init": cmd_init,
        "config": cmd_config,
        "monitor": cmd_monitor,
        "deploy": cmd_deploy,
        "boards": cmd_boards,
        "info": cmd_info,
    }

    handler = commands.get(args.command)
    if handler:
        handler(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
