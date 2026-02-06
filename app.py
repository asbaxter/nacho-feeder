from flask import Flask, render_template_string, request, jsonify
import motor_logic
import datetime
import os
import schedule
import time
import threading
import json
from dotenv import load_dotenv
import requests

# Load environment variables
load_dotenv()

# Try to import wyze_sdk, but don't fail if missing (local dev without sdk)
try:
    from wyze_sdk import Client
    from wyze_sdk.errors import WyzeApiError
    WYZE_SDK_AVAILABLE = True
except ImportError:
    WYZE_SDK_AVAILABLE = False
    print("Wyze SDK not found. Camera features will be disabled.")

app = Flask(__name__)

# Files to store data
LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "last_fed.txt")
SCHEDULE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "schedule_config.json")

# Global variables
current_config = {"time": "10:00", "enabled": True, "steps": 512, "camera_name": ""}  # Default
scheduler_thread = None
wyze_client = None
last_snapshot_url = None

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
            max-width: 400px;
            text-align: center;
        }
        h1 { color: #37474f; margin-bottom: 10px; font-size: 1.8rem; }
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
        
        <div class="slider-container">
            <label>Amount (Steps)</label><br>
            <input type="range" id="stepSlider" min="100" max="800" value="{{ config.get('steps', 512) }}" oninput="updateLabel(this.value)">
            <div class="val-display" id="stepVal">{{ config.get('steps', 512) }}</div>
        </div>

        <button class="forward" onclick="move('forward')">🪱 DISPENSE NOW</button>
        <button class="reverse" onclick="move('reverse')">🔄 CLEAR JAM</button>
        
        <div class="schedule-container">
            <label>Daily Schedule</label><br>
            <div style="display: flex; align-items: center; justify-content: center; margin-bottom: 10px;">
                <label class="switch">
                    <input type="checkbox" id="scheduleEnabled" {% if config.enabled %}checked{% endif %}>
                    Enable
                </label>
            </div>
            <input type="time" id="scheduleTime" value="{{ config.time }}">
            <button class="action-btn" onclick="updateSchedule()">Update Schedule</button>
        </div>
        
        <div class="schedule-container" style="background: #e0f2f1;">
            <label>📷 Camera Snapshot</label><br>
            <input type="text" id="cameraName" placeholder="Camera Name (e.g. Porch)" value="{{ config.get('camera_name', '') }}" style="width: 100%; margin-bottom: 10px; padding: 10px; border-radius: 10px; border: 1px solid #ddd;">
            <button class="action-btn" onclick="updateCamera()">Update Camera</button>
            
            <div id="video-container" style="margin-top: 15px; background: black; border-radius: 15px; overflow: hidden; display: {% if config.get('camera_name') %}block{% else %}none{% endif %}; text-align: center;">
                <img id="cam-snapshot" src="" style="width: 100%; display: none;" alt="Loading snapshot...">
                <div id="cam-loader" style="padding: 20px; color: white;">Loading...</div>
            </div>
             <p id="cam-status" style="font-size: 0.8rem; margin-top: 5px; color: #546e7a;">
                {% if not config.get('camera_name') %}Enter your camera name enable snapshots.{% endif %}
            </p>
        </div>

        <p id="status">System Ready</p>
        
        <div class="history-section">
            <b>Recent Feedings:</b>
            <ul class="history-list">
                {% for item in history %}
                <li>{{ item }}</li>
                {% else %}
                <li>No recent feedings</li>
                {% endfor %}
            </ul>
        </div>
    </div>

    <script>
        // Refresh snapshot loop
        let snapshotInterval = null;

        {% if config.get('camera_name') %}
        window.addEventListener('load', function() {
            startSnapshotLoop();
        });
        {% endif %}

        function startSnapshotLoop() {
            refreshSnapshot();
            // Refresh every 10 seconds
            snapshotInterval = setInterval(refreshSnapshot, 10000);
        }

        function refreshSnapshot() {
            fetch('/camera/snapshot')
                .then(res => res.json())
                .then(data => {
                    const img = document.getElementById('cam-snapshot');
                    const loader = document.getElementById('cam-loader');
                    
                    if (data.url) {
                        img.src = data.url; // The URL from Wyze is usually a directly accessible S3 link
                        img.onload = () => {
                            img.style.display = 'block';
                            loader.style.display = 'none';
                        };
                    } else {
                        console.log("No snapshot url:", data.error);
                    }
                })
                .catch(err => console.error("Snapshot error:", err));
        }

        function updateLabel(val) { document.getElementById('stepVal').innerText = val; }

        function move(dir) {
            const steps = document.getElementById('stepSlider').value;
            const status = document.getElementById('status');
            status.innerText = "Sending command...";
            
            fetch('/move', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({direction: dir, steps: parseInt(steps)})
            })
            .then(res => res.json())
            .then(data => {
                status.innerText = "Success! ✨";
                setTimeout(() => { location.reload(); }, 1000); 
            })
            .catch(err => { 
                status.innerText = "Error: Connection Lost"; 
                status.style.color = "red";
            });
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
        
        function updateCamera() {
            const name = document.getElementById('cameraName').value;
            const status = document.getElementById('status');
            status.innerText = "Saving camera...";
            
            fetch('/set_schedule', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({camera_name: name})
            })
            .then(res => res.json())
            .then(data => {
                status.innerText = "Camera Saved! 📹";
                setTimeout(() => { location.reload(); }, 1000);
            });
        }
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    history = load_history()
    # Reverse to show newest first
    return render_template_string(HTML_TEMPLATE, history=reversed(history), config=current_config)

@app.route('/move', methods=['POST'])
def move():
    data = request.get_json()
    steps = int(data.get('steps', 512))
    direction = data.get('direction', 'forward')
    
    motor_logic.run_motor(steps=steps, direction=direction)
    
    # Update timestamp
    now = datetime.datetime.now().strftime("%I:%M %p (%b %d)")
    save_history(now)

    # Persist the steps used if moving forward (feeding)
    if direction == 'forward':
        current_config['steps'] = steps
        save_schedule_config()
        
    return jsonify(status="success", time=now)

@app.route('/set_schedule', methods=['POST'])
def set_schedule():
    data = request.get_json()
    new_time = data.get('time')
    enabled = data.get('enabled', True)
    camera_name = data.get('camera_name')
    
    # Update whatever keys are present
    if new_time: current_config['time'] = new_time
    if 'enabled' in data: current_config['enabled'] = enabled
    if 'camera_name' in data: current_config['camera_name'] = camera_name.strip()
    
    save_schedule_config()
    return jsonify(status="success", config=current_config)

@app.route('/camera/snapshot')
def get_snapshot():
    global wyze_client, last_snapshot_url
    
    if not WYZE_SDK_AVAILABLE:
        return jsonify(error="SDK not installed"), 503
        
    camera_name = current_config.get('camera_name')
    if not camera_name:
        return jsonify(error="No camera configured"), 400

    try:
        # Initialize client if needed
        if not wyze_client:
            wyze_client = Client(
                email=os.getenv('WYZE_EMAIL'),
                password=os.getenv('WYZE_PASSWORD'),
                key_id=os.getenv('API_ID'),
                api_key=os.getenv('API_KEY')
            )
        
        # Find the camera
        cameras = wyze_client.cameras.list()
        target_cam = next((c for c in cameras if str(c.nickname).lower() == camera_name.lower()), None)
        
        if not target_cam:
            return jsonify(error="Camera not found"), 404
            
        # Get the latest thumbnail URL
        # Note: forcing a new snapshot is complex/slow, so we usually get the latest event thumbnail
        # For a true live snapshot we'd need to assume the camera is updating it or use specific commands
        return jsonify(url=target_cam.thumbnail_url)
        
    except Exception as e:
        print(f"Wyze Error: {e}")
        # Invalid client? try resetting
        wyze_client = None
        return jsonify(error=str(e)), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
