# Nacho Feeder Deployment Guide

Follow these steps to update your Raspberry Pi with the latest changes.

## 1. Connect to your Pi
SSH into your Raspberry Pi:
```bash
ssh pi@<your-pi-ip>
```

## 2. Update the Code
Navigate to your project directory and pull the latest changes from GitHub:
```bash
cd nacho-feeder
git pull origin main
```

## 3. Install/Update Dependencies
One of the changes we made was adding the `schedule` library. We need to install it on the Pi.
```bash
# If you are using a virtual environment (recommended):
source .venv/bin/activate
pip install -r requirements.txt

# OR if you are installing globally:
pip3 install -r requirements.txt
```
*Note: This will also ensure `RPi.GPIO` is installed since you uncommented it in requirements.txt.*

## 4. Restarting the Application

### Option A: If you run it manually
If you usually just run `python app.py`, you'll need to stop the current one (Ctrl+C) and start it again:
```bash
python3 app.py
```
*Tip: Use `nohup` to keep it running after you disconnect:*
```bash
nohup python3 app.py &
```

### Option B: If you use Systemd (Recommended)
If you want the feeder to start automatically when the Pi turns on, you should use a systemd service.

1. **Create a service file**:
   ```bash
   sudo nano /etc/systemd/system/nacho-feeder.service
   ```

2. **Paste the following** (adjust paths if your project is somewhere else):
   ```ini
   [Unit]
   Description=Nacho Feeder Web Server
   After=network.target

   [Service]
   User=pi
   WorkingDirectory=/home/pi/nacho-feeder
   ExecStart=/usr/bin/python3 /home/pi/nacho-feeder/app.py
   Restart=always

   [Install]
   WantedBy=multi-user.target
   ```

3. **Enable and Start**:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable nacho-feeder
   sudo systemctl start nacho-feeder
   ```

## 5. Setting up the Camera (Optional)
If you want to use the Wyze Camera feed, you'll need to run the bridge service.

1.  **Install Docker**:
    ```bash
    curl -sSL https://get.docker.com | sh
    sudo usermod -aG docker pi
    sudo apt-get install -y libffi-dev libssl-dev
    sudo apt install -y python3-dev
    sudo apt-get install -y python3 pip
    sudo pip3 install docker-compose
    ```

2.  **Configure Credentials**:
    Copy the template and edit it with your Wyze email/password and API Key.
    *Note: Even with an API Key, the bridge typically requires your email and password to log in initially.*
    ```bash
    cp .env.template .env
    nano .env
    ```

3.  **Start the Bridge**:
    ```bash
    docker-compose up -d
    ```
    *Wait about 30 seconds for it to login and start the stream.*

4.  **Connect in App**:
    - Go to the Wyze Bridge WebUI: `http://<pi-ip>:8888`
    - Find the "name" of your camera (e.g., `porch-cam`).
    - Go to your Nacho Feeder app.
    - Enter `porch-cam` in the "Camera Name" box and click Update.

## 6. To Update later
   Just run:
   ```bash
   git pull origin main
   sudo systemctl restart nacho-feeder
   # If you updated docker config:
   docker-compose pull
   docker-compose up -d
   ```
