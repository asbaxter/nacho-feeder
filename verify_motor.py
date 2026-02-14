import motor_logic
import time

print("Testing standard move...")
motor_logic.run_motor(100, "forward", stutter=False)
print("Standard move complete.")

print("Testing granular stutter move (Fwd 50, Back 10)...")
start = time.time()
# Should do roughly 2 cycles of (50 fwd, 10 back) -> net 80, then 20 remainder
motor_logic.run_motor(100, "forward", stutter=True, cycle_fwd=50, cycle_back=10)
print(f"Granular stutter move complete in {time.time() - start:.2f}s")
