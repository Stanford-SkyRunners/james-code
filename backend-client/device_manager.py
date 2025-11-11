"""
Device ID Management for Raspberry Pi WebSocket Client

This module handles persistent device identification, MAC address detection,
and device metadata management for the Vantir WebSocket client.
"""

import uuid
import os
import json
import socket
from pathlib import Path
from datetime import datetime


class DeviceManager:
    """Manages device identification and metadata for Raspberry Pi clients."""

    def __init__(self, config_file=None):
        """
        Initialize DeviceManager.

        Args:
            config_file: Path to config.json (optional, for device metadata)
        """
        # Determine repo root (parent of backend-client directory)
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.repo_root = os.path.dirname(self.script_dir)

        # Device ID file in repo root
        self.device_id_file = os.path.join(self.repo_root, '.device_id')

        # Config file
        self.config_file = config_file or os.path.join(self.repo_root, 'config.json')

        # Load or create device ID
        self.device_id = self.get_or_create_device_id()

    def get_or_create_device_id(self):
        """
        Get existing device ID or create a new one.

        Device IDs are persistent UUIDs stored in .device_id file.
        Format: pi-{uuid}

        Returns:
            str: Device ID (e.g., "pi-abc123...")
        """
        if os.path.exists(self.device_id_file):
            try:
                with open(self.device_id_file, 'r') as f:
                    data = json.load(f)
                    device_id = data.get('device_id')
                    if device_id:
                        print(f"📋 Loaded existing device ID: {device_id}")
                        return device_id
            except Exception as e:
                print(f"⚠️  Error reading device ID file: {e}")
                print("   Creating new device ID...")

        # Generate new UUID-based device ID
        device_id = f"pi-{uuid.uuid4()}"

        # Save to file
        try:
            data = {
                'device_id': device_id,
                'created_at': datetime.now().isoformat(),
                'hostname': socket.gethostname()
            }
            with open(self.device_id_file, 'w') as f:
                json.dump(data, f, indent=2)
            print(f"✓ Created new device ID: {device_id}")
        except Exception as e:
            print(f"⚠️  Error saving device ID: {e}")

        return device_id

    def get_mac_address(self):
        """
        Get MAC address from network interface.

        Tries to get MAC address from eth0 or wlan0 using netifaces library.
        Falls back to reading from /sys/class/net if netifaces is unavailable.

        Returns:
            str: MAC address or None if not found
        """
        # Try netifaces library (preferred method)
        try:
            import netifaces

            # Try common interfaces in order of preference
            for interface in ['eth0', 'wlan0', 'en0', 'wlan1']:
                if interface in netifaces.interfaces():
                    addrs = netifaces.ifaddresses(interface)
                    if netifaces.AF_LINK in addrs:
                        mac = addrs[netifaces.AF_LINK][0]['addr']
                        print(f"📡 MAC address from {interface}: {mac}")
                        return mac
        except ImportError:
            print("⚠️  netifaces not installed, trying fallback method...")
        except Exception as e:
            print(f"⚠️  Error getting MAC via netifaces: {e}")

        # Fallback: read from /sys/class/net
        for interface in ['eth0', 'wlan0']:
            try:
                mac_path = f'/sys/class/net/{interface}/address'
                if os.path.exists(mac_path):
                    with open(mac_path, 'r') as f:
                        mac = f.read().strip()
                        print(f"📡 MAC address from {interface}: {mac}")
                        return mac
            except Exception as e:
                continue

        print("⚠️  Could not detect MAC address")
        return None

    def load_device_config(self):
        """
        Load device-specific configuration from config.json.

        Looks for optional 'device' section in config.json:
        {
            "device": {
                "name": "Kitchen Pi",
                "location": "Building A - Kitchen",
                "metadata": {
                    "room": "Kitchen",
                    "floor": "1"
                }
            }
        }

        Returns:
            dict: Device config or defaults
        """
        default_config = {
            'name': f'Raspberry Pi ({socket.gethostname()})',
            'location': 'Unknown',
            'metadata': {}
        }

        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    device_config = config.get('device', {})

                    # Merge with defaults
                    return {
                        'name': device_config.get('name', default_config['name']),
                        'location': device_config.get('location', default_config['location']),
                        'metadata': device_config.get('metadata', {})
                    }
        except Exception as e:
            print(f"⚠️  Error loading device config: {e}")

        return default_config

    def get_device_info(self):
        """
        Get complete device information for registration.

        Returns:
            dict: Device info including:
                - deviceId: Persistent UUID-based ID
                - name: Human-readable device name
                - hostname: System hostname
                - deviceType: Always "raspberry_pi"
                - macAddress: MAC address (if available)
                - location: Physical location
                - metadata: Additional metadata
        """
        device_config = self.load_device_config()
        mac_address = self.get_mac_address()

        device_info = {
            'deviceId': self.device_id,
            'name': device_config['name'],
            'hostname': socket.gethostname(),
            'deviceType': 'raspberry_pi',
            'macAddress': mac_address,
            'location': device_config['location'],
            'metadata': device_config.get('metadata', {})
        }

        return device_info

    def create_registration_message(self):
        """
        Create a registration message for the WebSocket server.

        Returns:
            dict: Registration message ready to be JSON-serialized
        """
        device_info = self.get_device_info()

        return {
            'type': 'register',
            'deviceId': device_info['deviceId'],
            'name': device_info['name'],
            'hostname': device_info['hostname'],
            'deviceType': device_info['deviceType'],
            'macAddress': device_info['macAddress'],
            'metadata': {
                'location': device_info['location'],
                **device_info['metadata']
            }
        }


# Convenience functions for backward compatibility
def get_device_info():
    """
    Backward-compatible function for getting device info.

    Returns:
        dict: Device information
    """
    manager = DeviceManager()
    return manager.get_device_info()


if __name__ == '__main__':
    """Test device manager functionality."""
    print("=== Device Manager Test ===\n")

    manager = DeviceManager()

    print("\n--- Device Information ---")
    info = manager.get_device_info()
    for key, value in info.items():
        print(f"{key}: {value}")

    print("\n--- Registration Message ---")
    reg_msg = manager.create_registration_message()
    print(json.dumps(reg_msg, indent=2))
