# SkyRunners Raspberry Pi - Quick Start Guide

This guide will help you set up the SkyRunners Raspberry Pi system from scratch on a new Raspberry Pi.

## Prerequisites

- Raspberry Pi (tested on Raspberry Pi 4)
- Raspberry Pi OS installed
- Internet connection (WiFi or Ethernet)
- Gmail account with App Password
- Vantir backend server running and accessible

## Step 1: Clone the Repository

```bash
cd ~
git clone <your-repo-url> skyrunners
cd skyrunners
```

Or if you're setting up on a new Pi, copy the files:
```bash
scp -r skyrunners/ pi@NEW_PI_IP:~/
```

## Step 2: Configure Settings

Edit the main configuration file:
```bash
nano config.json
```

Update with your settings:
```json
{
  "email": {
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "from_address": "your-email@gmail.com",
    "to_address": "your-email@gmail.com",
    "password": "your-16-char-app-password"
  },
  "backend": {
    "websocket_url": "ws://YOUR_SERVER_IP:8001",
    "rest_api_url": "http://YOUR_SERVER_IP:8000",
    "description": "Backend server connection details"
  }
}
```

### Getting Gmail App Password

1. Go to https://myaccount.google.com/
2. Security → 2-Step Verification (enable if not already)
3. App Passwords → Generate new
4. Select "Mail" and "Other (Custom name)"
5. Copy the 16-character password (no spaces) into config.json

## Step 3: Install Python Dependencies

```bash
pip3 install websockets aiohttp --break-system-packages
```

## Step 4: Install WebSocket Client Service

```bash
cd ~/skyrunners/backend-client
sudo ./setup-websocket-service.sh
```

You should see:
```
==========================================
Vantir WebSocket Client Service Setup
==========================================

📦 Installing Python dependencies...
🔧 Making Python script executable...
📋 Installing systemd service...
🔄 Reloading systemd...
✅ Enabling service to start on boot...
🚀 Starting service...

==========================================
✅ Setup Complete!
==========================================
```

Verify it's running:
```bash
sudo systemctl status vantir-websocket-client.service
```

Check logs:
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

## Step 5: Install Status Monitor Service

```bash
cd ~/skyrunners/status-scripts
sudo ./setup-status-monitor.sh
```

Verify it's running:
```bash
sudo systemctl status status-monitor.service
```

## Step 6: Test the Setup

### Test Backend Connection

Check WebSocket status:
```bash
cat ~/skyrunners/websocket_status.json
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

### Test REST API

```bash
curl http://YOUR_SERVER_IP:8000/health
```

Should return:
```json
{"status":"healthy","timestamp":"...","uptime":...}
```

Get waypoints:
```bash
curl http://YOUR_SERVER_IP:8000/points
```

### Test Email Notifications

Restart status monitor to trigger an email:
```bash
sudo systemctl restart status-monitor.service
```

Check your email inbox - you should receive a status update within 1-2 minutes.

### Test Waypoint Reception

1. Open your Vantir frontend
2. Create a new waypoint on the map
3. Check Pi logs:
```bash
sudo journalctl -u vantir-websocket-client.service -n 10
```

You should see:
```
[2025-10-24 00:22:37] Received: waypoint_created
📍 NEW WAYPOINT CREATED
   ID: point_...
   Coordinates: [...]
   Timestamp: ...
```

## Step 7: Reboot Test

Test that everything auto-starts on boot:
```bash
sudo reboot
```

After reboot:
1. Check your email - you should receive WiFi connection notification
2. Check services are running:
```bash
sudo systemctl status vantir-websocket-client.service
sudo systemctl status status-monitor.service
```
3. Verify backend connection:
```bash
cat ~/skyrunners/websocket_status.json
```

## Complete Setup Checklist

- [ ] Repository cloned/copied to `~/skyrunners`
- [ ] `config.json` configured with email and backend URL
- [ ] Gmail App Password created and added to config
- [ ] Python dependencies installed (`websockets`, `aiohttp`)
- [ ] WebSocket client service installed and running
- [ ] Status monitor service installed and running
- [ ] Backend connection verified (websocket_status.json shows connected)
- [ ] REST API responding to health checks
- [ ] Email notification received
- [ ] Waypoint creation detected in Pi logs
- [ ] System tested after reboot
- [ ] Both services auto-start on boot

## Service Management Commands

### WebSocket Client

```bash
# Check status
sudo systemctl status vantir-websocket-client.service

# View live logs
sudo journalctl -u vantir-websocket-client.service -f

# Restart
sudo systemctl restart vantir-websocket-client.service

# Stop
sudo systemctl stop vantir-websocket-client.service

# Disable auto-start
sudo systemctl disable vantir-websocket-client.service
```

### Status Monitor

```bash
# Check status
sudo systemctl status status-monitor.service

# View live logs
sudo journalctl -u status-monitor.service -f

# Restart (triggers immediate email)
sudo systemctl restart status-monitor.service

# Stop
sudo systemctl stop status-monitor.service

# Disable auto-start
sudo systemctl disable status-monitor.service
```

## File Locations

```
~/skyrunners/
├── config.json                      # Main configuration
├── websocket_status.json            # Auto-generated WebSocket status
├── README.md                        # Main documentation
├── QUICKSTART.md                    # This file
│
├── backend-client/
│   ├── websocket_client.py          # WebSocket client
│   ├── setup-websocket-service.sh   # Install script
│   └── README.md                    # Detailed documentation
│
├── status-scripts/
│   ├── status_monitor.py            # Status monitor
│   ├── setup-status-monitor.sh      # Install script
│   └── README.md                    # Detailed documentation
│
├── services/
│   ├── vantir-websocket-client.service  # Systemd service
│   └── status-monitor.service           # Systemd service
│
├── apriltag/
│   ├── detect_apriltags.py          # AprilTag detection
│   └── README.md                    # AprilTag documentation
│
└── docs/
    ├── WEBSOCKET_SETUP.md           # WebSocket setup guide
    └── STATUS_MONITOR.md            # Status monitor guide
```

## Backend API Endpoints

Your backend server provides these endpoints:

### REST API (Port 8000)
- `GET /` - API information
- `GET /health` - Health check
- `GET /points` - Get all waypoints
- `POST /points` - Create waypoint
- `POST /points/:id/launch` - Launch waypoint
- `DELETE /points/:id` - Delete waypoint

### WebSocket (Port 8001)
Receives real-time messages:
- `connection` - Connection acknowledgment
- `waypoint_created` - New waypoint
- `waypoint_launch` - Launch command
- `client_joined` - Client connected
- `client_left` - Client disconnected

## Troubleshooting

### WebSocket Not Connecting

```bash
# Check if backend is reachable
ping YOUR_SERVER_IP

# Test REST API
curl http://YOUR_SERVER_IP:8000/health

# Check client logs
sudo journalctl -u vantir-websocket-client.service -n 50

# Verify config
cat ~/skyrunners/config.json
```

Common issues:
- Wrong IP address in config.json
- Firewall blocking ports 8000 or 8001
- Backend server not running
- Wrong port numbers (should be 8001 for WS, 8000 for REST)

### Emails Not Sending

```bash
# Check status monitor logs
sudo journalctl -u status-monitor.service -n 50 | grep -i error

# Test manually
sudo systemctl stop status-monitor.service
python3 ~/skyrunners/status-scripts/status_monitor.py
# Ctrl+C to stop
sudo systemctl start status-monitor.service
```

Common issues:
- Wrong Gmail app password
- 2-Step Verification not enabled
- Email address typo in config.json

### Services Not Starting on Boot

```bash
# Check if enabled
sudo systemctl is-enabled vantir-websocket-client.service
sudo systemctl is-enabled status-monitor.service

# Enable if needed
sudo systemctl enable vantir-websocket-client.service
sudo systemctl enable status-monitor.service

# Check boot logs
sudo journalctl -b | grep vantir
sudo journalctl -b | grep status-monitor
```

### Dependency Errors

```bash
# Reinstall Python packages
pip3 install websockets aiohttp --break-system-packages --force-reinstall

# Check if installed
python3 -c "import websockets; import aiohttp; print('OK')"
```

## What Happens Automatically

### On Boot
1. System boots
2. Network connects (WiFi or Ethernet)
3. **Status Monitor** starts, waits for network
4. **WebSocket Client** starts, connects to backend
5. Email sent with connection notification
6. Both services run continuously

### Every 5 Minutes
1. Status monitor collects system metrics
2. Checks backend connection (WebSocket + REST API)
3. Sends status email with all information

### When Waypoint Created
1. Frontend creates waypoint
2. Backend sends WebSocket message
3. Pi receives `waypoint_created` event
4. Logged to journalctl
5. Status file updated

### If Connection Lost
1. WebSocket client detects disconnect
2. Waits 5 seconds, tries to reconnect
3. If fails, waits 10 seconds
4. If fails, waits 20 seconds
5. Continues with exponential backoff up to 60 seconds
6. Keeps trying forever until reconnected
7. Status file updated with error
8. Status monitor reports disconnection in next email

## Next Steps

Now that your setup is complete:

1. **Customize behavior** - Edit `websocket_client.py` to add custom waypoint/launch handling
2. **Add AprilTag detection** - See `apriltag/README.md` for camera setup
3. **Adjust email frequency** - Edit `status_monitor.py` interval (default: 5 minutes)
4. **Add monitoring** - Set up alerts based on status emails
5. **Scale to multiple Pis** - Repeat this setup on additional Raspberry Pis

## Getting Help

- **Main README**: `~/skyrunners/README.md`
- **Backend Client**: `~/skyrunners/backend-client/README.md`
- **Status Monitor**: `~/skyrunners/status-scripts/README.md`
- **AprilTag**: `~/skyrunners/apriltag/README.md`
- **Detailed Guides**: `~/skyrunners/docs/`

View logs for debugging:
```bash
# WebSocket client
sudo journalctl -u vantir-websocket-client.service -f

# Status monitor
sudo journalctl -u status-monitor.service -f

# System logs
sudo journalctl -xe
```

## Success!

Your Raspberry Pi is now:
- ✅ Auto-connecting to backend on boot
- ✅ Receiving waypoints in real-time
- ✅ Sending status emails every 5 minutes
- ✅ Auto-reconnecting if connection drops
- ✅ Monitoring system health

You're ready to start building autonomous behaviors!
