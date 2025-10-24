# Raspberry Pi Status Monitor

Monitors system health and backend connectivity, sending email notifications on WiFi connection and periodic status updates.

## Features

- **WiFi Connection Monitoring** - Waits for WiFi on boot, sends immediate notification
- **Periodic Status Updates** - Sends comprehensive system report every 5 minutes
- **Backend Connection Tracking** - Monitors both WebSocket and REST API connections
- **System Metrics** - CPU temperature, usage, memory, disk space, uptime
- **Email Notifications** - Gmail SMTP integration for status reports

## What Gets Monitored

### Network Information
- WiFi SSID
- IP Address
- Signal Strength

### Backend Connection Status
- **WebSocket** - Reads from `/home/james/skyrunners/websocket_status.json`
  - Connection state (Connected/Disconnected)
  - Last update timestamp
  - Last message received
  - Any errors
- **REST API** - Live health check to backend
  - Tests `GET /health` endpoint
  - Connection state

### System Metrics
- **CPU Temperature** - From `vcgencmd`
- **CPU Usage** - Percentage from `top`
- **Load Average** - 1m, 5m, 15m averages
- **Memory Usage** - Total, used, available
- **Disk Usage** - Total, used, available, percentage
- **System Uptime** - How long Pi has been running

## Installation

### Quick Setup (Recommended)

Run the automated setup script:
```bash
cd /home/james/skyrunners/status-scripts
sudo ./setup-status-monitor.sh
```

This will:
1. Make the script executable
2. Install the systemd service
3. Enable auto-start on boot (waits for network)
4. Start the service immediately

### Manual Installation

1. Make script executable:
```bash
chmod +x /home/james/skyrunners/status-scripts/status_monitor.py
```

2. Install systemd service:
```bash
sudo cp /home/james/skyrunners/services/status-monitor.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable status-monitor.service
sudo systemctl start status-monitor.service
```

## Configuration

Edit `/home/james/skyrunners/config.json`:

```json
{
  "email": {
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "from_address": "skyrunnersstatus@gmail.com",
    "to_address": "skyrunnersstatus@gmail.com",
    "password": "your-app-password-here"
  },
  "backend": {
    "websocket_url": "ws://24.144.90.5:8001",
    "rest_api_url": "http://24.144.90.5:8000"
  }
}
```

### Gmail App Password Setup

1. Go to your Google Account settings
2. Security → 2-Step Verification (must be enabled)
3. App Passwords → Generate new app password
4. Select "Mail" and "Other (Custom name)"
5. Copy the 16-character password to config.json

## Service Management

### Check Status
```bash
sudo systemctl status status-monitor.service
```

### View Live Logs
```bash
sudo journalctl -u status-monitor.service -f
```

### View Recent Logs
```bash
sudo journalctl -u status-monitor.service -n 50
```

### Restart Service
```bash
sudo systemctl restart status-monitor.service
```

### Stop Service
```bash
sudo systemctl stop status-monitor.service
```

### Disable Auto-start
```bash
sudo systemctl disable status-monitor.service
```

## Email Notifications

### Initial Connection Email

Sent immediately when WiFi connects:

```
Subject: 🟢 Raspberry Pi Connected to WiFi: YourNetwork

Raspberry Pi WiFi Connection Notification
==========================================

Your Raspberry Pi has successfully connected to WiFi!

Connection Details:
-------------------
• Network (SSID): YourNetwork
• IP Address: 192.168.1.100
• Signal Strength: -45 dBm
• Connection Time: 2025-10-24 00:17:30

Backend Connection:
-------------------
• WebSocket: ✅ Connected
• REST API: ✅ Connected
• Last Update: 2025-10-24T00:15:31.286353
• Last Message: connection

Status monitoring is now active. You will receive status updates every 5 minutes.
```

### Periodic Status Email

Sent every 5 minutes:

```
Subject: 📊 Pi Status Update - YourNetwork

Raspberry Pi Status Update
==========================
Report Time: 2025-10-24 00:22:30
Script Started: 2025-10-24 00:17:30

Network Information:
--------------------
• Network (SSID): YourNetwork
• IP Address: 192.168.1.100
• Signal Strength: -45 dBm

Backend Connection:
-------------------
• WebSocket: ✅ Connected
• REST API: ✅ Connected
• Last Update: 2025-10-24T00:20:56.590392
• Last Message: waypoint_created
System Metrics:
---------------
• CPU Temperature: 48.7°C
• CPU Usage: 2.3%
• Load Average (1m, 5m, 15m): 0.15, 0.20, 0.18

Memory:
-------
• Total: 1.8G
• Used: 456M
• Available: 1.2G

Disk Usage (/):
---------------
• Total: 30G
• Used: 8.5G (29%)
• Available: 20G

System:
-------
• Uptime: up 2 days, 5 hours
```

## How It Works

### On Boot Sequence
1. Service starts after `network-online.target`
2. Script waits for WiFi connection (pings 8.8.8.8)
3. Once connected, sends initial connection email
4. Enters monitoring loop

### Monitoring Loop
1. Wait 5 minutes
2. Collect system metrics
3. Check backend connection status
4. Format and send status email
5. Repeat

### Backend Status Checking

**WebSocket Status:**
- Reads from `/home/james/skyrunners/websocket_status.json`
- File is auto-generated by `websocket_client.py`
- Shows last connection state and message

**REST API Status:**
- Performs live HTTP GET request to `/health`
- 3-second timeout
- Shows current connection state

## Troubleshooting

### Emails Not Sending

**Check Gmail credentials:**
```bash
# View logs for SMTP errors
sudo journalctl -u status-monitor.service -n 50 | grep -i error
```

Common issues:
- Wrong app password in config.json
- 2-Step Verification not enabled
- SMTP blocked by firewall

**Test email manually:**
```bash
# Stop service
sudo systemctl stop status-monitor.service

# Run manually to see output
python3 /home/james/skyrunners/status-scripts/status_monitor.py

# Ctrl+C to stop
# Restart service
sudo systemctl start status-monitor.service
```

### Backend Status Not Showing

**WebSocket status file missing:**
```bash
# Check if file exists
ls -la /home/james/skyrunners/websocket_status.json

# Check if websocket client is running
sudo systemctl status vantir-websocket-client.service
```

**REST API check failing:**
```bash
# Test manually
curl http://YOUR_SERVER_IP:8000/health

# Check if server is reachable
ping YOUR_SERVER_IP
```

### Service Not Starting on Boot

**Check service is enabled:**
```bash
sudo systemctl is-enabled status-monitor.service
```

**Check service logs:**
```bash
sudo journalctl -u status-monitor.service -b
```

**Verify config file exists:**
```bash
cat /home/james/skyrunners/config.json
```

### WiFi Not Detected

**Check WiFi interface:**
```bash
iwconfig
```

**Check if connected:**
```bash
iwgetid -r  # Shows SSID
hostname -I  # Shows IP
```

## Files

- `status_monitor.py` - Main monitoring script
- `setup-status-monitor.sh` - Automated installation script
- `../services/status-monitor.service` - Systemd service file
- `../config.json` - Configuration (email + backend)
- `../websocket_status.json` - WebSocket status (read-only for this script)

## Customization

### Change Email Frequency

Edit the interval in `status_monitor.py` (line 326):
```python
interval = 300  # 5 minutes = 300 seconds
```

Change to desired seconds:
- 1 minute = 60
- 10 minutes = 600
- 30 minutes = 1800
- 1 hour = 3600

Then restart:
```bash
sudo systemctl restart status-monitor.service
```

### Add Custom Metrics

Edit `get_system_metrics()` method in `status_monitor.py`:
```python
def get_system_metrics(self):
    metrics = {}
    # Add your custom metric here
    metrics['my_metric'] = get_my_custom_data()
    return metrics
```

Then update the email template in `format_status_email()`.

### Customize Email Format

Edit `format_status_email()` or `format_connection_email()` methods to change email content and formatting.

## Dependencies

All dependencies are part of Python standard library:
- `smtplib` - SMTP email
- `subprocess` - System commands
- `json` - Config parsing
- `email.mime` - Email formatting

External commands used:
- `iwgetid` - Get WiFi SSID
- `iwconfig` - Get signal strength
- `hostname` - Get IP address
- `vcgencmd` - Get CPU temperature (Raspberry Pi specific)
- `top` - CPU usage
- `free` - Memory info
- `df` - Disk usage
- `uptime` - System uptime
- `ping` - Network connectivity test

## Next Steps

After installation:
1. Reboot to test boot sequence: `sudo reboot`
2. Check email for WiFi connection notification
3. Verify service is running: `sudo systemctl status status-monitor`
4. Wait 5 minutes for first status update email
5. Monitor logs if needed: `sudo journalctl -u status-monitor -f`
