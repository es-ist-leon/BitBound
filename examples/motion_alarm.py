"""
BitBound Example: Motion Alarm

Simple motion detection alarm with buzzer and LED.
"""

from bitbound import Hardware
import time


def main():
    hw = Hardware()
    
    # PIR motion sensor
    pir = hw.attach("GPIO", type="PIR", pin=14)
    
    # Alarm outputs
    buzzer = hw.attach("GPIO", type="Buzzer", pin=15)
    led = hw.attach("GPIO", type="LED", pin=2)
    
    # LCD for status
    lcd = hw.attach("I2C", type="LCD1602")
    
    armed = [False]
    
    print("🚨 Motion Alarm System")
    print("   Press Enter to arm/disarm\n")
    
    lcd.write("Motion Alarm", y=0)
    lcd.write("Status: DISARMED", y=1)
    
    def on_motion(event):
        if not armed[0]:
            return
        
        print("⚠️  MOTION DETECTED!")
        lcd.clear()
        lcd.write("!! ALERT !!", y=0)
        lcd.write("Motion detected!", y=1)
        
        # Sound alarm
        for _ in range(3):
            buzzer.beep(freq=2000, duration=0.2)
            led.on()
            time.sleep(0.1)
            buzzer.beep(freq=1500, duration=0.2)
            led.off()
            time.sleep(0.1)
        
        lcd.clear()
        lcd.write("Motion Alarm", y=0)
        lcd.write("Status: ARMED", y=1)
    
    # Register motion detection
    pir.on_change("motion", on_motion)
    
    # Simple command loop
    print("Commands: 'arm', 'disarm', 'quit'\n")
    
    hw.start()  # Start event loop in background
    
    try:
        while True:
            cmd = input("> ").strip().lower()
            
            if cmd == "arm":
                armed[0] = True
                print("🔒 System ARMED")
                buzzer.beep(freq=1000, duration=0.1)
                lcd.write("Status: ARMED  ", y=1)
                
            elif cmd == "disarm":
                armed[0] = False
                print("🔓 System DISARMED")
                buzzer.beep(freq=500, duration=0.1)
                lcd.write("Status: DISARMED", y=1)
                
            elif cmd == "quit":
                break
                
            elif cmd == "status":
                print(f"   Armed: {armed[0]}")
                print(f"   Motion: {pir.motion}")
                
    except KeyboardInterrupt:
        pass
    
    print("\n🛑 Shutting down...")
    buzzer.off()
    led.off()
    lcd.clear()
    hw.stop()


if __name__ == "__main__":
    main()
