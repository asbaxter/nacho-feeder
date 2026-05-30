# 🦎 Nacho Feeder

[![Platform](https://img.shields.io/badge/platform-Raspberry%20Pi-red.svg)](https://www.raspberrypi.org/)
[![Language](https://img.shields.io/badge/language-Python%203-blue.svg)](https://www.python.org/)
[![VPN](https://img.shields.io/badge/VPN-Tailscale-orange.svg)](https://tailscale.com/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

An automated pet feeding system built for **Nacho** the lizard (or any small pet!). It combines custom 3D-printed hardware, a Raspberry Pi-driven stepper motor, a modern Flask-based control portal, and secure remote VPN management.

---

## 📸 Overview

The **Nacho Feeder** solves the problem of remote pet feeding. It features a custom 3D-printed enclosure containing a food hopper and a spiral auger screw. A 5V/12V stepper motor rotates the screw, pushing exact portions of food forward and out of the dispenser. 

The software component runs on a Raspberry Pi, exposing a mobile-friendly web app. Using **Tailscale VPN**, the dashboard can be accessed securely from anywhere in the world without exposing open ports to the public internet.

```
                  ┌────────────────────────────────────────┐
                  │            Tailscale VPN               │
                  │       (Secure Mobile Access)           │
                  └───────────────────┬────────────────────┘
                                      │
                                      ▼
┌──────────────────┐       ┌──────────────────┐       ┌──────────────────┐
│  Mobile/Desktop  ├──────►│   Flask Server   ├──────►│   RPi.GPIO Pins  │
│     Browser      │       │     (app.py)     │       │  [17, 18, 27, 22]│
└──────────────────┘       └────────┬─────────┘       └────────┬─────────┘
                                    │                          │
                                    ▼                          ▼
                         ┌────────────────────┐       ┌──────────────────┐
                         │  SQLite/JSON Config│       │  Stepper Motor   │
                         │ (schedule_config)  │       │  (Auger Screw)   │
                         └────────────────────┘       └──────────────────┘
```

---

## ✨ Features

- **📱 Responsive Web Portal**: A beautiful, mobile-friendly interface designed to trigger feedings instantly, adjust schedules, and view logs.
- **🔄 Smart Anti-Jam "Stutter" Algorithm**: Runs the auger screw forward and backward in cycles (e.g., 100 steps forward, 20 steps back) to agitate the food, prevent clogs, and ensure consistent portions.
- **🕒 Dynamic Scheduler**: Setup custom daily feed times that persist across restarts in a lightweight JSON configuration.
- **🔋 Battery & Motor Protection**: Automatically shuts down motor pins immediately after feeding to prevent overheating and save battery/power.
- **🛡️ Secure Remote Access**: Runs behind a private **Tailscale VPN** tunnel, allowing safe remote operation and troubleshooting from your phone, even when away from home.
- **📜 Detailed Feeding Log**: Keeps track of recent automated and manual feedings with visual indicators.

---

## 🛠️ Hardware Stack

- **Controller**: Raspberry Pi (Runs the Python Flask server)
- **Actuator**: 28BYJ-48 5V Stepper Motor (or similar 4-phase stepper motor)
- **Driver Board**: ULN2003 Driver Board (connected to GPIO pins `17`, `18`, `27`, and `22`)
- **Mechanicals**: 
  - 3D-printed hopper/dispenser casing
  - 3D-printed spiral auger screw
- **Power**: External power supply for the motor (highly recommended to avoid drawing too much current from the Raspberry Pi GPIOs)

---

## 💻 Software Stack

- **Backend**: Python 3, Flask, `schedule`
- **Frontend**: Responsive HTML5 + CSS3 Grid/Flexbox
- **Libraries**:
  - `RPi.GPIO` for direct hardware control (with automatic mock fallback for easy local desktop testing)
  - `python-dotenv` for environment management

---

## 🚀 Quick Start

### 1. Hardware Connection (GPIO BCM Mode)

Connect your stepper motor driver to the Raspberry Pi GPIO pins as follows:

| Motor Driver Input | Raspberry Pi GPIO Pin (BCM) |
|--------------------|-----------------------------|
| IN1                | GPIO 17                     |
| IN2                | GPIO 18                     |
| IN3                | GPIO 27                     |
| IN4                | GPIO 22                     |

### 2. Software Installation

Clone the repository to your Raspberry Pi:
```bash
git clone https://github.com/asbaxter/nacho-feeder.git
cd nacho-feeder
```

Set up a virtual environment and install the required dependencies:
```bash
# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Local Configuration

Create a `.env` file from the template:
```bash
cp .env.template .env
```
Fill in the parameters (e.g., if you set up optional camera systems or specific ports).

### 4. Running the Application

To run the server in development mode:
```bash
python app.py
```
The control portal will be live at `http://<your-pi-ip>:5000`.

*For detailed instructions on running this as a permanent background service on system boot, see [DEPLOY.md](file:///c:/Users/asbax/Desktop/Projects/nacho-feeder/DEPLOY.md).*

---

## 🔒 Security & Tailscale VPN Integration

Instead of exposing your home network by port-forwarding port `5000` (which leaves your Raspberry Pi vulnerable to external attacks), Nacho Feeder is designed to work in conjunction with **Tailscale**:

1. Install **Tailscale** on your Raspberry Pi:
   ```bash
   curl -fsSL https://tailscale.com/install.sh | sh
   sudo tailscale up
   ```
2. Install **Tailscale** on your mobile phone or computer.
3. Access your feeder dashboard securely from anywhere using the private Tailscale IP (e.g., `http://100.x.y.z:5000`) or your Tailscale MagicDNS name!

---

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.
