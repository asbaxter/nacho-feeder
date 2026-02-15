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
        # "Always Stutter" / Cycle Logic
        # The 'direction' param is largely ignored now; 
        # actual movement is dictated by cycle_fwd vs cycle_back ratios.
        
        total_run = 0
        
        # If both are 0, default to standard forward to prevent infinite loop/no-op
        if cycle_fwd == 0 and cycle_back == 0:
            cycle_fwd = 100

        while total_run < steps:
            if stop_event and stop_event.is_set(): return
            
            # --- Forward Phase ---
            remaining = steps - total_run
            if remaining <= 0: break
            
            to_move = min(cycle_fwd, remaining)
            if to_move > 0:
                _move_raw(to_move, "forward", stop_event)
                total_run += to_move
                if stop_event and stop_event.is_set(): return
            
            # Break if done
            if total_run >= steps: break
            
            # --- Reverse Phase ---
            remaining = steps - total_run
            if remaining <= 0: break
            
            to_move = min(cycle_back, remaining)
            if to_move > 0:
                # Small pause before reversing direction
                time.sleep(0.1)
                _move_raw(to_move, "reverse", stop_event)
                total_run += to_move
                if stop_event and stop_event.is_set(): return
                time.sleep(0.1) # Pause after reverse
                
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
            time.sleep(0.005) # Slower speed = Higher Torque



