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


def run_motor(steps, direction="forward", stutter=False, cycle_fwd=100, cycle_back=20, stop_event=None):
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)
    for pin in PINS:
        GPIO.setup(pin, GPIO.OUT)
    
    try:
        if stutter and direction == "forward":
             # Stutter mode: Move forward significantly, then back a bit to clear jams.
             # Count TOTAL steps (fwd + back) to control total run time/activity.
             
             total_run = 0
             cycle_total = cycle_fwd + cycle_back
             
             while total_run < steps:
                 if stop_event and stop_event.is_set(): return
                 
                 # Check if we can do a full cycle
                 if total_run + cycle_total <= steps:
                     _move_raw(cycle_fwd, "forward", stop_event)
                     if stop_event and stop_event.is_set(): return
                     time.sleep(0.1)
                     
                     _move_raw(cycle_back, "reverse", stop_event)
                     if stop_event and stop_event.is_set(): return
                     time.sleep(0.1)
                     
                     total_run += cycle_total
                 else:
                     # Run remaining steps forward
                     remaining = steps - total_run
                     if remaining > 0:
                         _move_raw(remaining, "forward", stop_event)
                     break
        else:
            # Standard operation
            _move_raw(steps, direction, stop_event)
            
    finally:
        # Turn off pins to save 9V battery
        for pin in PINS:
            GPIO.output(pin, False)
        GPIO.cleanup()

def _move_raw(steps, direction, stop_event=None):
    # Reverse sequence if direction is 'reverse'
    seq = SEQUENCE if direction == "forward" else list(reversed(SEQUENCE))
    
    for _ in range(steps):
        if stop_event and stop_event.is_set(): return
        for step in seq:
            for i in range(4):
                GPIO.output(PINS[i], step[i])
            time.sleep(0.004) # Adjust for speed



