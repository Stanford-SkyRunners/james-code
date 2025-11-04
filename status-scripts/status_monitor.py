#!/usr/bin/env python3
"""
Raspberry Pi Status Monitor
Sends email on WiFi connection and periodic status updates every 5 minutes.
"""

import smtplib
import subprocess
import time
import os
import sys
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import json
from dotenv import load_dotenv


class StatusMonitor:
    def __init__(self, config_file=None):
        """Initialize the status monitor with configuration."""
        # Get the repository root directory (parent of status-scripts)
        if config_file is None:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            repo_root = os.path.dirname(script_dir)
            config_file = os.path.join(repo_root, 'config.json')

        # Store repo root for other file paths
        self.repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        # Load environment variables from .env file
        load_dotenv(os.path.join(self.repo_root, '.env'))

        self.config = self.load_config(config_file)
        self.startup_time = datetime.now()

    def load_config(self, config_file):
        """Load configuration from JSON file."""
        try:
            with open(config_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Error: Configuration file not found: {config_file}")
            print("Please create config.json with your email settings.")
            sys.exit(1)
        except json.JSONDecodeError:
            print(f"Error: Invalid JSON in configuration file: {config_file}")
            sys.exit(1)

    def get_hostname(self):
        """Get the Raspberry Pi hostname in user@hostname.local format."""
        try:
            # Get username
            username_result = subprocess.run(['whoami'],
                                           capture_output=True, text=True, timeout=5)
            username = username_result.stdout.strip()

            # Get hostname
            hostname_result = subprocess.run(['hostname'],
                                           capture_output=True, text=True, timeout=5)
            hostname = hostname_result.stdout.strip()

            return f"{username}@{hostname}.local"
        except Exception as e:
            return "Unknown"

    def get_wifi_info(self):
        """Get current WiFi connection information."""
        try:
            # Get SSID
            ssid_result = subprocess.run(['iwgetid', '-r'],
                                        capture_output=True, text=True, timeout=5)
            ssid = ssid_result.stdout.strip() or "Not connected"

            # Get IP address
            ip_result = subprocess.run(['hostname', '-I'],
                                      capture_output=True, text=True, timeout=5)
            ip_address = ip_result.stdout.strip().split()[0] if ip_result.stdout.strip() else "No IP"

            # Get signal strength
            signal_result = subprocess.run(['iwconfig', 'wlan0'],
                                          capture_output=True, text=True, timeout=5)
            signal_strength = "Unknown"
            for line in signal_result.stdout.split('\n'):
                if 'Signal level' in line:
                    signal_strength = line.split('Signal level=')[1].split()[0]
                    break

            return {
                'ssid': ssid,
                'ip_address': ip_address,
                'signal_strength': signal_strength
            }
        except Exception as e:
            return {
                'ssid': 'Error',
                'ip_address': 'Error',
                'signal_strength': f'Error: {str(e)}'
            }

    def get_backend_status(self):
        """Get WebSocket and REST API backend connection status."""
        status_file = os.path.join(self.repo_root, 'websocket_status.json')

        # Check WebSocket status from file
        websocket_status = {
            'connected': False,
            'last_update': 'Never',
            'last_message': 'None',
            'error': None
        }

        try:
            if os.path.exists(status_file):
                with open(status_file, 'r') as f:
                    status = json.load(f)
                    websocket_status = {
                        'connected': status.get('connected', False),
                        'last_update': status.get('last_update', 'Never'),
                        'last_message': status.get('last_message', 'None'),
                        'error': status.get('error', None)
                    }
            else:
                websocket_status['error'] = 'Status file not found'
        except Exception as e:
            websocket_status['error'] = str(e)

        # Check REST API status by pinging health endpoint
        rest_api_status = {
            'connected': False,
            'error': None
        }

        try:
            rest_api_url = self.config.get('backend', {}).get('rest_api_url', 'http://24.144.90.5:8000')
            import urllib.request
            req = urllib.request.Request(f"{rest_api_url}/api/health", method='GET')
            with urllib.request.urlopen(req, timeout=3) as response:
                if response.status == 200:
                    rest_api_status['connected'] = True
        except Exception as e:
            rest_api_status['error'] = str(e)

        return {
            'websocket': websocket_status,
            'rest_api': rest_api_status
        }

    def get_system_metrics(self):
        """Collect comprehensive system metrics."""
        metrics = {}

        # CPU Temperature
        try:
            temp_result = subprocess.run(['vcgencmd', 'measure_temp'],
                                        capture_output=True, text=True, timeout=5)
            temp = temp_result.stdout.strip().replace("temp=", "")
            metrics['cpu_temp'] = temp
        except:
            metrics['cpu_temp'] = "N/A"

        # CPU Usage
        try:
            cpu_result = subprocess.run(['top', '-bn1'],
                                       capture_output=True, text=True, timeout=5)
            for line in cpu_result.stdout.split('\n'):
                if 'Cpu(s)' in line:
                    idle = float(line.split('id,')[0].split()[-1])
                    metrics['cpu_usage'] = f"{100 - idle:.1f}%"
                    break
        except:
            metrics['cpu_usage'] = "N/A"

        # Memory Usage
        try:
            mem_result = subprocess.run(['free', '-h'],
                                       capture_output=True, text=True, timeout=5)
            lines = mem_result.stdout.split('\n')
            if len(lines) > 1:
                mem_line = lines[1].split()
                metrics['memory_total'] = mem_line[1]
                metrics['memory_used'] = mem_line[2]
                metrics['memory_available'] = mem_line[6]
        except:
            metrics['memory_total'] = "N/A"
            metrics['memory_used'] = "N/A"
            metrics['memory_available'] = "N/A"

        # Disk Usage
        try:
            disk_result = subprocess.run(['df', '-h', '/'],
                                        capture_output=True, text=True, timeout=5)
            lines = disk_result.stdout.split('\n')
            if len(lines) > 1:
                disk_line = lines[1].split()
                metrics['disk_total'] = disk_line[1]
                metrics['disk_used'] = disk_line[2]
                metrics['disk_available'] = disk_line[3]
                metrics['disk_usage_percent'] = disk_line[4]
        except:
            metrics['disk_total'] = "N/A"
            metrics['disk_used'] = "N/A"
            metrics['disk_available'] = "N/A"
            metrics['disk_usage_percent'] = "N/A"

        # Uptime
        try:
            uptime_result = subprocess.run(['uptime', '-p'],
                                          capture_output=True, text=True, timeout=5)
            metrics['uptime'] = uptime_result.stdout.strip()
        except:
            metrics['uptime'] = "N/A"

        # Load Average
        try:
            load_result = subprocess.run(['cat', '/proc/loadavg'],
                                        capture_output=True, text=True, timeout=5)
            load_avg = load_result.stdout.strip().split()[:3]
            metrics['load_avg'] = f"{load_avg[0]}, {load_avg[1]}, {load_avg[2]}"
        except:
            metrics['load_avg'] = "N/A"

        return metrics

    def format_connection_email(self, wifi_info):
        """Format the WiFi connection notification email."""
        hostname = self.get_hostname()
        subject = f"🟢 {hostname} Connected to WiFi: {wifi_info['ssid']}"

        # Get backend status
        backend_status = self.get_backend_status()
        backend_icon = "✅" if backend_status['websocket']['connected'] else "❌"
        backend_text = "Connected" if backend_status['websocket']['connected'] else "Disconnected"

        body = f"""
Raspberry Pi WiFi Connection Notification
==========================================

Your Raspberry Pi has successfully connected to WiFi!

Device Information:
-------------------
• Hostname: {hostname}

Connection Details:
-------------------
• Network (SSID): {wifi_info['ssid']}
• IP Address: {wifi_info['ip_address']}
• Signal Strength: {wifi_info['signal_strength']}
• Connection Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Backend Connection:
-------------------
• WebSocket: {backend_icon} {backend_text}
• REST API: {"✅ Connected" if backend_status['rest_api']['connected'] else "❌ Disconnected"}
• Last Update: {backend_status['websocket']['last_update']}
• Last Message: {backend_status['websocket']['last_message']}
{f"• Error: {backend_status['websocket']['error']}" if backend_status['websocket']['error'] else ""}

Status monitoring is now active. You will receive status updates every 5 minutes.

---
Raspberry Pi Status Monitor
"""
        return subject, body

    def format_status_email(self, wifi_info, metrics):
        """Format the periodic status update email."""
        hostname = self.get_hostname()
        subject = f"📊 {hostname} Status Update - {wifi_info['ssid']}"

        # Get backend status
        backend_status = self.get_backend_status()
        backend_icon = "✅" if backend_status['websocket']['connected'] else "❌"
        backend_text = "Connected" if backend_status['websocket']['connected'] else "Disconnected"

        body = f"""
Raspberry Pi Status Update
==========================
Report Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Script Started: {self.startup_time.strftime('%Y-%m-%d %H:%M:%S')}

Device Information:
-------------------
• Hostname: {hostname}

Network Information:
--------------------
• Network (SSID): {wifi_info['ssid']}
• IP Address: {wifi_info['ip_address']}
• Signal Strength: {wifi_info['signal_strength']}

Backend Connection:
-------------------
• WebSocket: {backend_icon} {backend_text}
• REST API: {"✅ Connected" if backend_status['rest_api']['connected'] else "❌ Disconnected"}
• Last Update: {backend_status['websocket']['last_update']}
• Last Message: {backend_status['websocket']['last_message']}
{f"• Error: {backend_status['websocket']['error']}\n" if backend_status['websocket']['error'] else ""}
System Metrics:
---------------
• CPU Temperature: {metrics.get('cpu_temp', 'N/A')}
• CPU Usage: {metrics.get('cpu_usage', 'N/A')}
• Load Average (1m, 5m, 15m): {metrics.get('load_avg', 'N/A')}

Memory:
-------
• Total: {metrics.get('memory_total', 'N/A')}
• Used: {metrics.get('memory_used', 'N/A')}
• Available: {metrics.get('memory_available', 'N/A')}

Disk Usage (/):
---------------
• Total: {metrics.get('disk_total', 'N/A')}
• Used: {metrics.get('disk_used', 'N/A')} ({metrics.get('disk_usage_percent', 'N/A')})
• Available: {metrics.get('disk_available', 'N/A')}

System:
-------
• Uptime: {metrics.get('uptime', 'N/A')}

---
Raspberry Pi Status Monitor
"""
        return subject, body

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

            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Email sent: {subject}")
            return True

        except Exception as e:
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Error sending email: {str(e)}")
            return False

    def wait_for_wifi(self):
        """Wait for WiFi connection to be established and network to be reachable."""
        print("Waiting for WiFi connection...")
        while True:
            wifi_info = self.get_wifi_info()
            if wifi_info['ssid'] != "Not connected" and wifi_info['ip_address'] != "No IP":
                # Verify network is actually reachable by pinging Google DNS
                try:
                    ping_result = subprocess.run(['ping', '-c', '1', '-W', '2', '8.8.8.8'],
                                                capture_output=True, timeout=5)
                    if ping_result.returncode == 0:
                        return wifi_info
                    else:
                        print("WiFi connected but network not reachable yet, waiting...")
                except:
                    print("WiFi connected but network not reachable yet, waiting...")
            time.sleep(5)

    def run(self):
        """Main monitoring loop."""
        print("Raspberry Pi Status Monitor Started")
        print("=" * 50)

        # Wait for WiFi connection
        wifi_info = self.wait_for_wifi()
        print(f"Connected to WiFi: {wifi_info['ssid']}")

        # Send connection notification
        subject, body = self.format_connection_email(wifi_info)
        self.send_email(subject, body)

        # Main monitoring loop - send status every 5 minutes
        interval = 300  # 5 minutes = 300 seconds
        while True:
            # Sleep with countdown
            for remaining in range(interval, 0, -60):
                minutes = remaining // 60
                seconds = remaining % 60
                if minutes > 0:
                    print(f"Next email in: {minutes}m {seconds}s")
                else:
                    print(f"Next email in: {seconds}s")
                time.sleep(min(60, remaining))

            # Get updated information
            wifi_info = self.get_wifi_info()
            metrics = self.get_system_metrics()

            # Send status email
            subject, body = self.format_status_email(wifi_info, metrics)
            self.send_email(subject, body)


if __name__ == "__main__":
    try:
        monitor = StatusMonitor()
        monitor.run()
    except KeyboardInterrupt:
        print("\nStatus monitor stopped by user.")
        sys.exit(0)
    except Exception as e:
        print(f"Fatal error: {str(e)}")
        sys.exit(1)
