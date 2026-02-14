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


def run_motor(steps, direction="forward", stutter=False):
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)
    for pin in PINS:
        GPIO.setup(pin, GPIO.OUT)
    
    try:
        if stutter and direction == "forward":
             # Stutter mode: Move forward significantly, then back a bit to clear jams.
             # Cycle: Forward 50, Back 20 (Net +30)
             cycle_fwd = 50
             cycle_back = 20
             cycle_net = cycle_fwd - cycle_back
             
             remaining = steps
             while remaining >= cycle_fwd:
                 _move_raw(cycle_fwd, "forward")
                 time.sleep(0.1)
                 _move_raw(cycle_back, "reverse")
                 time.sleep(0.1)
                 remaining -= cycle_net
            
             # Finish remaining steps
             if remaining > 0:
                 _move_raw(remaining, "forward")
        else:
            # Standard operation
            _move_raw(steps, direction)
            
    finally:
        # Turn off pins to save 9V battery
        for pin in PINS:
            GPIO.output(pin, False)
        GPIO.cleanup()

def _move_raw(steps, direction):
    # Reverse sequence if direction is 'reverse'
    seq = SEQUENCE if direction == "forward" else list(reversed(SEQUENCE))
    
    for _ in range(steps):
        for step in seq:
            for i in range(4):
                GPIO.output(PINS[i], step[i])
            time.sleep(0.004) # Adjust for speed

