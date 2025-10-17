#!/bin/bash

# Raspberry Pi Status Monitor Installation Script

set -e

echo "=========================================="
echo "Raspberry Pi Status Monitor Installation"
echo "=========================================="
echo ""

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    echo "Error: Please do not run this script as root"
    echo "Run it as your normal user: ./install.sh"
    exit 1
fi

# Check if config.json exists
if [ ! -f "/home/james/status-scripts/config.json" ]; then
    echo "Error: config.json not found!"
    echo "Please create config.json from the template:"
    echo "  cp config.json.example config.json"
    echo "  nano config.json"
    echo ""
    echo "Then edit it with your email settings."
    exit 1
fi

# Make the Python script executable
echo "Making status_monitor.py executable..."
chmod +x /home/james/status-scripts/status_monitor.py

# Copy systemd service file
echo "Installing systemd service..."
sudo cp /home/james/status-scripts/status-monitor.service /etc/systemd/system/

# Reload systemd
echo "Reloading systemd..."
sudo systemctl daemon-reload

# Enable the service
echo "Enabling status-monitor service..."
sudo systemctl enable status-monitor.service

# Start the service
echo "Starting status-monitor service..."
sudo systemctl start status-monitor.service

# Check status
echo ""
echo "Installation complete!"
echo ""
echo "Service status:"
sudo systemctl status status-monitor.service --no-pager

echo ""
echo "=========================================="
echo "Useful commands:"
echo "=========================================="
echo "Check status:    sudo systemctl status status-monitor"
echo "View logs:       sudo journalctl -u status-monitor -f"
echo "View log file:   tail -f /home/james/status-scripts/status_monitor.log"
echo "Stop service:    sudo systemctl stop status-monitor"
echo "Restart service: sudo systemctl restart status-monitor"
echo "Disable service: sudo systemctl disable status-monitor"
echo ""
