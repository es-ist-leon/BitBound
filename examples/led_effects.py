"""
BitBound Example: LED Effects

Demonstrates various LED and NeoPixel effects.
"""

from bitbound import Hardware
import time


def main():
    hw = Hardware()
    
    # Single LED
    led = hw.attach("GPIO", type="LED", pin=2)
    
    # RGB LED
    rgb = hw.attach("GPIO", type="RGB", pins={"r": 12, "g": 13, "b": 14})
    
    # NeoPixel strip (8 LEDs)
    strip = hw.attach("GPIO", type="NeoPixel", pin=16, num_leds=8)
    
    print("💡 LED Effects Demo\n")
    
    # Simple LED blink
    print("1. Simple LED blink")
    led.blink(times=5, on_time=0.2, off_time=0.2)
    time.sleep(1)
    
    # RGB color cycle
    print("2. RGB color cycle")
    colors = ["red", "green", "blue", "yellow", "cyan", "magenta", "white"]
    for color in colors:
        print(f"   {color}")
        rgb.color = color
        time.sleep(0.5)
    rgb.off()
    time.sleep(0.5)
    
    # RGB fade
    print("3. RGB fade: red -> blue")
    rgb.fade((255, 0, 0), (0, 0, 255), duration=2.0)
    rgb.off()
    time.sleep(0.5)
    
    # NeoPixel fill
    print("4. NeoPixel fill")
    for color in [(255, 0, 0), (0, 255, 0), (0, 0, 255)]:
        strip.fill(color)
        time.sleep(0.5)
    
    # NeoPixel chase
    print("5. NeoPixel chase")
    for _ in range(3):
        for i in range(len(strip)):
            strip.fill((0, 0, 0))
            strip[i] = (255, 255, 255)
            time.sleep(0.1)
    
    # NeoPixel rainbow
    print("6. NeoPixel rainbow")
    strip.rainbow(delay_ms=10)
    
    # Cleanup
    strip.clear()
    led.off()
    rgb.off()
    
    print("\n✅ Demo complete!")
    hw.stop()


if __name__ == "__main__":
    main()
