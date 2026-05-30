# Nacho Feeder

An automated pet feeding system designed for Nacho the lizard. The project integrates a 3D-printed hopper dispenser, a Raspberry Pi-driven stepper motor, a Flask-based web control portal, and a secure Tailscale VPN tunnel for remote mobile access.

---

## Project Overview

This repository contains the software and configuration for a smart pet feeder. The physical unit is based on the [Thingiverse 3D-Printed Feeder design (Thing #3966726)](https://www.thingiverse.com/thing:3966726), modified with a custom-designed extender to increase food storage capacity. 

A stepper motor drives a spiral auger screw to push food portions forward and out of the dispenser. The software, running on a Raspberry Pi, hosts a lightweight web interface to control the feeding process, set schedules, and monitor historical feeding logs. For secure remote operation, a private Tailscale VPN tunnel is used, removing the need to expose ports to the public internet.

```
                  +----------------------------------------+
                  |            Tailscale VPN               |
                  |       (Secure Mobile Access)           |
                  +-------------------+--------------------+
                                      |
                                      v
+------------------+       +------------------+       +------------------+
|  Mobile/Desktop  |------>|   Flask Server   |------>|   RPi.GPIO Pins  |
|     Browser      |       |     (app.py)     |       |  [17, 18, 27, 22]|
+------------------+       +------------------+       +------------------+
                                    |                          |
                                    v                          v
                         +--------------------+       +------------------+
                         | SQLite/JSON Config |       |  Stepper Motor   |
                         | (schedule_config)  |       |  (Auger Screw)   |
                         +--------------------+       +------------------+
```

---

## Features

*   **Responsive Web Portal**: Clean dashboard to trigger manual feedings, configure daily schedules, and adjust portions.
*   **Stutter Motor Movement**: Implements alternating cycles (forward/reverse phases) in an attempt to agitate the food and clear minor blockages.
*   **Persistent Scheduler**: Schedules are managed through a dynamic scheduler and saved locally in a JSON configuration file.
*   **Automatic Pin Cleanup**: Shuts down the GPIO pins immediately after rotation is completed to prevent motor overheating and conserve power.
*   **Secure Networking**: Operates within a private Tailscale network to keep the web application private and accessible from mobile devices on the go.
*   **Recent Feedings Log**: Displays a historical record of manual and scheduled feedings.

---

## Hardware Specifications

*   **Controller**: Raspberry Pi
*   **Actuator**: 28BYJ-48 5V Stepper Motor + ULN2003 Driver Board
*   **Wiring Connection**:
    *   IN1 -> GPIO 17 (BCM)
    *   IN2 -> GPIO 18 (BCM)
    *   IN3 -> GPIO 27 (BCM)
    *   IN4 -> GPIO 22 (BCM)
*   **Dispenser Casing**: [Thingiverse 3D Model #3966726](https://www.thingiverse.com/thing:3966726) with a custom-printed extender column.
*   **Power Supply**: External power source recommended for the motor driver to prevent excessive current draw from the Raspberry Pi.

---

## Engineering Notes, Limitations & Lessons Learned

While this project is fully functional as a prototype, several real-world hardware and mechanical limitations were identified during testing:

### 1. Stepper Motor Torque Constraints
The default 28BYJ-48 stepper motor is relatively low-torque. Depending on the size, weight, and shape of the pet food used, the motor will stall or jam frequently when trying to force food through the auger. 

### 2. Software Jam Mitigation (Stutter Logic)
To combat motor stalls, a "stutter" algorithm is implemented in `motor_logic.py`. The motor runs forward for a cycle (e.g., 100 steps) and then briefly reverses (e.g., 20 steps) before resuming. This back-and-forth action helps shake the food loose. While it mitigates some jams, it does not solve severe blockages caused by motor torque limitations.

### 3. 3D Print Tolerances & Roughness
Smoothness and tolerances of the 3D-printed auger screw and the inner casing walls are critical:
*   If the print has rough layer lines or minor surface imperfections, the auger can easily snag or bind against the casing walls.
*   **Solution**: To make this mechanical setup work reliably, you must either print the parts at a very high quality (low layer heights) or manually sand/finish the inner surfaces of the casing and the screw to ensure smooth friction-free contact.

### 4. Design Recommendations for Future Iterations
If rebuilding this feeder, a different approach is recommended:
*   Upgrading to a high-torque NEMA 17 or geared DC motor.
*   Redesigning the dispensing mechanism entirely (e.g., a gravity-fed trapdoor or horizontal conveyor style instead of a vertical/tight-tolerance auger screw).

---

## Setup & Local Installation

### 1. Virtual Environment Setup
Clone the repository and install the dependencies:
```bash
git clone https://github.com/asbaxter/nacho-feeder.git
cd nacho-feeder

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configuration
Copy the environment template and configure your local settings:
```bash
cp .env.template .env
```

### 3. Execution
Run the Flask server:
```bash
python app.py
```
The application will listen on port `5000`. For detailed instructions on setting this up as a background systemd service, see [DEPLOY.md](file:///c:/Users/asbax/Desktop/Projects/nacho-feeder/DEPLOY.md).

---

## License

This project is licensed under the MIT License.
