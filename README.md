# SkyRunners - Raspberry Pi Project

This repository contains scripts and services for the SkyRunners Raspberry Pi system, including status monitoring, backend communication, and AprilTag detection.

## 📁 Project Structure

```
skyrunners/
├── config.json                      # Main configuration file (email, backend URL)
├── websocket_status.json            # WebSocket connection status (auto-generated)
│
├── apriltag/                        # AprilTag detection module
│   ├── detect_apriltags.py          # AprilTag detection script
│   └── README.md                    # AprilTag documentation
│
├── backend-client/                  # Backend WebSocket client
│   ├── websocket_client.py          # WebSocket client script
│   └── setup-websocket-service.sh   # Installation script
│
├── status-scripts/                  # Status monitoring system
│   ├── status_monitor.py            # Main status monitor script
│   └── setup-status-monitor.sh      # Installation script
│
├── services/                        # Systemd service files
│   ├── vantir-websocket-client.service
│   └── status-monitor.service
│
└── docs/                            # Documentation
    ├── WEBSOCKET_SETUP.md           # WebSocket client setup guide
    └── STATUS_MONITOR.md            # Status monitor setup guide
```

## 🚀 Quick Start

### 1. Configure Settings

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
    "password": "your-app-password"
  },
  "backend": {
    "websocket_url": "ws://YOUR_SERVER_IP:8001",
    "rest_api_url": "http://YOUR_SERVER_IP:8000"
  }
}
```

### 2. Install Status Monitor

```bash
cd /home/james/skyrunners/status-scripts
./setup-status-monitor.sh
```

This will:
- Enable status monitoring on boot
- Send email on WiFi connection
- Send status updates every 5 minutes
- Include backend connection status

### 3. Install WebSocket Client

```bash
cd /home/james/skyrunners/backend-client
sudo ./setup-websocket-service.sh
```

This will:
- Install websockets library
- Enable WebSocket client on boot
- Auto-connect to backend server
- Auto-reconnect on connection loss

## 📊 What Happens on Boot

When your Raspberry Pi boots up:

1. ✅ **Network connects** - Waits for WiFi connection
2. ✅ **Services start** - Both status monitor and WebSocket client start automatically
3. ✅ **Email sent** - You receive a connection notification:

```
🟢 Raspberry Pi Connected to WiFi: SkyRunners

Connection Details:
-------------------
• Network (SSID): SkyRunners
• IP Address: 192.168.8.116
• Signal Strength: -52

Backend Connection:
-------------------
• WebSocket: ✅ Connected
• REST API: ✅ Connected
• Last Update: 2025-10-23 21:30:00
• Last Message: connection

Status monitoring is now active. You will receive status updates every 5 minutes.
```

4. ✅ **Periodic updates** - Every 5 minutes you get system metrics + backend status

## 🛠️ Service Management

### Status Monitor

```bash
# Check status
sudo systemctl status status-monitor

# View logs
sudo journalctl -u status-monitor -f

# Restart
sudo systemctl restart status-monitor

# Stop
sudo systemctl stop status-monitor
```

### WebSocket Client

```bash
# Check status
sudo systemctl status vantir-websocket-client

# View logs
sudo journalctl -u vantir-websocket-client -f

# Restart
sudo systemctl restart vantir-websocket-client

# Stop
sudo systemctl stop vantir-websocket-client
```

## 📖 Documentation

- **[WebSocket Setup Guide](docs/WEBSOCKET_SETUP.md)** - Detailed WebSocket client documentation
- **[Status Monitor Guide](docs/STATUS_MONITOR.md)** - Status monitoring system documentation

## 🔧 Components

### Status Monitor
- Monitors WiFi connection, CPU, memory, disk usage
- Sends email notifications
- Tracks both WebSocket and REST API connection status
- Tests backend health endpoint
- Runs every 5 minutes

### WebSocket Client
- Connects to Vantir backend server (WebSocket + REST API)
- Receives waypoint creation events in real-time
- Receives launch commands
- Fetches waypoints via REST API (/points)
- Checks backend health (/health)
- Auto-reconnects on failure with exponential backoff
- Updates status file for monitoring

### AprilTag Detection
- Computer vision for AprilTag detection
- (See apriltag/README.md for details)

## 📝 Status Files

### websocket_status.json
Auto-generated file tracking WebSocket connection:
```json
{
  "connected": true,
  "last_update": "2025-10-23T21:30:00.123456",
  "last_message": "waypoint_created",
  "error": null
}
```

### status_monitor.log
Log file from status monitor service (created in root directory)

## 🔒 Configuration Files

### config.json
Main configuration file containing:
- Email SMTP settings
- Backend WebSocket URL
- Credentials (keep this file secure!)

## ⚙️ Requirements

- Python 3.7+
- systemd (for auto-start services)
- Network connectivity
- Gmail account with app password (for email notifications)
- Python packages:
  - `websockets` - For WebSocket client
  - `aiohttp` - For async HTTP requests

## 🐛 Troubleshooting

### Email not sending
- Check config.json has correct email settings
- Verify Gmail app password is correct
- Check logs: `sudo journalctl -u status-monitor -f`

### WebSocket not connecting
- Verify backend server is running
- Check WebSocket URL in config.json
- Test connectivity: `ping YOUR_SERVER_IP`
- View logs: `sudo journalctl -u vantir-websocket-client -f`

### Services not starting on boot
- Verify service is enabled: `sudo systemctl is-enabled status-monitor`
- Check service status: `sudo systemctl status status-monitor`
- View system logs: `sudo journalctl -xe`

## 📞 Support

For issues or questions:
- Check the documentation in `docs/`
- View service logs
- Review configuration files

## 🎯 Next Steps

After setup:
1. Reboot to test auto-start: `sudo reboot`
2. Check your email for connection notification
3. Verify services are running
4. Test backend communication by creating a waypoint in your frontend
