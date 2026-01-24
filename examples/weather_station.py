"""
BitBound Example: IoT Weather Station

A complete weather station that reads environmental data
and displays it on an OLED screen.
"""

from bitbound import Hardware
import time


def main():
    hw = Hardware()
    
    # Sensors
    bme = hw.attach("I2C", type="BME280")
    light = hw.attach("I2C", type="BH1750")
    
    # Display
    oled = hw.attach("I2C", type="SSD1306", address=0x3C)
    
    # Status LED
    led = hw.attach("GPIO", type="LED", pin=2)
    
    print("🌤️  Weather Station Starting...")
    
    def update_display(event=None):
        """Update OLED display with current readings."""
        temp = bme.temperature
        humidity = bme.humidity
        pressure = bme.pressure
        lux = light.lux
        
        oled.clear()
        oled.text("Weather Station", 0, 0)
        oled.line(0, 10, 127, 10)
        oled.text(f"Temp: {temp:.1f}C", 0, 16)
        oled.text(f"Hum:  {humidity:.1f}%", 0, 26)
        oled.text(f"Pres: {pressure:.0f}hPa", 0, 36)
        oled.text(f"Light: {lux:.0f}lux", 0, 46)
        oled.show()
        
        # Blink LED to show activity
        led.blink(times=1, on_time=0.05, off_time=0.05)
    
    # Update every 5 seconds
    bme.on_interval(5000, update_display)
    
    # Alert on rapid pressure changes (storm warning)
    last_pressure = [bme.pressure]
    
    def check_pressure_change(event):
        current = bme.pressure
        change = current - last_pressure[0]
        last_pressure[0] = current
        
        if abs(change) > 3:  # More than 3 hPa change
            print(f"⚠️  Rapid pressure change: {change:+.1f} hPa")
            led.blink(times=5, on_time=0.1, off_time=0.1)
    
    bme.on_change("pressure", check_pressure_change)
    
    # Initial update
    update_display()
    
    print("📊 Weather Station running...")
    print("   Press Ctrl+C to stop\n")
    
    try:
        hw.run()
    except KeyboardInterrupt:
        print("\n🛑 Shutting down...")
        oled.clear()
        oled.text("Goodbye!", 40, 28)
        oled.show()
        time.sleep(1)
        oled.clear()
        hw.stop()


if __name__ == "__main__":
    main()
