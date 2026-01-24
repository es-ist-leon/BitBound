"""
Motor actuators (DC, Servo, Stepper).
"""

from typing import Any, Dict, Optional
import time
from ...device import Actuator, DeviceInfo


class Motor(Actuator):
    """Base class for motor actuators."""
    pass


class DCMotor(Motor):
    """
    DC Motor with PWM speed control.
    
    Example:
        from bitbound import Hardware
        
        hw = Hardware()
        motor = hw.attach("GPIO", type="DCMotor",
                         enable_pin=5, in1_pin=6, in2_pin=7)
        
        motor.forward(speed=75)   # 75% speed forward
        motor.backward(speed=50)  # 50% speed backward
        motor.stop()
    """
    
    def __init__(
        self,
        bus,
        enable_pin: int,
        in1_pin: int,
        in2_pin: int,
        freq: int = 1000,
        name: str = "DCMotor"
    ):
        """
        Initialize DC motor.
        
        Args:
            bus: GPIO bus instance
            enable_pin: PWM enable pin
            in1_pin: Direction pin 1
            in2_pin: Direction pin 2
            freq: PWM frequency
            name: Device name
        """
        super().__init__(bus, None, name)
        
        self._enable_pin = enable_pin
        self._in1_pin = in1_pin
        self._in2_pin = in2_pin
        self._freq = freq
        
        self._in1 = None
        self._in2 = None
        self._speed = 0
        self._direction = 0  # 0=stopped, 1=forward, -1=backward
    
    def connect(self) -> bool:
        """Connect to motor."""
        try:
            if hasattr(self._bus, 'output'):
                self._in1 = self._bus.output(self._in1_pin)
                self._in2 = self._bus.output(self._in2_pin)
                self._bus.pwm(self._enable_pin, self._freq, 0)
            
            self._connected = True
            return True
        except Exception as e:
            print(f"DCMotor connect error: {e}")
            return False
    
    def disconnect(self) -> None:
        """Disconnect from motor."""
        self.stop()
        self._connected = False
    
    def get_info(self) -> DeviceInfo:
        """Get device information."""
        return DeviceInfo(
            device_type="actuator",
            name=self._name,
            model="DCMotor",
            bus_type="GPIO",
            capabilities=["forward", "backward", "stop", "speed"]
        )
    
    def on(self) -> None:
        """Turn on (forward at current speed)."""
        self.forward(self._speed if self._speed > 0 else 100)
    
    def off(self) -> None:
        """Turn off."""
        self.stop()
    
    def forward(self, speed: int = 100) -> None:
        """
        Run motor forward.
        
        Args:
            speed: Speed percentage (0-100)
        """
        speed = max(0, min(100, speed))
        
        if self._in1:
            self._in1.on()
        if self._in2:
            self._in2.off()
        
        if hasattr(self._bus, 'set_pwm_duty'):
            self._bus.set_pwm_duty(self._enable_pin, speed)
        
        self._speed = speed
        self._direction = 1
    
    def backward(self, speed: int = 100) -> None:
        """
        Run motor backward.
        
        Args:
            speed: Speed percentage (0-100)
        """
        speed = max(0, min(100, speed))
        
        if self._in1:
            self._in1.off()
        if self._in2:
            self._in2.on()
        
        if hasattr(self._bus, 'set_pwm_duty'):
            self._bus.set_pwm_duty(self._enable_pin, speed)
        
        self._speed = speed
        self._direction = -1
    
    def stop(self) -> None:
        """Stop the motor."""
        if self._in1:
            self._in1.off()
        if self._in2:
            self._in2.off()
        
        if hasattr(self._bus, 'set_pwm_duty'):
            self._bus.set_pwm_duty(self._enable_pin, 0)
        
        self._speed = 0
        self._direction = 0
    
    def brake(self) -> None:
        """Active brake (short motor terminals)."""
        if self._in1:
            self._in1.on()
        if self._in2:
            self._in2.on()
        
        self._speed = 0
        self._direction = 0
    
    def set_speed(self, speed: int) -> None:
        """Set motor speed without changing direction."""
        speed = max(0, min(100, speed))
        
        if hasattr(self._bus, 'set_pwm_duty'):
            self._bus.set_pwm_duty(self._enable_pin, speed)
        
        self._speed = speed
    
    @property
    def speed(self) -> int:
        """Get current speed."""
        return self._speed
    
    @property
    def direction(self) -> int:
        """Get current direction (-1, 0, 1)."""
        return self._direction
    
    def read_all(self) -> Dict[str, Any]:
        """Read all values."""
        return {"speed": self._speed, "direction": self._direction}


class ServoMotor(Motor):
    """
    Servo Motor with angle control.
    
    Example:
        from bitbound import Hardware
        
        hw = Hardware()
        servo = hw.attach("GPIO", type="Servo", pin=15)
        
        servo.angle = 90   # Move to 90°
        servo.angle = 0    # Move to 0°
    """
    
    def __init__(
        self,
        bus,
        pin: int,
        min_pulse: int = 500,
        max_pulse: int = 2500,
        min_angle: int = 0,
        max_angle: int = 180,
        freq: int = 50,
        name: str = "Servo"
    ):
        """
        Initialize servo motor.
        
        Args:
            bus: GPIO bus instance
            pin: PWM pin
            min_pulse: Minimum pulse width in µs
            max_pulse: Maximum pulse width in µs
            min_angle: Minimum angle
            max_angle: Maximum angle
            freq: PWM frequency (typically 50Hz)
            name: Device name
        """
        super().__init__(bus, pin, name)
        
        self._pin = pin
        self._min_pulse = min_pulse
        self._max_pulse = max_pulse
        self._min_angle = min_angle
        self._max_angle = max_angle
        self._freq = freq
        
        self._angle = 90
        self._pwm = None
    
    def connect(self) -> bool:
        """Connect to servo."""
        try:
            try:
                from machine import Pin, PWM
                self._pwm = PWM(Pin(self._pin), freq=self._freq)
                self._connected = True
            except ImportError:
                # Simulation mode
                self._connected = True
            return True
        except Exception as e:
            print(f"Servo connect error: {e}")
            return False
    
    def disconnect(self) -> None:
        """Disconnect from servo."""
        if self._pwm:
            self._pwm.deinit()
        self._connected = False
    
    def get_info(self) -> DeviceInfo:
        """Get device information."""
        return DeviceInfo(
            device_type="actuator",
            name=self._name,
            model="Servo",
            address=self._pin,
            bus_type="GPIO",
            capabilities=["angle"],
            properties={
                "min_angle": self._min_angle,
                "max_angle": self._max_angle
            }
        )
    
    def on(self) -> None:
        """Move to center position."""
        self.angle = (self._min_angle + self._max_angle) // 2
    
    def off(self) -> None:
        """Disable servo (stop PWM)."""
        if self._pwm:
            self._pwm.duty_u16(0)
    
    @property
    def angle(self) -> int:
        """Get current angle."""
        return self._angle
    
    @angle.setter
    def angle(self, value: int) -> None:
        """Set servo angle."""
        value = max(self._min_angle, min(self._max_angle, value))
        
        # Calculate pulse width
        pulse_range = self._max_pulse - self._min_pulse
        angle_range = self._max_angle - self._min_angle
        pulse = self._min_pulse + (value - self._min_angle) * pulse_range // angle_range
        
        # Convert to duty cycle (16-bit)
        # Period = 1/freq seconds = 1000000/freq µs
        period_us = 1000000 // self._freq
        duty = int(pulse * 65535 // period_us)
        
        if self._pwm:
            self._pwm.duty_u16(duty)
        
        self._angle = value
    
    def sweep(self, start: int, end: int, step: int = 1, delay_ms: int = 15) -> None:
        """
        Sweep servo from start to end angle.
        
        Args:
            start: Start angle
            end: End angle
            step: Step size
            delay_ms: Delay between steps
        """
        if start < end:
            angles = range(start, end + 1, step)
        else:
            angles = range(start, end - 1, -step)
        
        for a in angles:
            self.angle = a
            time.sleep(delay_ms / 1000.0)
    
    def read_all(self) -> Dict[str, Any]:
        """Read all values."""
        return {"angle": self._angle}


class StepperMotor(Motor):
    """
    Stepper Motor control.
    
    Example:
        from bitbound import Hardware
        
        hw = Hardware()
        stepper = hw.attach("GPIO", type="Stepper",
                           pins=[12, 13, 14, 15])
        
        stepper.step(100)   # 100 steps forward
        stepper.step(-50)   # 50 steps backward
        stepper.rotate(90)  # Rotate 90°
    """
    
    # Full step sequence
    FULL_STEP = [
        [1, 0, 1, 0],
        [0, 1, 1, 0],
        [0, 1, 0, 1],
        [1, 0, 0, 1],
    ]
    
    # Half step sequence
    HALF_STEP = [
        [1, 0, 0, 0],
        [1, 1, 0, 0],
        [0, 1, 0, 0],
        [0, 1, 1, 0],
        [0, 0, 1, 0],
        [0, 0, 1, 1],
        [0, 0, 0, 1],
        [1, 0, 0, 1],
    ]
    
    def __init__(
        self,
        bus,
        pins: list,
        steps_per_rev: int = 2048,
        half_step: bool = True,
        name: str = "Stepper"
    ):
        """
        Initialize stepper motor.
        
        Args:
            bus: GPIO bus instance
            pins: List of 4 control pins [IN1, IN2, IN3, IN4]
            steps_per_rev: Steps per revolution
            half_step: Use half-stepping for smoother motion
            name: Device name
        """
        super().__init__(bus, None, name)
        
        self._pins = pins
        self._steps_per_rev = steps_per_rev
        self._half_step = half_step
        self._sequence = self.HALF_STEP if half_step else self.FULL_STEP
        
        self._gpio_pins = []
        self._step_index = 0
        self._position = 0
    
    def connect(self) -> bool:
        """Connect to stepper motor."""
        try:
            if hasattr(self._bus, 'output'):
                for pin in self._pins:
                    self._gpio_pins.append(self._bus.output(pin))
            
            self._connected = True
            return True
        except Exception as e:
            print(f"Stepper connect error: {e}")
            return False
    
    def disconnect(self) -> None:
        """Disconnect and release motor."""
        self.release()
        self._connected = False
    
    def get_info(self) -> DeviceInfo:
        """Get device information."""
        return DeviceInfo(
            device_type="actuator",
            name=self._name,
            model="Stepper",
            bus_type="GPIO",
            capabilities=["step", "rotate"],
            properties={"steps_per_rev": self._steps_per_rev}
        )
    
    def on(self) -> None:
        """Hold current position."""
        self._set_step(self._step_index)
    
    def off(self) -> None:
        """Release motor (no holding torque)."""
        self.release()
    
    def _set_step(self, step_index: int) -> None:
        """Set coil pattern for a step."""
        pattern = self._sequence[step_index % len(self._sequence)]
        for i, pin in enumerate(self._gpio_pins):
            pin.value = pattern[i]
    
    def step(self, steps: int, delay_ms: int = 2) -> None:
        """
        Move a number of steps.
        
        Args:
            steps: Number of steps (positive=forward, negative=backward)
            delay_ms: Delay between steps
        """
        direction = 1 if steps > 0 else -1
        steps = abs(steps)
        
        for _ in range(steps):
            self._step_index = (self._step_index + direction) % len(self._sequence)
            self._set_step(self._step_index)
            self._position += direction
            time.sleep(delay_ms / 1000.0)
    
    def rotate(self, degrees: float, delay_ms: int = 2) -> None:
        """
        Rotate a number of degrees.
        
        Args:
            degrees: Degrees to rotate (positive=CW, negative=CCW)
            delay_ms: Delay between steps
        """
        steps = int(degrees * self._steps_per_rev / 360)
        self.step(steps, delay_ms)
    
    def release(self) -> None:
        """Release motor (disable all coils)."""
        for pin in self._gpio_pins:
            pin.value = 0
    
    @property
    def position(self) -> int:
        """Get current position in steps."""
        return self._position
    
    def reset_position(self) -> None:
        """Reset position counter to zero."""
        self._position = 0
    
    def read_all(self) -> Dict[str, Any]:
        """Read all values."""
        return {"position": self._position}
