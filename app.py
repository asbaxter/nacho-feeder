from flask import Flask, render_template_string, request, jsonify
import motor_logic
import datetime
import os
import schedule
import time
import threading
import json
app = Flask(__name__)

# Files to store data
LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "last_fed.txt")
SCHEDULE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "schedule_config.json")

# Global variables
current_config = {"time": "10:00", "enabled": True, "steps": 512}  # Default
scheduler_thread = None
motor_thread = None
stop_event = threading.Event()
motor_status = "idle"

def load_history():
    if not os.path.exists(LOG_FILE):
        return []
    with open(LOG_FILE, "r") as f:
        lines = f.readlines()
    return [line.strip() for line in lines[-5:]] # Return last 5

def save_history(timestamp):
    history = load_history()
    history.append(timestamp)
    with open(LOG_FILE, "w") as f:
        f.write("\n".join(history[-5:])) # Keep only last 5
        f.write("\n") # Ensure newline at end

def load_schedule():
    global current_config
    if os.path.exists(SCHEDULE_FILE):
        with open(SCHEDULE_FILE, "r") as f:
            try:
                data = json.load(f)
                # Handle migration or direct load
                if isinstance(data, str): # Old format
                     current_config = {"time": data, "enabled": True, "steps": 512}
                else:
                    current_config = data
                    # Ensure steps exists if loading from older json
                    if "steps" not in current_config:
                        current_config["steps"] = 512
                    if "stutter_fwd" not in current_config:
                        current_config["stutter_fwd"] = 100
                    if "stutter_back" not in current_config:
                        current_config["stutter_back"] = 20
                    if "camera_name" not in current_config:
                        current_config["camera_name"] = ""
            except:
                pass # Use default if error
    return current_config

def save_schedule_config():
    global current_config
    with open(SCHEDULE_FILE, "w") as f:
        json.dump(current_config, f)
    update_scheduler()

def feed_job():
    print(f"Executing scheduled feed at {datetime.datetime.now()}")
    steps = current_config.get("steps", 512)
    motor_logic.run_motor(steps=steps, direction='forward')
    now = datetime.datetime.now().strftime("%I:%M %p (%b %d)")
    save_history(now)

def update_scheduler():
    schedule.clear()
    if current_config['enabled']:
        schedule.every().day.at(current_config['time']).do(feed_job)
        print(f"Scheduler updated: Feeding daily at {current_config['time']}")
    else:
        print("Scheduler updated: Disabled")

def run_scheduler():
    while True:
        schedule.run_pending()
        time.sleep(1)

# Initialize scheduler
load_schedule()
update_scheduler()
scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
scheduler_thread.start()

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Nacho Feeder</title>
    <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1">
    <style>
        * { box-sizing: border-box; }
        body { 
            font-family: 'Segoe UI', sans-serif; 
            margin: 0;
            padding: 0;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            background: #263238; 
        }
        .card { 
            background: white; 
            padding: 25px; 
            border-radius: 25px; 
            box-shadow: 0 15px 35px rgba(0,0,0,0.3); 
            width: 95%; 
            width: 95%; 
            max-width: 800px; /* Wider for desktop */
            text-align: center;
        }
        .main-content {
            display: flex;
            gap: 20px;
            text-align: left;
        }
        @media (max-width: 600px) {
            .main-content {
                flex-direction: column;
            }
        }
        h1 { color: #37474f; margin-bottom: 20px; font-size: 2rem; text-align: center; }
        .slider-container { 
            background: #f1f8e9;
            padding: 15px;
            border-radius: 15px;
            margin: 20px 0; 
        }
        input[type=range] { width: 100%; height: 15px; cursor: pointer; }
        .val-display { font-size: 28px; font-weight: bold; color: #689f38; }
        
        button { 
            padding: 20px; 
            font-size: 18px; 
            margin: 10px 0; 
            width: 100%; 
            cursor: pointer; 
            border-radius: 15px; 
            border: none; 
            font-weight: bold;
            transition: transform 0.1s;
        }
        button:active { transform: scale(0.96); }
        
        .forward { background: #8bc34a; color: white; }
        .reverse { background: #ff7043; color: white; }
        .action-btn { background: #29b6f6; color: white; padding: 10px; margin-top: 5px;}
        
        #status { margin-top: 20px; font-weight: bold; color: #78909c; min-height: 24px; }
        .history-section { 
            font-size: 0.9rem;
            color: #546e7a; 
            margin-top: 15px; 
            border-top: 1px solid #eee; 
            padding-top: 15px; 
            text-align: left;
        }
        .history-list { list-style: none; padding: 0; margin: 10px 0; }
        .history-list li { padding: 5px 0; border-bottom: 1px solid #eee; }
        
        .schedule-container {
            background: #e1f5fe;
            padding: 15px;
            border-radius: 15px;
            margin: 20px 0;
        }
        input[type=time] {
            padding: 10px;
            border-radius: 10px;
            border: 1px solid #ddd;
            font-size: 16px;
        }
    </style>
</head>
<body>
    <div class="card">
        <h1>🦎 Nacho Feeder</h1>
        
        <div class="main-content">
            <!-- Left Column: Controls -->
            <div class="schedule-container" style="background: #fff3e0; border: 1px solid #ffe0b2; flex: 1; margin:0;">
                <h3 style="margin-top:0; color: #ef6c00;">Feeding Controls</h3>
                
                <label>Total Amount (Steps)</label>
                <div style="display: flex; align-items: center;">
                    <input type="range" id="stepSlider" min="100" max="10000" value="{{ config.get('steps', 512) }}" oninput="updateLabel('stepVal', this.value)" style="flex-grow: 1;">
                    <span class="val-display" id="stepVal" style="min-width: 60px; text-align: right; font-size: 1.2rem;">{{ config.get('steps', 512) }}</span>
                </div>

                <div style="margin: 15px 0; border-top: 1px dashed #ccc; padding-top: 10px;">
                    <label class="switch">
                        <input type="checkbox" id="stutterMode" checked onchange="toggleStutterOptions()">
                        Anti-Jam / Stutter Mode
                    </label>
                    
                    <div id="stutterOptions" style="margin-top: 10px;">
                        <label style="font-size: 0.9em;">Forward Cycle:</label>
                        <div style="display: flex; align-items: center;">
                            <input type="range" id="stutterFwd" min="0" max="1000" value="{{ config.get('stutter_fwd', 100) }}" oninput="updateLabel('fwdVal', this.value)" style="flex-grow: 1;">
                            <span style="min-width: 40px; text-align: right; font-weight: bold;" id="fwdVal">{{ config.get('stutter_fwd', 100) }}</span>
                        </div>
                        
                        <label style="font-size: 0.9em;">Reverse Cycle:</label>
                        <div style="display: flex; align-items: center;">
                            <input type="range" id="stutterBack" min="0" max="1000" value="{{ config.get('stutter_back', 20) }}" oninput="updateLabel('backVal', this.value)" style="flex-grow: 1;">
                            <span style="min-width: 40px; text-align: right; font-weight: bold;" id="backVal">{{ config.get('stutter_back', 20) }}</span>
                        </div>
                    </div>
                </div>

                <div id="controls" style="display: flex; gap: 10px;">
                    <button class="forward" id="btnDispense" onclick="move('forward')" style="flex: 1;">🏁 RUN MOTOR</button>
                    <button class="reverse" id="btnStop" onclick="stop()" style="display: none; background: #e53935; flex: 1;">🛑 STOP FEEDING</button>
                </div>
                <p id="status">System Ready</p>
            </div>
            
            <!-- Right Column: Schedule & Logic -->
            <div style="flex: 1; display: flex; flex-direction: column; gap: 20px;">
                <div class="schedule-container" style="margin: 0;">
                    <h3 style="margin-top:0; color: #0277bd;">Daily Schedule</h3>
                    <div style="display: flex; align-items: center; justify-content: center; margin-bottom: 10px;">
                        <label class="switch">
                            <input type="checkbox" id="scheduleEnabled" {% if config.enabled %}checked{% endif %}>
                            Enable
                        </label>
                    </div>
                    <input type="time" id="scheduleTime" value="{{ config.time }}">
                    <button class="action-btn" onclick="updateSchedule()">Save Schedule</button>
                </div>

                <div class="history-section" style="margin:0; border:none; background: #f5f5f5; padding: 10px; border-radius: 15px;">
                     <details>
                        <summary style="cursor: pointer; font-weight: bold; color: #546e7a;">📜 Recent Feedings Log</summary>
                        <ul class="history-list">
                            {% for item in history %}
                            <li>{{ item }}</li>
                            {% else %}
                            <li>No recent feedings</li>
                            {% endfor %}
                        </ul>
                    </details>
                </div>
            </div>
        </div>

    <script>
        function updateLabel(id, val) { document.getElementById(id).innerText = val; }

        function toggleStutterOptions() {
            const enabled = document.getElementById('stutterMode').checked;
            document.getElementById('stutterOptions').style.display = enabled ? 'block' : 'none';
        }

        function move(dir) {
            const steps = document.getElementById('stepSlider').value;
            const stutter = document.getElementById('stutterMode').checked;
            const cycle_fwd = document.getElementById('stutterFwd').value;
            const cycle_back = document.getElementById('stutterBack').value;
            
            const status = document.getElementById('status');
            status.innerText = "Starting...";
            
            fetch('/move', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    direction: dir, 
                    steps: parseInt(steps), 
                    stutter: stutter,
                    cycle_fwd: parseInt(cycle_fwd),
                    cycle_back: parseInt(cycle_back)
                })
            })
            .then(res => res.json())
            .then(data => {
                if(data.status === "started") {
                    monitorStatus();
                } else {
                    status.innerText = data.message || "Error";
                }
            });
        }
        
        function stop() {
            fetch('/stop', {method: 'POST'});
        }

        function monitorStatus() {
            const btnDispense = document.getElementById('btnDispense');
            const btnStop = document.getElementById('btnStop');
            const status = document.getElementById('status');
            
            btnDispense.style.display = 'none';
            btnStop.style.display = 'block';
            status.innerText = "Feeding in progress...";
            status.style.color = "#ff9800";
            
            const interval = setInterval(() => {
                fetch('/status')
                .then(res => res.json())
                .then(data => {
                    if (data.status === 'idle') {
                        clearInterval(interval);
                        status.innerText = "Feeding Complete ✨";
                        status.style.color = "#689f38";
                        btnDispense.style.display = 'block';
                        btnStop.style.display = 'none';
                        setTimeout(() => location.reload(), 1500);
                    }
                });
            }, 1000);
        }
        
        function updateSchedule() {
            const time = document.getElementById('scheduleTime').value;
            const enabled = document.getElementById('scheduleEnabled').checked;
            const status = document.getElementById('status');
            status.innerText = "Updating schedule...";
            
            fetch('/set_schedule', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({time: time, enabled: enabled})
            })
            .then(res => res.json())
            .then(data => {
                status.innerText = "Schedule Saved! 🕒";
                setTimeout(() => { status.innerText = "System Ready"; }, 2000);
            });
        }
        
        // Initial setup
        toggleStutterOptions();
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    history = load_history()
    # Reverse to show newest first
    return render_template_string(HTML_TEMPLATE, history=reversed(history), config=current_config)

def run_motor_thread(steps, direction, stutter, cycle_fwd, cycle_back):
    global motor_status
    motor_status = "running"
    stop_event.clear()
    
    try:
        motor_logic.run_motor(
            steps=steps, 
            direction=direction, 
            stutter=stutter, 
            cycle_fwd=cycle_fwd, 
            cycle_back=cycle_back,
            stop_event=stop_event
        )
        # Update timestamp only if not stopped? Or always?
        # Let's record it even if stopped partial
        now = datetime.datetime.now().strftime("%I:%M %p (%b %d)")
        save_history(now)
    except Exception as e:
        print(f"Motor error: {e}")
    finally:
        motor_status = "idle"

@app.route('/move', methods=['POST'])
def move():
    global motor_thread
    
    if motor_status == "running":
        return jsonify(status="error", message="Motor already running")

    data = request.get_json()
    steps = int(data.get('steps', 512))
    direction = data.get('direction', 'forward')
    stutter = data.get('stutter', False)
    cycle_fwd = int(data.get('cycle_fwd', 100))
    cycle_back = int(data.get('cycle_back', 20))
    
    # Persist config
    if direction == 'forward':
        current_config['steps'] = steps
        current_config['stutter_fwd'] = cycle_fwd
        current_config['stutter_back'] = cycle_back
        save_schedule_config()
    
    motor_thread = threading.Thread(
        target=run_motor_thread, 
        args=(steps, direction, stutter, cycle_fwd, cycle_back)
    )
    motor_thread.start()
        
    return jsonify(status="started")

@app.route('/stop', methods=['POST'])
def stop_motor():
    stop_event.set()
    return jsonify(status="stopping")

@app.route('/status')
def get_status():
    return jsonify(status=motor_status)

@app.route('/set_schedule', methods=['POST'])
def set_schedule():
    data = request.get_json()
    new_time = data.get('time')
    enabled = data.get('enabled', True)
    camera_name = data.get('camera_name')
    
    # Update whatever keys are present
    if new_time: current_config['time'] = new_time
    if 'enabled' in data: current_config['enabled'] = enabled
    
    save_schedule_config()
    return jsonify(status="success", config=current_config)



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
