from flask import Flask, render_template_string, request, jsonify
import motor_logic
import datetime
import os

app = Flask(__name__)

# File to store the last feeding time
LOG_FILE = "/home/pi/nacho-feeder/last_fed.txt"

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
            background: #263238; /* Darker background for better contrast */
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
        
        #status { margin-top: 20px; font-weight: bold; color: #78909c; min-height: 24px; }
        #last-fed { 
            font-size: 0.9rem;
            color: #546e7a; 
            margin-top: 15px; 
            border-top: 1px solid #eee; 
            padding-top: 15px; 
        }
    </style>
</head>
<body>
    <div class="card">
        <h1>🦎 Nacho Feeder</h1>
        
        <div class="slider-container">
            <label>Amount (Steps)</label><br>
            <input type="range" id="stepSlider" min="100" max="5000" value="512" oninput="updateLabel(this.value)">
            <div class="val-display" id="stepVal">512</div>
        </div>

        <button class="forward" onclick="move('forward')">🪱 DISPENSE NOW</button>
        <button class="reverse" onclick="move('reverse')">🔄 CLEAR JAM</button>
        
        <p id="status">System Ready</p>
        <div id="last-fed">Last Fed: <b>{{ last_fed }}</b></div>
    </div>

    <script>
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
                document.querySelector('#last-fed b').innerText = data.time;
                setTimeout(() => { status.innerText = "System Ready"; }, 3000);
            })
            .catch(err => { 
                status.innerText = "Error: Connection Lost"; 
                status.style.color = "red";
            });
        }
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    last_fed = "Not yet today"
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r") as f:
            last_fed = f.read()
    return render_template_string(HTML_TEMPLATE, last_fed=last_fed)

@app.route('/move', methods=['POST'])
def move():
    data = request.get_json()
    motor_logic.run_motor(steps=data.get('steps', 512), direction=data.get('direction', 'forward'))
    
    # Update timestamp
    now = datetime.datetime.now().strftime("%I:%M %p (%b %d)")
    with open(LOG_FILE, "w") as f:
        f.write(now)
        
    return jsonify(status="success", time=now)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
