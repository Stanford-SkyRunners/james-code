#!/usr/bin/env python3
"""
Vantir WebSocket Client for Raspberry Pi
Connects to the backend server and listens for waypoint and launch commands.
"""

import asyncio
import websockets
import json
import signal
import sys
from datetime import datetime
import os
import aiohttp
import socket

# Load configuration
CONFIG_FILE = '/home/james/skyrunners/config.json'
STATUS_FILE = '/home/james/skyrunners/websocket_status.json'

def load_config():
    """Load configuration from JSON file."""
    try:
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: Configuration file not found: {CONFIG_FILE}")
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON in configuration file: {CONFIG_FILE}")
        sys.exit(1)

def get_device_info():
    """Get device information for registration."""
    try:
        hostname = socket.gethostname()
        return {
            'deviceId': hostname,
            'deviceType': 'raspberry_pi',
            'hostname': hostname
        }
    except Exception as e:
        print(f"Error getting device info: {e}")
        return {
            'deviceId': 'unknown',
            'deviceType': 'raspberry_pi',
            'hostname': 'unknown'
        }

def update_status(connected, last_message=None, error=None):
    """Update WebSocket connection status file."""
    status = {
        'connected': connected,
        'last_update': datetime.now().isoformat(),
        'last_message': last_message,
        'error': error
    }
    try:
        with open(STATUS_FILE, 'w') as f:
            json.dump(status, f, indent=2)
    except Exception as e:
        print(f"Error updating status file: {e}")

class VantirClient:
    def __init__(self, websocket_url, rest_api_url):
        self.websocket_url = websocket_url
        self.rest_api_url = rest_api_url
        self.websocket = None
        self.should_reconnect = True
        self.device_info = get_device_info()
        self.session = None
        self.heartbeat_task = None
        self.heartbeat_interval = 30  # Send heartbeat every 30 seconds

    async def check_health(self):
        """Check backend health status."""
        try:
            if not self.session:
                self.session = aiohttp.ClientSession()

            url = f"{self.rest_api_url}/health"
            async with self.session.get(url) as response:
                if response.status == 200:
                    print(f"✓ Backend health check passed")
                    return True
                else:
                    print(f"⚠️  Backend health check failed: {response.status}")
                    return False
        except Exception as e:
            print(f"❌ Backend health check error: {e}")
            return False

    async def send_heartbeat(self):
        """Send periodic heartbeat (disabled - backend doesn't support this endpoint)."""
        # Backend doesn't have /api/devices/heartbeat endpoint
        # Keeping this method for future use if needed
        pass

    async def fetch_waypoints(self):
        """Fetch all waypoints from REST API."""
        try:
            if not self.session:
                self.session = aiohttp.ClientSession()

            url = f"{self.rest_api_url}/points"
            async with self.session.get(url) as response:
                if response.status == 200:
                    waypoints = await response.json()
                    print(f"📍 Fetched {len(waypoints)} waypoints")
                    return waypoints
                else:
                    print(f"⚠️  Failed to fetch waypoints: {response.status}")
                    return []
        except Exception as e:
            print(f"❌ Error fetching waypoints: {e}")
            return []

    async def update_device_status(self, status_data):
        """Update device status (disabled - backend doesn't support this endpoint)."""
        # Backend doesn't have /api/devices/status endpoint
        # Keeping this method for future use if needed
        pass

    async def handle_message(self, message):
        """Handle incoming WebSocket messages."""
        try:
            data = json.loads(message)
            msg_type = data.get('type')

            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            print(f"\n[{timestamp}] Received: {msg_type}")

            if msg_type == 'connection':
                client_id = data.get('clientId')
                print(f"✓ Connected to server with ID: {client_id}")
                update_status(True, msg_type)

            elif msg_type == 'waypoint_created':
                waypoint_data = data.get('data', {})
                print(f"📍 NEW WAYPOINT CREATED")
                print(f"   ID: {waypoint_data.get('id')}")
                print(f"   Coordinates: {waypoint_data.get('coordinates')}")
                print(f"   Timestamp: {waypoint_data.get('timestamp')}")
                update_status(True, msg_type)

                # Add your custom waypoint handling here
                # Example: Store waypoint, prepare navigation, etc.

            elif msg_type == 'waypoint_launch':
                waypoint_id = data.get('waypointId')
                launch_data = data.get('data', {})
                print(f"🚀 LAUNCH COMMAND RECEIVED")
                print(f"   Waypoint ID: {waypoint_id}")
                print(f"   Data: {json.dumps(launch_data, indent=2)}")
                update_status(True, msg_type)

                # Add your custom launch logic here
                # Example: Start navigation, activate motors, etc.
                # self.execute_launch(waypoint_id, launch_data)

            elif msg_type == 'client_joined':
                client_id = data.get('clientId')
                print(f"👋 Client joined: {client_id}")
                update_status(True, msg_type)

            elif msg_type == 'client_left':
                client_id = data.get('clientId')
                print(f"👋 Client left: {client_id}")
                update_status(True, msg_type)

            else:
                print(f"❓ Unknown message type: {msg_type}")
                print(f"   Data: {json.dumps(data, indent=2)}")
                update_status(True, msg_type)

        except json.JSONDecodeError as e:
            print(f"❌ Error decoding message: {e}")
            update_status(True, error=str(e))
        except Exception as e:
            print(f"❌ Error handling message: {e}")
            update_status(True, error=str(e))

    async def listen(self):
        """Listen for messages from the WebSocket server."""
        try:
            # Check backend health first
            await self.check_health()

            # Connect to WebSocket
            async with websockets.connect(self.websocket_url) as websocket:
                self.websocket = websocket
                print(f"🔌 Connected to WebSocket: {self.websocket_url}")
                update_status(True)

                async for message in websocket:
                    await self.handle_message(message)

        except websockets.exceptions.ConnectionClosed:
            print("⚠️  WebSocket connection closed by server")
            update_status(False, error="Connection closed by server")
        except Exception as e:
            print(f"❌ Connection error: {e}")
            update_status(False, error=str(e))

    async def connect_with_retry(self):
        """Connect to WebSocket with automatic retry."""
        retry_delay = 5
        max_retry_delay = 60

        while self.should_reconnect:
            try:
                print(f"\n{'='*60}")
                print(f"Vantir WebSocket Client")
                print(f"{'='*60}")
                print(f"Connecting to: {self.websocket_url}")
                print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"{'='*60}\n")

                await self.listen()

            except Exception as e:
                print(f"\n❌ Connection failed: {e}")
                update_status(False, error=str(e))

                if self.should_reconnect:
                    print(f"⏳ Retrying in {retry_delay} seconds...")
                    await asyncio.sleep(retry_delay)

                    # Exponential backoff
                    retry_delay = min(retry_delay * 2, max_retry_delay)
                else:
                    break

    async def cleanup(self):
        """Clean up resources."""
        if self.session and not self.session.closed:
            await self.session.close()

    def stop(self):
        """Stop the client and prevent reconnection."""
        print("\n\n🛑 Shutting down client...")
        self.should_reconnect = False
        update_status(False, error="Client stopped by user")

def signal_handler(signum, frame):
    """Handle shutdown signals."""
    print(f"\n\nReceived signal {signum}")
    sys.exit(0)

async def main():
    """Main entry point."""
    # Load configuration
    config = load_config()
    backend_config = config.get('backend', {})
    websocket_url = backend_config.get('websocket_url', 'ws://localhost:8001')
    rest_api_url = backend_config.get('rest_api_url', 'http://localhost:8000')

    print(f"\n{'='*60}")
    print(f"Vantir Client - Dual Connection Mode")
    print(f"{'='*60}")
    print(f"WebSocket: {websocket_url}")
    print(f"REST API:  {rest_api_url}")
    print(f"{'='*60}\n")

    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Create and run client
    client = VantirClient(websocket_url, rest_api_url)

    try:
        await client.connect_with_retry()
    except KeyboardInterrupt:
        client.stop()
        await client.cleanup()
    except Exception as e:
        print(f"Fatal error: {e}")
        update_status(False, error=f"Fatal error: {str(e)}")
        await client.cleanup()
        sys.exit(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Client stopped by user")
        update_status(False, error="Client stopped by user")
        sys.exit(0)
