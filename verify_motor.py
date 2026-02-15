import motor_logic
import time

def test_direction(fwd, back, name):
    print(f"--- Testing {name} ---")
    print(f"Cycle: {fwd} Fwd, {back} Back")
    
    start = time.time()
    # Run for a small total amount to verify direction logic holds
    motor_logic.run_motor(200, "forward", stutter=True, cycle_fwd=fwd, cycle_back=back)
    print(f"Completed in {time.time() - start:.2f}s")
    print("-----------------------")

# Test 1: Net Forward (Standard)
test_direction(100, 20, "Net Forward (+80)")

# Test 2: Net Reverse
test_direction(20, 100, "Net Reverse (-80)")

# Test 3: Zero Forward
test_direction(0, 50, "Zero Forward (Strict Reverse)")
