#!/bin/bash

# Raspberry Pi Status Monitor Installation Script

set -e

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Get the repository root (parent of status-scripts)
REPO_ROOT="$(dirname "$SCRIPT_DIR")"

echo "=========================================="
echo "Raspberry Pi Status Monitor Installation"
echo "=========================================="
echo ""

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    echo "Error: Please do not run this script as root"
    echo "Run it as your normal user: ./setup-status-monitor.sh"
    exit 1
fi

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip3 install python-dotenv --break-system-packages

# Check if config.json exists
if [ ! -f "$REPO_ROOT/config.json" ]; then
    echo "Error: config.json not found!"
    echo "Please create and configure config.json first:"
    echo "  nano $REPO_ROOT/config.json"
    echo ""
    echo "See README.md for configuration instructions."
    exit 1
fi

# Check if .env exists
if [ ! -f "$REPO_ROOT/.env" ]; then
    echo "Error: .env file not found!"
    echo "Please create .env file with your email password:"
    echo "  cp $REPO_ROOT/.env.example $REPO_ROOT/.env"
    echo "  nano $REPO_ROOT/.env"
    echo ""
    exit 1
fi

# Make the Python script executable
echo "Making status_monitor.py executable..."
chmod +x "$SCRIPT_DIR/status_monitor.py"

# Generate systemd service file with correct paths
echo "Generating systemd service file..."
cat > /tmp/status-monitor.service <<EOF
[Unit]
Description=Raspberry Pi Status Monitor
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$REPO_ROOT
ExecStart=/usr/bin/python3 -u $SCRIPT_DIR/status_monitor.py
Restart=always
RestartSec=10
StandardOutput=append:$REPO_ROOT/status_monitor.log
StandardError=append:$REPO_ROOT/status_monitor.log

[Install]
WantedBy=multi-user.target
EOF

# Copy systemd service file
echo "Installing systemd service..."
sudo cp /tmp/status-monitor.service /etc/systemd/system/
rm /tmp/status-monitor.service

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
echo "View log file:   tail -f $REPO_ROOT/status_monitor.log"
echo "Stop service:    sudo systemctl stop status-monitor"
echo "Restart service: sudo systemctl restart status-monitor"
echo "Disable service: sudo systemctl disable status-monitor"
echo ""
