"""
BitBound Example: Smart Thermostat

Demonstrates using BitBound for a simple smart thermostat system
with temperature monitoring and automatic fan control.
"""

from bitbound import Hardware


def main():
    # Initialize hardware
    hw = Hardware()
    
    # Attach devices
    sensor = hw.attach("I2C", type="BME280")
    fan = hw.attach("GPIO", type="Relay", pin=5, name="Fan")
    led = hw.attach("GPIO", type="LED", pin=2, name="StatusLED")
    lcd = hw.attach("I2C", type="LCD1602")
    
    # Configuration
    TARGET_TEMP = 23.0
    TEMP_HYSTERESIS = 2.0
    
    print("🌡️  Smart Thermostat Starting...")
    print(f"   Target: {TARGET_TEMP}°C")
    print(f"   Hysteresis: ±{TEMP_HYSTERESIS}°C")
    
    # Define threshold callbacks
    def on_too_hot(event):
        print(f"🔥 Temperature too high: {event.new_value}°C - Turning ON fan")
        fan.on()
        led.on()
    
    def on_cool_enough(event):
        print(f"❄️  Temperature normal: {event.new_value}°C - Turning OFF fan")
        fan.off()
        led.off()
    
    def on_temp_change(event):
        temp = sensor.temperature
        humidity = sensor.humidity
        
        # Update display
        lcd.clear()
        lcd.write(f"Temp: {temp:.1f}C", y=0)
        lcd.write(f"Humidity: {humidity:.1f}%", y=1)
    
    # Register events with threshold expressions
    sensor.on_threshold(
        f"temperature > {TARGET_TEMP + TEMP_HYSTERESIS}°C",
        on_too_hot,
        debounce_ms=5000  # Prevent rapid switching
    )
    
    sensor.on_threshold(
        f"temperature < {TARGET_TEMP - TEMP_HYSTERESIS}°C",
        on_cool_enough,
        debounce_ms=5000
    )
    
    # Update display on any temperature change
    sensor.on_change("temperature", on_temp_change)
    
    # Initial display update
    lcd.write(f"Temp: {sensor.temperature:.1f}C", y=0)
    lcd.write(f"Humidity: {sensor.humidity:.1f}%", y=1)
    
    print("\n📊 Current readings:")
    print(f"   Temperature: {sensor.temperature}°C")
    print(f"   Humidity: {sensor.humidity}%")
    print(f"   Pressure: {sensor.pressure} hPa")
    print(f"   Fan status: {'ON' if fan.state else 'OFF'}")
    
    print("\n🔄 Running event loop... (Ctrl+C to stop)")
    
    try:
        hw.run()
    except KeyboardInterrupt:
        print("\n\n🛑 Shutting down...")
        fan.off()
        led.off()
        lcd.clear()
        lcd.write("Goodbye!", y=0)
        hw.stop()


if __name__ == "__main__":
    main()
