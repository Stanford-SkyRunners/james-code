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
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from gpiozero import LED
import time
from dotenv import load_dotenv
from device_manager import DeviceManager

# Load configuration
# Get the repository root directory (parent of backend-client)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(SCRIPT_DIR)
CONFIG_FILE = os.path.join(REPO_ROOT, 'config.json')
STATUS_FILE = os.path.join(REPO_ROOT, 'websocket_status.json')

# Load environment variables from .env file
load_dotenv(os.path.join(REPO_ROOT, '.env'))

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
    def __init__(self, websocket_url, rest_api_url, config):
        self.websocket_url = websocket_url
        self.rest_api_url = rest_api_url
        self.websocket = None
        self.should_reconnect = True

        # Initialize device manager
        self.device_manager = DeviceManager(config_file=CONFIG_FILE)
        self.device_info = self.device_manager.get_device_info()

        self.session = None
        self.heartbeat_task = None
        self.heartbeat_interval = 30  # Send heartbeat every 30 seconds
        self.config = config
        self.registered = False  # Track if device is registered with server

        # Initialize LED if enabled
        self.led = None
        led_config = config.get('led', {})
        if led_config.get('enabled', False):
            try:
                gpio_pin = led_config.get('gpio_pin', 17)
                # active_high=False means LED is wired active low (LOW = ON)
                self.led = LED(gpio_pin, active_high=False)
                self.led.off()  # Ensure LED starts in OFF state
                print(f"✓ LED initialized on GPIO pin {gpio_pin} (active low)")
            except Exception as e:
                print(f"⚠️  Failed to initialize LED: {e}")
                self.led = None

    async def check_health(self):
        """Check backend health status."""
        try:
            if not self.session:
                self.session = aiohttp.ClientSession()

            url = f"{self.rest_api_url}/api/health"
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
        """Send periodic heartbeat messages to server."""
        while self.websocket and not self.websocket.closed:
            try:
                await asyncio.sleep(self.heartbeat_interval)

                heartbeat_msg = {
                    'type': 'heartbeat',
                    'deviceId': self.device_info['deviceId'],
                    'timestamp': datetime.now().isoformat()
                }

                await self.websocket.send(json.dumps(heartbeat_msg))
                print(f"💓 Heartbeat sent")

            except websockets.exceptions.ConnectionClosed:
                print("⚠️  Heartbeat stopped - connection closed")
                break
            except Exception as e:
                print(f"⚠️  Heartbeat error: {e}")
                break

    async def fetch_waypoints(self):
        """Fetch all waypoints from REST API."""
        try:
            if not self.session:
                self.session = aiohttp.ClientSession()

            url = f"{self.rest_api_url}/api/points"
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

    async def blink_led(self, duration=None):
        """
        Turn on LED for specified duration, then turn it off.

        Args:
            duration: Time in seconds to keep LED on (defaults to config value)
        """
        if not self.led:
            return

        try:
            if duration is None:
                duration = self.config.get('led', {}).get('blink_duration', 3)

            print(f"💡 Turning LED ON for {duration} seconds")
            self.led.on()
            await asyncio.sleep(duration)
            self.led.off()
            print(f"💡 LED OFF")
        except Exception as e:
            print(f"⚠️  LED control error: {e}")

    def send_email(self, subject, body):
        """Send email using SMTP configuration from config.json and .env."""
        try:
            # Get email credentials from environment variables, fallback to config for backward compatibility
            from_address = os.getenv('EMAIL_FROM_ADDRESS', self.config['email'].get('from_address', ''))
            to_address = os.getenv('EMAIL_TO_ADDRESS', self.config['email'].get('to_address', ''))
            password = os.getenv('EMAIL_PASSWORD', self.config['email'].get('password', ''))

            msg = MIMEMultipart()
            msg['From'] = from_address
            msg['To'] = to_address
            msg['Subject'] = subject

            msg.attach(MIMEText(body, 'plain'))

            # Connect to SMTP server
            server = smtplib.SMTP(self.config['email']['smtp_server'],
                                 self.config['email']['smtp_port'])
            server.starttls()
            server.login(from_address, password)

            # Send email
            server.send_message(msg)
            server.quit()

            print(f"✅ Email sent successfully: {subject}")
            return True

        except Exception as e:
            print(f"❌ Error sending email: {str(e)}")
            return False

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

                # Send confirmation back to server
                confirmation = {
                    'type': 'launch_confirmation',
                    'deviceId': self.device_info['deviceId'],
                    'waypointId': waypoint_id,
                    'status': 'started',
                    'timestamp': datetime.now().isoformat()
                }
                await self.websocket.send(json.dumps(confirmation))
                print(f"✓ Launch confirmation sent")

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

            elif msg_type == 'registration_confirmed':
                print(f"✅ Device registration confirmed by server")
                self.registered = True
                update_status(True, msg_type)

            elif msg_type == 'ping':
                # Respond to ping with pong
                pong_msg = {
                    'type': 'pong',
                    'deviceId': self.device_info['deviceId'],
                    'timestamp': datetime.now().isoformat()
                }
                await self.websocket.send(json.dumps(pong_msg))
                print(f"🏓 Pong sent in response to ping")
                update_status(True, msg_type)

            elif msg_type == 'send_test_email':
                print(f"📧 TEST EMAIL REQUEST RECEIVED")
                sender = data.get('sender', 'Frontend')
                request_time = data.get('timestamp', datetime.now().isoformat())

                # Turn on LED immediately (non-blocking)
                asyncio.create_task(self.blink_led())

                # Format email with persistent device ID
                subject = "🧪 Test Email from Raspberry Pi"
                body = f"""
Test Email Triggered from Frontend
===================================

This email was triggered by a button click in the frontend!

Request Details:
----------------
• Sender: {sender}
• Request Time: {request_time}
• Device ID: {self.device_info['deviceId']}
• Device Name: {self.device_info['name']}
• Hostname: {self.device_info['hostname']}
• Device Type: {self.device_info['deviceType']}
• Location: {self.device_info['location']}

Communication Flow:
-------------------
1. Frontend button clicked ✅
2. Frontend → Backend request sent ✅
3. Backend → Raspberry Pi WebSocket message ✅
4. Raspberry Pi → LED turned on ✅
5. Raspberry Pi → Email sent ✅

Your bidirectional communication is working perfectly!

---
Raspberry Pi WebSocket Client
"""

                # Send email in background (non-blocking)
                loop = asyncio.get_event_loop()
                loop.run_in_executor(None, self.send_email, subject, body)

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

                # STEP 1: Send registration message immediately
                registration_msg = self.device_manager.create_registration_message()
                await websocket.send(json.dumps(registration_msg))
                print(f"📤 Sent registration as: {self.device_info['deviceId']} ({self.device_info['name']})")

                # STEP 2: Wait for registration confirmation (with timeout)
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                    response_data = json.loads(response)

                    if response_data.get('type') == 'registration_confirmed':
                        print(f"✅ Registration confirmed by server!")
                        self.registered = True
                    else:
                        print(f"⚠️  Unexpected response: {response_data.get('type')}")
                        # Still process the message
                        await self.handle_message(response)

                except asyncio.TimeoutError:
                    print(f"⚠️  Registration confirmation timeout (continuing anyway)")
                    self.registered = False

                # STEP 3: Start heartbeat task
                if self.heartbeat_task:
                    self.heartbeat_task.cancel()
                self.heartbeat_task = asyncio.create_task(self.send_heartbeat())
                print(f"💓 Heartbeat task started (interval: {self.heartbeat_interval}s)")

                # STEP 4: Listen for messages
                async for message in websocket:
                    await self.handle_message(message)

        except websockets.exceptions.ConnectionClosed:
            print("⚠️  WebSocket connection closed by server")
            update_status(False, error="Connection closed by server")

            # Cancel heartbeat task
            if self.heartbeat_task:
                self.heartbeat_task.cancel()
                self.heartbeat_task = None

        except Exception as e:
            print(f"❌ Connection error: {e}")
            update_status(False, error=str(e))

            # Cancel heartbeat task
            if self.heartbeat_task:
                self.heartbeat_task.cancel()
                self.heartbeat_task = None

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
        if self.led:
            self.led.off()
            self.led.close()
            print("✓ LED cleaned up")

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
    client = VantirClient(websocket_url, rest_api_url, config)

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
