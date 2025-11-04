# SkyRunners - Raspberry Pi Autonomous System

Complete setup guide for running the SkyRunners system on Raspberry Pi. Follow this guide top-to-bottom to get everything working.

## What This Does

Your Raspberry Pi will:
- ✅ Auto-connect to your backend server on boot
- ✅ Receive waypoints in real-time via WebSocket
- ✅ Send status emails every 5 minutes with system metrics
- ✅ Send immediate email notification on WiFi connection
- ✅ Monitor backend connection (WebSocket + REST API)
- ✅ Auto-reconnect if connection drops
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
~/skyrunners/
├── .env                             # Email credentials (you'll create this)
├── .env.example                     # Template for .env file
├── config.json                      # Main configuration (backend URLs, SMTP settings)
├── websocket_status.json            # Auto-generated connection status
├── status_monitor.log               # Auto-generated log file
│
├── backend-client/                  # WebSocket client
│   ├── websocket_client.py          # Connects to backend, receives waypoints
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
git clone <your-repository-url> skyrunners
cd skyrunners
```

Or copy from another system:
```bash
scp -r skyrunners/ pi@<raspberry-pi-ip>:~/
```

---

## Step 2: Configure Environment Variables

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

### Gmail App Password Setup

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

## Step 3: Configure Backend Settings (Optional)

The backend server URLs are already set in `config.json`. Only edit if your backend server IP differs:

```bash
nano ~/james-code/config.json
```

```json
{
  "email": {
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587
  },
  "backend": {
    "websocket_url": "ws://YOUR_SERVER_IP:8001",
    "rest_api_url": "http://YOUR_SERVER_IP:8000"
  },
  "led": {
    "enabled": false,
    "gpio_pin": 17,
    "blink_duration": 3
  }
}
```

**Important:**
- Replace `YOUR_SERVER_IP` with your backend server's IP address
- Use port **8001** for WebSocket
- Use port **8000** for REST API
- LED control is optional (set `enabled: true` to use)

---

## Step 4: Install Python Dependencies

Install required Python packages:

```bash
pip3 install websockets aiohttp gpiozero python-dotenv --break-system-packages
```

> **Note:** The `--break-system-packages` flag is required on modern Raspberry Pi OS.

Verify installation:
```bash
python3 -c "import websockets, aiohttp, dotenv; print('✅ Dependencies installed')"
```

---

## Step 5: Install WebSocket Client Service

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
✓ Backend health check passed
🔌 Connected to WebSocket: ws://YOUR_SERVER_IP:8001
✓ Connected to server with ID: <random-id>
```

Press Ctrl+C to exit logs.

---

## Step 6: Install Status Monitor Service

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

## Step 7: Test Your Setup

### 7.1 Check WebSocket Connection

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

### 7.2 Test REST API Connection

```bash
# Health check
curl http://YOUR_SERVER_IP:8000/health

# Should return:
# {"status":"healthy","timestamp":"...","uptime":...}

# Get waypoints
curl http://YOUR_SERVER_IP:8000/api/points
```

### 7.3 Check Email Notifications

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

### 7.4 Test Waypoint Reception

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

## Step 8: Reboot Test

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
   cat ~/skyrunners/websocket_status.json
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
tail -f ~/skyrunners/status_monitor.log
```

### Quick Status Check

```bash
# Check both services at once
systemctl is-active vantir-websocket-client.service status-monitor.service

# Check connection status file
cat ~/skyrunners/websocket_status.json

# Watch connection status in real-time
watch -n 1 cat ~/skyrunners/websocket_status.json
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
Receives real-time messages:
- `connection` - Connection acknowledgment with client ID
- `waypoint_created` - New waypoint created
- `waypoint_launch` - Launch command issued
- `send_test_email` - Test email trigger (LED + email)
- `client_joined` - Another client connected
- `client_left` - Another client disconnected

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
python3 ~/skyrunners/status-scripts/status_monitor.py

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
~/skyrunners/
├── .env                             # Email credentials (you create this)
├── .env.example                     # Template for .env file
├── config.json                      # Main configuration (backend URLs, SMTP)
├── websocket_status.json            # Auto-generated status file
├── status_monitor.log               # Auto-generated log file
│
├── backend-client/
│   ├── websocket_client.py          # WebSocket client
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
│         Raspberry Pi (skyrunners)           │
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
3. **WebSocket Client** starts, connects to backend
4. Email sent with connection notification
5. Both services run continuously

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

## Next Steps

Now that setup is complete:

1. **Test waypoint creation** - Create waypoints in your frontend and verify Pi receives them
2. **Customize behavior** - Edit `websocket_client.py` to add your autonomous logic
3. **Add AprilTag detection** - See `apriltag/README.md` for camera-based navigation
4. **Monitor status emails** - Set up email filters/alerts for status monitoring
5. **Scale to multiple Pis** - Repeat this setup on additional Raspberry Pis

---

## Complete Setup Checklist

- [ ] Repository cloned to `~/skyrunners`
- [ ] `.env` file created from `.env.example`
- [ ] `.env` configured with email credentials
- [ ] `config.json` configured with backend server IP (if needed)
- [ ] Gmail App Password created and added to `.env`
- [ ] Python dependencies installed (`websockets`, `aiohttp`, `gpiozero`, `python-dotenv`)
- [ ] WebSocket client service installed and running
- [ ] Status monitor service installed and running
- [ ] WebSocket connection verified (websocket_status.json shows connected)
- [ ] REST API responding to health checks
- [ ] Initial connection email received
- [ ] Waypoint creation detected in Pi logs
- [ ] System tested after reboot
- [ ] Both services auto-start on boot
- [ ] Status emails arriving every 5 minutes

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
cat ~/skyrunners/config.json
cat ~/skyrunners/.env  # Check email settings
```

**Check connection status:**
```bash
cat ~/skyrunners/websocket_status.json
```

---

## Success! 🎉

Your Raspberry Pi is now fully autonomous and ready for development. The system will:
- ✅ Auto-connect to backend on every boot
- ✅ Receive waypoints in real-time
- ✅ Send detailed status emails
- ✅ Monitor system and network health
- ✅ Auto-recover from connection failures

You're ready to build autonomous behaviors!
