# WebSocket Client Setup for Raspberry Pi

This guide explains how to set up the WebSocket client to automatically connect to your backend server on boot and include the connection status in your status emails.

## Quick Setup

### 1. Update Backend Server URL

Edit the configuration file to point to your backend server:

```bash
nano /home/james/skyrunners/config.json
```

Update the `websocket_url` to your server's IP address:
```json
{
  "backend": {
    "websocket_url": "ws://YOUR_SERVER_IP:3001"
  }
}
```

For example, if your server is at `192.168.1.100`:
```json
{
  "backend": {
    "websocket_url": "ws://192.168.1.100:3001"
  }
}
```

### 2. Run the Setup Script

Install and enable the WebSocket client service:

```bash
cd /home/james/skyrunners/backend-client
sudo ./setup-websocket-service.sh
```

This script will:
- Install required Python dependencies (websockets)
- Make the Python script executable
- Install the systemd service
- Enable auto-start on boot
- Start the service immediately

### 3. Verify It's Running

Check the service status:
```bash
sudo systemctl status vantir-websocket-client.service
```

View live logs:
```bash
sudo journalctl -u vantir-websocket-client.service -f
```

## What's Included

### Files Created

1. **`backend-client/websocket_client.py`** - Main WebSocket client script
   - Connects to backend server
   - Listens for waypoint and launch commands
   - Updates connection status file
   - Auto-reconnects on connection loss

2. **`websocket_status.json`** - Status file (created automatically in root)
   - Stores current connection state
   - Read by status monitor for email reports
   - Updated in real-time by the client

3. **`services/vantir-websocket-client.service`** - Systemd service file
   - Enables auto-start on boot
   - Automatic restart on failure
   - Runs after network is available

4. **`backend-client/setup-websocket-service.sh`** - Installation script
   - One-command setup
   - Installs dependencies
   - Configures service

### Status Monitor Integration

The status monitor has been updated to include backend connection status in all emails:

#### WiFi Connection Email (on boot)
```
🟢 Raspberry Pi Connected to WiFi: SkyRunners

Backend Connection:
-------------------
• Status: ✅ Connected
• Last Update: 2025-10-23 21:30:00
• Last Message: waypoint_created
```

#### Periodic Status Updates (every 5 minutes)
```
📊 Pi Status Update - SkyRunners

Backend Connection:
-------------------
• Status: ✅ Connected
• Last Update: 2025-10-23 21:35:00
• Last Message: waypoint_launch
```

If disconnected:
```
Backend Connection:
-------------------
• Status: ❌ Disconnected
• Last Update: 2025-10-23 21:30:00
• Last Message: connection
• Error: Connection closed by server
```

## WebSocket Client Features

### Auto-Reconnection
- Automatically reconnects if connection is lost
- Exponential backoff (5s → 10s → 20s → 40s → 60s max)
- Runs continuously until manually stopped

### Message Handling

The client listens for these message types:

1. **`waypoint_created`** - New waypoint from frontend
2. **`waypoint_launch`** - Launch command clicked
3. **`connection`** - Connected to server
4. **`client_joined`** - Another client connected
5. **`client_left`** - Client disconnected

### Status Tracking

Connection status is saved to `/home/james/skyrunners/websocket_status.json`:

```json
{
  "connected": true,
  "last_update": "2025-10-23T21:30:00.123456",
  "last_message": "waypoint_created",
  "error": null
}
```

## Useful Commands

### Service Management

```bash
# Check status
sudo systemctl status vantir-websocket-client.service

# Start service
sudo systemctl start vantir-websocket-client.service

# Stop service
sudo systemctl stop vantir-websocket-client.service

# Restart service
sudo systemctl restart vantir-websocket-client.service

# Enable auto-start on boot
sudo systemctl enable vantir-websocket-client.service

# Disable auto-start
sudo systemctl disable vantir-websocket-client.service
```

### Viewing Logs

```bash
# View live logs
sudo journalctl -u vantir-websocket-client.service -f

# View last 50 lines
sudo journalctl -u vantir-websocket-client.service -n 50

# View logs since boot
sudo journalctl -u vantir-websocket-client.service -b
```

### Manual Testing

Run the client manually (for testing):
```bash
python3 /home/james/skyrunners/backend-client/websocket_client.py
```

Stop with `Ctrl+C`

## Customizing the Client

Edit `/home/james/skyrunners/backend-client/websocket_client.py` to add your custom logic:

### Example: Handle Launch Command

```python
elif msg_type == 'waypoint_launch':
    waypoint_id = data.get('waypointId')
    launch_data = data.get('data', {})

    # Your custom code here
    print(f"Launching to waypoint {waypoint_id}")

    # Example: Control GPIO
    # import RPi.GPIO as GPIO
    # GPIO.setmode(GPIO.BCM)
    # GPIO.setup(18, GPIO.OUT)
    # GPIO.output(18, GPIO.HIGH)

    # Example: Navigate to coordinates
    # coordinates = launch_data.get('coordinates')
    # navigate_to(coordinates)
```

After editing, restart the service:
```bash
sudo systemctl restart vantir-websocket-client.service
```

## Troubleshooting

### Service Won't Start

Check if Python 3 and websockets are installed:
```bash
python3 --version
pip3 list | grep websockets
```

Install websockets if missing:
```bash
pip3 install websockets
```

### Can't Connect to Backend

1. Check if backend server is running
2. Verify the WebSocket URL in `/home/james/skyrunners/config.json`
3. Test connectivity:
   ```bash
   ping YOUR_SERVER_IP
   ```

### Status Not Showing in Emails

1. Check if status file exists:
   ```bash
   cat /home/james/skyrunners/websocket_status.json
   ```

2. Verify service is running:
   ```bash
   sudo systemctl status vantir-websocket-client.service
   ```

### View Real-time Status

```bash
watch -n 1 cat /home/james/skyrunners/websocket_status.json
```

## On Every Boot

When your Raspberry Pi boots up:

1. ✅ Network connection established
2. ✅ Status monitor starts → sends WiFi connection email with backend status
3. ✅ WebSocket client service starts automatically
4. ✅ Client connects to backend server
5. ✅ Status updates every 5 minutes include backend connection status

## Next Steps

After setup:

1. Reboot your Pi to test auto-start:
   ```bash
   sudo reboot
   ```

2. Check your email for the connection notification with backend status

3. Verify the service started automatically:
   ```bash
   sudo systemctl status vantir-websocket-client.service
   ```

4. Create a waypoint in your frontend and watch the logs:
   ```bash
   sudo journalctl -u vantir-websocket-client.service -f
   ```
