try:
    import RPi.GPIO as GPIO
except ImportError:
    print("RPi.GPIO not found, using mock for local development")
    class MockGPIO:
        BCM = "BCM"
        OUT = "OUT"
        def setwarnings(self, *args): pass
        def setmode(self, *args): pass
        def setup(self, *args): pass
        def output(self, *args): pass
        def cleanup(self, *args): pass
    GPIO = MockGPIO()
import time

PINS = [17, 18, 27, 22]
SEQUENCE = [[1, 1, 0, 0], [0, 1, 1, 0], [0, 0, 1, 1], [1, 0, 0, 1]]

def run_motor(steps, direction="forward"):
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)
    for pin in PINS:
        GPIO.setup(pin, GPIO.OUT)
    
    # Reverse sequence if direction is 'reverse'
    seq = SEQUENCE if direction == "forward" else list(reversed(SEQUENCE))
    
    try:
        for _ in range(steps):
            for step in seq:
                for i in range(4):
                    GPIO.output(PINS[i], step[i])
                time.sleep(0.004) # Adjust for speed
    finally:
        # Turn off pins to save 9V battery
        for pin in PINS:
            GPIO.output(pin, False)
        GPIO.cleanup()
