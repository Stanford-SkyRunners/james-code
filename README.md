# james-code - Raspberry Pi Autonomous System

Complete setup guide for running the james-code system on Raspberry Pi. Follow this guide top-to-bottom to get everything working.

## What This Does

Your Raspberry Pi will:
- ✅ Auto-connect to your backend server on boot
- ✅ Register with persistent UUID-based device ID
- ✅ Receive waypoints in real-time via WebSocket
- ✅ Send status emails every 5 minutes with system metrics
- ✅ Send immediate email notification on WiFi connection
- ✅ Monitor backend connection (WebSocket + REST API)
- ✅ Auto-reconnect if connection drops
- ✅ Send periodic heartbeat messages to server
- ✅ Support AprilTag detection for computer vision (optional)

## Prerequisites

Before you begin, make sure you have:

- Raspberry Pi (tested on Raspberry Pi 4)
- Raspberry Pi OS installed
- Internet connection (WiFi or Ethernet)
- Gmail account with App Password ([setup instructions](#gmail-app-password-setup))
- Backend server running and accessible (ports 8000 and 8001)

## 📁 Project Structure

```
~/james-code/
├── .env                             # Email credentials (you'll create this)
├── .env.example                     # Template for .env file
├── config.json                      # Main configuration (backend URLs, SMTP, device info)
├── .device_id                       # Auto-generated persistent device ID (gitignored)
├── websocket_status.json            # Auto-generated connection status
├── status_monitor.log               # Auto-generated log file
│
├── backend-client/                  # WebSocket client
│   ├── websocket_client.py          # Connects to backend, receives waypoints
│   ├── device_manager.py            # Device ID and metadata management
│   ├── requirements.txt             # Python dependencies
│   └── setup-websocket-service.sh   # Setup script (auto-generates systemd service)
│
├── status-scripts/                  # Status monitoring
│   ├── status_monitor.py            # Monitors system + sends email updates
│   └── setup-status-monitor.sh      # Setup script (auto-generates systemd service)
│
└── apriltag/                        # AprilTag detection (optional)
    ├── detect_apriltags.py
    └── README.md
```

> **Note:** This repository is portable! You can clone it to any location. The setup scripts automatically detect paths and generate service files with correct absolute paths for your system.

---

## Step 1: Clone Repository

Clone or copy the repository to your Raspberry Pi:

```bash
cd ~
git clone <your-repository-url> james-code
cd james-code
```

Or copy from another system:
```bash
scp -r james-code/ pi@<raspberry-pi-ip>:~/
```

---

## Step 2: Configure Your Device

### 2.1 Create Configuration File

Copy the example configuration file and customize it for your device:

```bash
cp config.example.json config.json
nano config.json
```

**IMPORTANT:** You must customize these fields in `config.json`:

```json
{
  "backend": {
    "websocket_url": "ws://YOUR_BACKEND_IP:8000/ws",
    "rest_api_url": "http://YOUR_BACKEND_IP:8000"
  },
  "device": {
    "name": "My Raspberry Pi",        # ← CHANGE THIS to a meaningful name
    "location": "Your Location",       # ← CHANGE THIS to actual location
    "metadata": {
      "description": "Your device description",  # ← CHANGE THIS
      "owner": "Your Name"                        # ← CHANGE THIS
    }
  }
}
```

**What happens if you don't change these:**
- `name`: Defaults to `"Raspberry Pi (hostname)"` - not very useful when you have multiple devices
- `location`: Defaults to `"Unknown"` - you won't know where your device is
- `metadata.owner` and `metadata.description`: Will be empty - no info about who owns it or what it's for

**Example customization:**
```json
{
  "device": {
    "name": "Kitchen Navigation Pi",
    "location": "Building A - Kitchen - Counter 3",
    "metadata": {
      "description": "Autonomous navigation testing unit",
      "owner": "James",
      "department": "Robotics Lab",
      "install_date": "2025-11-17"
    }
  }
}
```

### 2.2 Configure Environment Variables

Create your `.env` file from the template:

```bash
cp .env.example .env
nano .env
```

Update with your email settings:

```bash
# Email configuration for status notifications
EMAIL_PASSWORD=your-16-char-app-password
EMAIL_FROM_ADDRESS=your-email@gmail.com
EMAIL_TO_ADDRESS=your-email@gmail.com
```

### 2.3 Gmail App Password Setup

1. Go to https://myaccount.google.com/
2. Navigate to **Security** → **2-Step Verification** (enable if not already)
3. Go back, and in the search bar, enter: **App Passwords** → **Generate new**
4. Select "Mail" and "Other (Custom name)"
5. Copy the 16-character password (no spaces)
6. Paste into `.env` as `EMAIL_PASSWORD`

**For other email providers:**
- Outlook: Update `smtp_server` in `config.json` to `smtp.office365.com`, port `587`
- Yahoo: Update `smtp_server` in `config.json` to `smtp.mail.yahoo.com`, port `587`

---

## Step 3: Install Python Dependencies

Install required Python packages:

```bash
# Install via pip3 (if using virtual environment)
pip3 install websockets aiohttp gpiozero python-dotenv netifaces --break-system-packages

# Or install system packages (recommended for Raspberry Pi OS)
sudo apt install -y python3-websockets python3-aiohttp python3-gpiozero python3-dotenv python3-netifaces
```

> **Note:** The `--break-system-packages` flag is required on modern Raspberry Pi OS if using pip3 directly. Using `sudo apt install` is recommended for system-wide installation.

Verify installation:
```bash
python3 -c "import websockets, aiohttp, dotenv, netifaces; print('✅ Dependencies installed')"
```

---

## Step 4: Install WebSocket Client Service

Run the setup script:

```bash
cd ~/james-code/backend-client
sudo ./setup-websocket-service.sh
```

You should see:
```
==========================================
Vantir WebSocket Client Service Setup
==========================================

📦 Installing Python dependencies...
🔧 Making Python script executable...
📋 Generating systemd service file...
🔄 Reloading systemd...
✅ Enabling service to start on boot...
🚀 Starting service...

==========================================
✅ Setup Complete!
==========================================
```

### Verify WebSocket Client

Check service status:
```bash
sudo systemctl status vantir-websocket-client.service
```

View live logs:
```bash
sudo journalctl -u vantir-websocket-client.service -f
```

You should see:
```
✓ Created new device ID: pi-abc123...
📡 MAC address from eth0: xx:xx:xx:xx:xx:xx
✓ Backend health check passed
🔌 Connected to WebSocket: ws://YOUR_SERVER_IP:8001
📤 Sent registration as: pi-abc123... (James Pi)
✅ Registration confirmed by server!
💓 Heartbeat task started (interval: 30s)
```

Press Ctrl+C to exit logs.

**Note:** The device ID is automatically generated on first run and persisted in `.device_id` file. This ID remains constant across reboots and reinstalls.

---

## Step 5: Install Status Monitor Service

Run the setup script:

```bash
cd ~/james-code/status-scripts
./setup-status-monitor.sh
```

### Verify Status Monitor

Check service status:
```bash
sudo systemctl status status-monitor.service
```

View live logs:
```bash
sudo journalctl -u status-monitor.service -f
```

You should see it waiting for network, then connecting and sending the first email.

---

## Step 6: Test Your Setup

### 6.1 Check WebSocket Connection

View connection status:
```bash
cat ~/james-code/websocket_status.json
```

Should show:
```json
{
  "connected": true,
  "last_update": "2025-10-24T...",
  "last_message": "connection",
  "error": null
}
```

### 6.2 Test REST API Connection

```bash
# Health check
curl http://YOUR_SERVER_IP:8000/health

# Should return:
# {"status":"healthy","timestamp":"...","uptime":...}

# Get waypoints
curl http://YOUR_SERVER_IP:8000/api/points
```

### 6.3 Check Email Notifications

Within 1-2 minutes of starting the status monitor, you should receive an email like:

```
Subject: 🟢 Raspberry Pi Connected to WiFi: YourNetwork

Connection Details:
-------------------
• Network (SSID): YourNetwork
• IP Address: 192.168.1.100
• Signal Strength: -45 dBm

Backend Connection:
-------------------
• WebSocket: ✅ Connected
• REST API: ✅ Connected
• Last Update: 2025-10-24T00:15:31
• Last Message: connection

Status monitoring is now active. You will receive status updates every 5 minutes.
```

### 6.4 Test Waypoint Reception

1. Open your frontend application
2. Create a new waypoint on the map
3. Check Raspberry Pi logs:

```bash
sudo journalctl -u vantir-websocket-client.service -n 20
```

You should see:
```
[2025-10-24 00:22:37] Received: waypoint_created
📍 NEW WAYPOINT CREATED
   ID: point_...
   Coordinates: [lat, lng]
   Timestamp: ...
```

---

## Step 7: Reboot Test

Test that everything auto-starts on boot:

```bash
sudo reboot
```

After reboot (wait 2-3 minutes):

1. ✅ Check your email - you should receive a WiFi connection notification
2. ✅ Verify services are running:
   ```bash
   sudo systemctl status vantir-websocket-client.service
   sudo systemctl status status-monitor.service
   ```
3. ✅ Check connection status:
   ```bash
   cat ~/james-code/websocket_status.json
   ```

---

## ✅ Setup Complete!

Your Raspberry Pi is now fully configured and will:
- Auto-start both services on boot
- Connect to backend automatically
- Receive waypoints in real-time
- Send status emails every 5 minutes
- Auto-reconnect if connection drops
- Monitor system health continuously

---

## Service Management

### WebSocket Client Commands

```bash
# Check status
sudo systemctl status vantir-websocket-client.service

# View live logs
sudo journalctl -u vantir-websocket-client.service -f

# View recent logs
sudo journalctl -u vantir-websocket-client.service -n 50

# Restart
sudo systemctl restart vantir-websocket-client.service

# Stop
sudo systemctl stop vantir-websocket-client.service

# Disable auto-start
sudo systemctl disable vantir-websocket-client.service
```

### Status Monitor Commands

```bash
# Check status
sudo systemctl status status-monitor.service

# View live logs
sudo journalctl -u status-monitor.service -f

# Restart (triggers immediate email)
sudo systemctl restart status-monitor.service

# Stop
sudo systemctl stop status-monitor.service

# View log file
tail -f ~/james-code/status_monitor.log
```

### Quick Status Check

```bash
# Check both services at once
systemctl is-active vantir-websocket-client.service status-monitor.service

# Check connection status file
cat ~/james-code/websocket_status.json

# Watch connection status in real-time
watch -n 1 cat ~/james-code/websocket_status.json
```

---

## Backend API Reference

Your backend server provides these endpoints:

### REST API (Port 8000)
- `GET /health` - Health check
- `GET /api/points` - Get all waypoints
- `POST /api/points` - Create waypoint
- `POST /api/points/:id/launch` - Launch waypoint
- `DELETE /api/points/:id` - Delete waypoint

### WebSocket (Port 8001)

**Messages FROM Pi → Server:**
- `register` - Device registration with UUID, MAC address, metadata
- `heartbeat` - Periodic heartbeat (every 30s)
- `pong` - Response to ping
- `launch_confirmation` - Acknowledgment of waypoint launch command

**Messages FROM Server → Pi:**
- `registration_confirmed` - Confirms device registration
- `connection` - Connection acknowledgment with client ID
- `waypoint_created` - New waypoint created
- `waypoint_launch` - Launch command issued
- `send_test_email` - Test email trigger (LED + email)
- `ping` - Request for pong response
- `client_joined` - Another client connected
- `client_left` - Another client disconnected

---

## Device ID Management

Each Raspberry Pi is assigned a persistent, unique device ID on first run. This ID:
- **Persists across reboots** - Same ID after restart
- **Survives reinstalls** - Stored in `.device_id` file (gitignored)
- **Format**: `pi-{uuid}` (e.g., `pi-deb488ff-f491-45ad-9988-4a2dbcf69736`)
- **Includes metadata**: Device name, location, MAC address, custom fields

### View Device Information

```bash
# View device ID file
cat ~/james-code/.device_id

# Test device manager
cd ~/james-code/backend-client
python3 device_manager.py
```

Output example:
```json
{
  "deviceId": "pi-deb488ff-f491-45ad-9988-4a2dbcf69736",
  "name": "James Pi",
  "hostname": "jamesraspberrypi",
  "deviceType": "raspberry_pi",
  "macAddress": "d8:3a:dd:26:bf:21",
  "location": "Development Lab",
  "metadata": {
    "description": "Development Raspberry Pi for testing",
    "owner": "James"
  }
}
```

### Customize Device Information

Edit `config.json` to customize device metadata:

```json
{
  "device": {
    "name": "Kitchen Pi",
    "location": "Building A - Kitchen",
    "metadata": {
      "room": "Kitchen",
      "floor": "1",
      "purpose": "Navigation testing"
    }
  }
}
```

Then restart the service:
```bash
sudo systemctl restart vantir-websocket-client.service
```

### Reset Device ID

To generate a new device ID (e.g., when moving SD card to different Pi):

```bash
rm ~/james-code/.device_id
sudo systemctl restart vantir-websocket-client.service
```

A new device ID will be automatically generated on next connection.

### Registration Flow

When the Pi connects to the server:

1. **Device ID Generation/Loading**
   - Checks for existing `.device_id` file
   - If not found, generates new UUID-based ID
   - Saves to `.device_id` for persistence

2. **MAC Address Detection**
   - Attempts to detect MAC address from `eth0` or `wlan0`
   - Used as backup identifier

3. **Metadata Loading**
   - Loads device name, location from `config.json`
   - Merges with custom metadata fields

4. **Registration Message**
   - Sends complete device info to server
   - Format: `{"type": "register", "deviceId": "...", ...}`

5. **Confirmation**
   - Waits up to 10 seconds for `registration_confirmed` response
   - Logs warning if timeout, but continues operation

6. **Heartbeat Start**
   - Begins sending heartbeat every 30 seconds
   - Format: `{"type": "heartbeat", "deviceId": "...", "timestamp": "..."}`

---

## Troubleshooting

### WebSocket Not Connecting

**Check logs:**
```bash
sudo journalctl -u vantir-websocket-client.service -n 50
```

**Common issues:**
- ❌ Wrong IP address in `config.json`
- ❌ Backend server not running
- ❌ Firewall blocking ports 8000 or 8001
- ❌ Wrong port numbers (should be 8001 for WebSocket, 8000 for REST)

**Test connectivity:**
```bash
# Ping server
ping YOUR_SERVER_IP

# Test REST API
curl http://YOUR_SERVER_IP:8000/health

# Test network connectivity
curl -I http://google.com
```

---

### Emails Not Sending

**Check logs:**
```bash
sudo journalctl -u status-monitor.service -n 50 | grep -i error
```

**Common issues:**
- ❌ Wrong Gmail app password in `config.json`
- ❌ 2-Step Verification not enabled on Gmail
- ❌ Email address typo in config
- ❌ SMTP server blocked by network/firewall

**Test manually:**
```bash
# Stop service
sudo systemctl stop status-monitor.service

# Run manually to see detailed output
python3 ~/james-code/status-scripts/status_monitor.py

# Ctrl+C to stop, then restart service
sudo systemctl start status-monitor.service
```

---

### Services Not Starting on Boot

**Check if services are enabled:**
```bash
sudo systemctl is-enabled vantir-websocket-client.service
sudo systemctl is-enabled status-monitor.service
```

**Enable if needed:**
```bash
sudo systemctl enable vantir-websocket-client.service
sudo systemctl enable status-monitor.service
```

**Check boot logs:**
```bash
sudo journalctl -b | grep vantir
sudo journalctl -b | grep status-monitor
```

---

### Connection Keeps Dropping

The WebSocket client has automatic reconnection with exponential backoff:
- First retry: 5 seconds
- Second retry: 10 seconds
- Third retry: 20 seconds
- Fourth retry: 40 seconds
- Fifth+ retries: 60 seconds (continues forever)

**Check for:**
- Network instability
- Backend server restarting
- Firewall issues
- WiFi signal strength (check status emails)

---

### Python Dependencies Missing

**Reinstall packages:**
```bash
pip3 install websockets aiohttp gpiozero python-dotenv --break-system-packages --force-reinstall
```

**Verify installation:**
```bash
python3 -c "import websockets; print('websockets OK')"
python3 -c "import aiohttp; print('aiohttp OK')"
python3 -c "import gpiozero; print('gpiozero OK')"
python3 -c "import dotenv; print('python-dotenv OK')"
```

---

## Customization

### Change Email Frequency

Edit `status_monitor.py` (line ~347):

```python
interval = 300  # 5 minutes = 300 seconds
```

Change to desired interval:
- 1 minute = 60
- 10 minutes = 600
- 30 minutes = 1800
- 1 hour = 3600

Then restart:
```bash
sudo systemctl restart status-monitor.service
```

### Add Custom Waypoint Handling

Edit `backend-client/websocket_client.py` in the `handle_message` method:

```python
elif msg_type == 'waypoint_launch':
    waypoint_id = data.get('waypointId')
    launch_data = data.get('data', {})

    # Add your custom logic here
    print(f"🚀 Launching to waypoint {waypoint_id}")
    # Example: Start motors, navigate, etc.
```

After editing, restart the service:
```bash
sudo systemctl restart vantir-websocket-client.service
```

### LED Control

To enable LED control for visual feedback, edit `config.json`:

```json
{
  "led": {
    "enabled": true,
    "gpio_pin": 17,
    "blink_duration": 3
  }
}
```

The LED will turn on when:
- Test email command is received
- You can trigger it from the frontend

Wire the LED:
- GPIO Pin 17 → LED anode (long leg)
- LED cathode (short leg) → 220Ω resistor → Ground

---

## File Locations

```
~/james-code/
├── .env                             # Email credentials (you create this)
├── .env.example                     # Template for .env file
├── config.json                      # Main configuration (backend URLs, SMTP, device info)
├── .device_id                       # Auto-generated persistent device ID (gitignored)
├── websocket_status.json            # Auto-generated status file
├── status_monitor.log               # Auto-generated log file
│
├── backend-client/
│   ├── websocket_client.py          # WebSocket client
│   ├── device_manager.py            # Device ID and metadata management
│   ├── requirements.txt             # Python dependencies
│   └── setup-websocket-service.sh   # Setup script
│
├── status-scripts/
│   ├── status_monitor.py            # Status monitor
│   └── setup-status-monitor.sh      # Setup script
│
└── apriltag/
    ├── detect_apriltags.py
    └── README.md
```

**Systemd service files** (auto-generated during setup):
- `/etc/systemd/system/vantir-websocket-client.service`
- `/etc/systemd/system/status-monitor.service`

---

## AprilTag Detection (Optional)

For computer vision and AprilTag detection, see:
- [apriltag/README.md](apriltag/README.md)

---

## System Architecture

```
┌─────────────────────────────────────────────┐
│         Raspberry Pi (james-code)           │
├─────────────────────────────────────────────┤
│                                             │
│  ┌──────────────────────────────────────┐  │
│  │   WebSocket Client Service           │  │
│  │   - Connects to port 8001            │  │
│  │   - Receives waypoints in real-time  │  │
│  │   - Auto-reconnects on failure       │  │
│  │   - Updates websocket_status.json    │  │
│  └──────────────────────────────────────┘  │
│                  │                          │
│                  │                          │
│                  ▼                          │
│  ┌──────────────────────────────────────┐  │
│  │   Status Monitor Service             │  │
│  │   - Reads websocket_status.json      │  │
│  │   - Collects system metrics          │  │
│  │   - Sends emails every 5 minutes     │  │
│  │   - Monitors backend connection      │  │
│  └──────────────────────────────────────┘  │
│                                             │
└─────────────────────────────────────────────┘
                    │
                    ▼
        ┌───────────────────────┐
        │   Backend Server      │
        ├───────────────────────┤
        │  REST API (Port 8000) │
        │  WebSocket (Port 8001)│
        └───────────────────────┘
```

---

## What Happens Automatically

### On Boot
1. System boots and network connects
2. **Status Monitor** starts, waits for WiFi
3. **WebSocket Client** starts
4. Device ID loaded (or generated if first run)
5. MAC address detected
6. Connects to backend WebSocket
7. Sends device registration message
8. Waits for registration confirmation
9. Starts heartbeat task
10. Email sent with connection notification
11. Both services run continuously

### Every 5 Minutes
1. Status monitor collects system metrics
2. Checks backend connection (WebSocket + REST API)
3. Formats and sends status email

### When Waypoint Created
1. Frontend creates waypoint
2. Backend sends WebSocket message
3. Pi receives `waypoint_created` event
4. Event logged to journalctl
5. Status file updated

### If Connection Lost
1. WebSocket client detects disconnect
2. Waits 5 seconds, tries to reconnect
3. If fails, exponential backoff (5s → 10s → 20s → 40s → 60s max)
4. Keeps trying forever until reconnected
5. Status file updated with error
6. Next status email reports disconnection

---

## 📹 Live Video Streaming with WebRTC (Optional)

Stream live video from your Raspberry Pi camera to your web frontend with ultra-low latency using WebRTC!

### Features

- ✅ **Ultra-Low Latency**: 100-300ms end-to-end delay (feels like live TV!)
- ✅ **High Quality**: Configurable resolution up to 1080p @ 30fps
- ✅ **Multiple Viewers**: Support 2-5+ simultaneous viewers
- ✅ **Direct P2P Connection**: Video streams directly from Pi to browsers (minimal server load)
- ✅ **NAT Traversal**: Works across the internet using STUN servers
- ✅ **Camera Auto-Detection**: Supports both USB webcams and Raspberry Pi Camera Module

### Quick Start

#### 1. Install Video Dependencies

```bash
# Install WebRTC and video encoding libraries
pip3 install aiortc av --break-system-packages

# Verify installation
python3 -c "import aiortc, av; print('✅ Video libraries installed')"
```

#### 2. Configure Video Settings

Your `config.json` already has a video section. Enable and customize it:

```bash
nano ~/james-code/config.json
```

Update the video section:

```json
{
  "video": {
    "enabled": true,              # ← Set to true to enable streaming
    "width": 1280,                # Resolution width (640, 1280, 1920)
    "height": 720,                # Resolution height (480, 720, 1080)
    "fps": 30,                    # Frame rate (15, 24, 30)
    "bitrate": 1500000,           # Bitrate in bits/second (higher = better quality)
    "camera_type": "usb"          # "usb" for webcam, "picamera2" for Pi Camera
  },
  "webrtc": {
    "stun_servers": [
      "stun:stun.l.google.com:19302",
      "stun:stun1.l.google.com:19302"
    ],
    "max_viewers": 5              # Maximum simultaneous viewers
  }
}
```

**Camera Type Guide:**
- `"usb"`: For USB webcams (Logitech, generic USB cameras)
- `"picamera2"`: For official Raspberry Pi Camera Module (requires `picamera2` library)

**Resolution & Bitrate Recommendations:**
- **Low bandwidth** (mobile hotspot): 640x480 @ 15fps, bitrate 500000 (500 kbps)
- **Medium quality**: 1280x720 @ 30fps, bitrate 1500000 (1.5 Mbps) - **Default**
- **High quality**: 1920x1080 @ 30fps, bitrate 3000000 (3 Mbps)

#### 3. Test Your Camera

Verify your camera is detected and working:

```bash
cd ~/james-code

# List available cameras
ls /dev/video*
# Should show: /dev/video0 (or /dev/video1, etc.)

# Test camera capture
python3 test_camera.py

# Test specific camera device
python3 test_camera.py 0  # for /dev/video0
```

You should see:
```
📹 Testing camera /dev/video0...
✅ Camera opened successfully
📸 Resolution: 1280x720
🎬 FPS: 30
✅ Camera test complete
```

#### 4. Enable Streaming

Restart the WebSocket client to enable video streaming:

```bash
sudo systemctl restart vantir-websocket-client.service
```

Check logs to verify WebRTC initialized:

```bash
sudo journalctl -u vantir-websocket-client.service -n 50 | grep -i webrtc
```

You should see:
```
✓ WebRTC streamer initialized
📹 Camera type: usb
📐 Resolution: 1280x720 @ 30fps
```

#### 5. Connect from Frontend

To view the stream, your frontend needs to implement WebRTC client. **Complete implementation guides provided:**

- **`WEBRTC_BACKEND_GUIDE.md`** - How to relay WebRTC signaling messages in your backend
- **`WEBRTC_FRONTEND_GUIDE.md`** - Complete JavaScript code for browser video playback

### How It Works

```
┌─────────────────────┐
│   Raspberry Pi      │
│                     │
│  Camera → WebRTC    │──┐
│  (H.264 encoding)   │  │
└─────────────────────┘  │
                          │  Signaling via
                          │  WebSocket Server
┌─────────────────────┐  │  (SDP exchange)
│   Your Backend      │◄─┤
│   (Message relay)   │  │
└─────────────────────┘  │
                          │
┌─────────────────────┐  │  Direct P2P video
│   Web Browser       │◄─┘  stream (UDP/RTP)
│   (Video player)    │
└─────────────────────┘
```

1. **Pi** captures video and encodes with H.264
2. **Signaling** happens through your WebSocket backend (offers/answers/ICE candidates)
3. **Video stream** flows directly from Pi to browser via P2P connection
4. **STUN servers** help traverse NAT/firewalls

### Configuration Reference

**Video Settings:**

| Option | Description | Default | Options |
|--------|-------------|---------|---------|
| `enabled` | Enable/disable video streaming | `false` | `true`, `false` |
| `width` | Video width in pixels | `1280` | `640`, `1280`, `1920` |
| `height` | Video height in pixels | `720` | `480`, `720`, `1080` |
| `fps` | Frames per second | `30` | `15`, `24`, `30` |
| `bitrate` | Encoding bitrate (bits/sec) | `1500000` | `500000` - `5000000` |
| `camera_type` | Camera device type | `"usb"` | `"usb"`, `"picamera2"` |

**WebRTC Settings:**

| Option | Description | Default |
|--------|-------------|---------|
| `stun_servers` | STUN servers for NAT traversal | Google STUN servers |
| `turn_servers` | TURN servers (optional, for restrictive NATs) | `[]` |
| `max_viewers` | Max simultaneous viewers | `5` |

### Troubleshooting

#### Camera Not Detected

```bash
# Check if camera is connected
ls /dev/video*

# Check camera permissions
ls -l /dev/video0

# Test with different camera index
python3 test_camera.py 1  # Try /dev/video1
```

**Common fixes:**
- USB camera not plugged in
- Camera already in use by another process
- Need to add user to `video` group: `sudo usermod -a -G video $USER`

#### WebRTC Not Initializing

```bash
# Check logs for errors
sudo journalctl -u vantir-websocket-client.service -f

# Verify video enabled in config
cat ~/james-code/config.json | grep -A 10 '"video"'

# Test dependencies
python3 -c "import aiortc, av; print('OK')"
```

**Common issues:**
- `config.json` has `"enabled": false`
- Missing dependencies (`pip3 install aiortc av`)
- Camera permissions issue

#### Low Frame Rate / Stuttering

- **Lower resolution**: Try 640x480 instead of 1280x720
- **Reduce FPS**: Try 15fps or 24fps instead of 30fps
- **Lower bitrate**: Reduce to 800000 (800 kbps)
- **Check CPU**: Run `htop` - video encoding is CPU-intensive
- **Network bandwidth**: Ensure stable connection with enough upload speed

#### Connection Issues

- **STUN servers unreachable**: Try adding more STUN servers
- **Firewall blocking**: Ensure UDP ports are open
- **Restrictive NAT**: May need TURN server (relay server) instead of STUN

### Next Steps

1. ✅ Enable and test camera on Pi (Steps 1-4 above)
2. 📘 Read `WEBRTC_BACKEND_GUIDE.md` to add signaling relay to your backend
3. 🌐 Read `WEBRTC_FRONTEND_GUIDE.md` to implement video player in your web app
4. 🎥 View live stream in your browser!

### Files Added for Video Streaming

```
~/james-code/
├── webrtc_streamer.py              # WebRTC streaming engine
├── test_camera.py                  # Camera testing utility
├── WEBRTC_BACKEND_GUIDE.md         # Backend signaling implementation
└── WEBRTC_FRONTEND_GUIDE.md        # Frontend video player code
```

---

## Next Steps

Now that setup is complete:

1. **Test waypoint creation** - Create waypoints in your frontend and verify Pi receives them
2. **Set up WebRTC streaming** - Follow the guides above to enable live video
3. **Customize behavior** - Edit `websocket_client.py` to add your autonomous logic
4. **Add AprilTag detection** - See `apriltag/README.md` for camera-based navigation
5. **Monitor status emails** - Set up email filters/alerts for status monitoring
6. **Scale to multiple Pis** - Repeat this setup on additional Raspberry Pis

---

## Complete Setup Checklist

### Required Setup
- [ ] Repository cloned to `~/james-code`
- [ ] **`config.json` created from `config.example.json`**
- [ ] **`config.json` updated with backend server IP**
- [ ] **`config.json` device section customized (name, location, owner, description)**
- [ ] `.env` file created from `.env.example`
- [ ] `.env` configured with email credentials
- [ ] Gmail App Password created and added to `.env`
- [ ] Python dependencies installed (`websockets`, `aiohttp`, `gpiozero`, `python-dotenv`, `netifaces`)
- [ ] WebSocket client service installed and running
- [ ] Status monitor service installed and running
- [ ] Device ID generated and visible in logs
- [ ] Device registration confirmed by server
- [ ] Heartbeat task started
- [ ] WebSocket connection verified (websocket_status.json shows connected)
- [ ] REST API responding to health checks
- [ ] Initial connection email received
- [ ] Waypoint creation detected in Pi logs
- [ ] System tested after reboot
- [ ] Both services auto-start on boot
- [ ] Status emails arriving every 5 minutes

### Optional - Video Streaming
- [ ] Video dependencies installed (`aiortc`, `av`)
- [ ] Camera detected and tested with `test_camera.py`
- [ ] `config.json` video section enabled and configured
- [ ] WebSocket client restarted, WebRTC initialized in logs
- [ ] Backend implemented WebRTC signaling relay (see `WEBRTC_BACKEND_GUIDE.md`)
- [ ] Frontend implemented WebRTC video player (see `WEBRTC_FRONTEND_GUIDE.md`)
- [ ] Live video stream visible in browser

---

## Getting Help

**View logs:**
```bash
# WebSocket client
sudo journalctl -u vantir-websocket-client.service -f

# Status monitor
sudo journalctl -u status-monitor.service -f

# System logs
sudo journalctl -xe
```

**Check configuration:**
```bash
cat ~/james-code/config.json
cat ~/james-code/.env  # Check email settings
```

**Check connection status:**
```bash
cat ~/james-code/websocket_status.json
```

---

## Success! 🎉

Your Raspberry Pi is now fully autonomous and ready for development. The system will:
- ✅ Auto-connect to backend on every boot
- ✅ Register with persistent device ID
- ✅ Send heartbeat messages every 30 seconds
- ✅ Receive waypoints in real-time
- ✅ Send detailed status emails
- ✅ Monitor system and network health
- ✅ Auto-recover from connection failures
- ✅ Track device metadata (name, location, MAC address)

You're ready to build autonomous behaviors!
