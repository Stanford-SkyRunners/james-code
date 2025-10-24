# Vantir Backend Client

This client connects to both the WebSocket server and REST API for real-time and HTTP-based communication with the Vantir backend.

## Features

### WebSocket Connection
- Real-time bidirectional communication on port 8001
- Receives waypoint creation events (`waypoint_created`)
- Receives launch commands (`waypoint_launch`)
- Receives client join/leave notifications
- Automatic reconnection with exponential backoff (5s → 60s max)
- Never gives up - will keep trying to reconnect indefinitely

### REST API Connection
- Health check on startup (`GET /health`)
- Fetch all waypoints (`GET /points`)
- HTTP requests on port 8000

## Configuration

Edit `/home/james/skyrunners/config.json`:

```json
{
  "email": {
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "from_address": "skyrunnersstatus@gmail.com",
    "to_address": "skyrunnersstatus@gmail.com",
    "password": "your-app-password"
  },
  "backend": {
    "websocket_url": "ws://24.144.90.5:8001",
    "rest_api_url": "http://24.144.90.5:8000",
    "description": "Backend server connection details"
  }
}
```

Replace `24.144.90.5` with your backend server's IP address.

## Backend API Endpoints

The backend server provides these endpoints:

### REST API (Port 8000)
- `GET /` - API information and available endpoints
- `GET /health` - Health check endpoint
- `GET /points` - Get all waypoints
- `POST /points` - Create a new waypoint
- `POST /points/:id/launch` - Launch a specific waypoint
- `DELETE /points/:id` - Delete a waypoint

### WebSocket (Port 8001)
Receives real-time messages:
- `connection` - Initial connection acknowledgment with client ID
- `waypoint_created` - New waypoint created from frontend
- `waypoint_launch` - Launch command issued
- `client_joined` - Another client connected
- `client_left` - Another client disconnected

## Installation

### Quick Setup (Recommended)

Run the automated setup script:
```bash
cd /home/james/skyrunners/backend-client
sudo ./setup-websocket-service.sh
```

This will:
1. Install Python dependencies (`websockets`, `aiohttp`)
2. Make the script executable
3. Install the systemd service
4. Enable auto-start on boot
5. Start the service immediately

### Manual Installation

1. Install dependencies:
```bash
pip3 install websockets aiohttp --break-system-packages
```

2. Make the script executable:
```bash
chmod +x /home/james/skyrunners/backend-client/websocket_client.py
```

3. Test manually:
```bash
python3 /home/james/skyrunners/backend-client/websocket_client.py
```

4. Install as a service:
```bash
sudo cp /home/james/skyrunners/services/vantir-websocket-client.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable vantir-websocket-client.service
sudo systemctl start vantir-websocket-client.service
```

## Service Management

### Check Status
```bash
sudo systemctl status vantir-websocket-client.service
```

### View Live Logs
```bash
sudo journalctl -u vantir-websocket-client.service -f
```

### View Recent Logs
```bash
sudo journalctl -u vantir-websocket-client.service -n 50
```

### Restart Service
```bash
sudo systemctl restart vantir-websocket-client.service
```

### Stop Service
```bash
sudo systemctl stop vantir-websocket-client.service
```

### Disable Auto-start
```bash
sudo systemctl disable vantir-websocket-client.service
```

## Monitoring Connection Status

The client writes its connection status to a JSON file that can be monitored:

```bash
cat /home/james/skyrunners/websocket_status.json
```

Example output:
```json
{
  "connected": true,
  "last_update": "2025-10-24T00:20:56.590392",
  "last_message": "waypoint_created",
  "error": null
}
```

### Watch Status in Real-time
```bash
watch -n 1 cat /home/james/skyrunners/websocket_status.json
```

## Testing Connection

### Test REST API
```bash
# Check if backend is reachable
curl http://YOUR_SERVER_IP:8000/

# Test health endpoint
curl http://YOUR_SERVER_IP:8000/health

# Get all waypoints
curl http://YOUR_SERVER_IP:8000/points
```

### Test WebSocket
The easiest way to test WebSocket is to run the client manually:
```bash
# Stop the service first
sudo systemctl stop vantir-websocket-client.service

# Run manually to see live output
python3 /home/james/skyrunners/backend-client/websocket_client.py

# Press Ctrl+C when done
# Restart the service
sudo systemctl start vantir-websocket-client.service
```

## What Happens When Connected

1. **On Startup:**
   - Checks backend health via REST API
   - Connects to WebSocket server
   - Receives connection acknowledgment with unique client ID

2. **While Running:**
   - Listens for waypoint events
   - Updates status file after each message
   - Automatically reconnects if connection drops

3. **Reconnection Behavior:**
   - First retry: 5 seconds
   - Second retry: 10 seconds
   - Third retry: 20 seconds
   - Fourth retry: 40 seconds
   - Fifth+ retries: 60 seconds (keeps trying forever)

## Device Information

The client identifies itself with:
- `deviceId`: Raspberry Pi hostname (e.g., "jamesraspberrypi")
- `deviceType`: "raspberry_pi"
- `hostname`: System hostname

## Message Handling

### Waypoint Created Event
```python
# Received when a new waypoint is created
{
  "type": "waypoint_created",
  "data": {
    "id": "point_1761290556335_d6x1shbkq",
    "coordinates": [-122.17375, 37.43351],
    "timestamp": "2025-10-24T07:22:36.335Z",
    "metadata": {"zoom": 14.34, "bearing": 0, "pitch": 0}
  }
}
```

### Launch Command
```python
# Received when a waypoint is launched
{
  "type": "waypoint_launch",
  "waypointId": "point_123",
  "data": {
    # Launch-specific data
  }
}
```

## Customization

To add custom behavior when messages are received, edit the `handle_message` method in `websocket_client.py`:

```python
async def handle_message(self, message):
    data = json.loads(message)
    msg_type = data.get('type')

    if msg_type == 'waypoint_launch':
        # Add your launch logic here
        waypoint_id = data.get('waypointId')
        self.execute_launch(waypoint_id)
```

## Troubleshooting

### Connection Refused (errno 111)
- Backend server is not running or port is wrong
- Check with: `curl http://YOUR_SERVER_IP:8000/health`
- Verify ports 8000 and 8001 are accessible

### Service Not Starting
- Check logs: `sudo journalctl -u vantir-websocket-client.service -n 50`
- Verify config.json exists and is valid
- Ensure Python dependencies are installed

### Rapid Connect/Disconnect Loop
- This was fixed by updating endpoints to match backend
- Check that backend has matching `/points` and `/health` endpoints
- Not `/api/devices/*` endpoints (those don't exist)

### Dependencies Not Found
```bash
# Install with break-system-packages flag on Raspberry Pi OS
pip3 install websockets aiohttp --break-system-packages
```

## Files

- `websocket_client.py` - Main client script
- `setup-websocket-service.sh` - Automated installation script
- `../services/vantir-websocket-client.service` - Systemd service file
- `../config.json` - Configuration file
- `../websocket_status.json` - Auto-generated status file

## Architecture

```
Raspberry Pi Client
├── WebSocket (Port 8001)
│   ├── Real-time bidirectional communication
│   ├── Receives waypoint events
│   └── Auto-reconnects on failure
│
└── REST API (Port 8000)
    ├── Health checks
    ├── Fetch waypoints
    └── HTTP-based operations
```

## Next Steps

After installation:
1. Check service status: `sudo systemctl status vantir-websocket-client`
2. View logs to confirm connection: `sudo journalctl -u vantir-websocket-client -f`
3. Test by creating a waypoint in your frontend
4. Check the status file to verify messages are being received
5. The service will auto-start on every boot
