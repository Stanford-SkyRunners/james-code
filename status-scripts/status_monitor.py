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


class StatusMonitor:
    def __init__(self, config_file=None):
        """Initialize the status monitor with configuration.

        By default the monitor looks for `config.json` in the repository root
        (one directory up from this script's parent). This avoids hard-coding
        the username or repo path in the source.
        """
        if config_file is None:
            # repo root is one level up from the directory that contains this script
            repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
            config_file = os.path.join(repo_root, 'config.json')

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
        subject = f"🟢 Raspberry Pi Connected to WiFi: {wifi_info['ssid']}"

        body = f"""
Raspberry Pi WiFi Connection Notification
==========================================

Your Raspberry Pi has successfully connected to WiFi!

Connection Details:
-------------------
• Network (SSID): {wifi_info['ssid']}
• IP Address: {wifi_info['ip_address']}
• Signal Strength: {wifi_info['signal_strength']}
• Connection Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Status monitoring is now active. You will receive status updates every 5 minutes.

---
Raspberry Pi Status Monitor
"""
        return subject, body

    def format_status_email(self, wifi_info, metrics):
        """Format the periodic status update email."""
        subject = f"📊 Pi Status Update - {wifi_info['ssid']}"

        body = f"""
Raspberry Pi Status Update
==========================
Report Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Script Started: {self.startup_time.strftime('%Y-%m-%d %H:%M:%S')}

Network Information:
--------------------
• Network (SSID): {wifi_info['ssid']}
• IP Address: {wifi_info['ip_address']}
• Signal Strength: {wifi_info['signal_strength']}

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
        """Send email using SMTP."""
        try:
            msg = MIMEMultipart()
            msg['From'] = self.config['email']['from_address']
            msg['To'] = self.config['email']['to_address']
            msg['Subject'] = subject

            msg.attach(MIMEText(body, 'plain'))

            # Connect to SMTP server
            server = smtplib.SMTP(self.config['email']['smtp_server'],
                                 self.config['email']['smtp_port'])
            server.starttls()
            server.login(self.config['email']['from_address'],
                        self.config['email']['password'])

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
