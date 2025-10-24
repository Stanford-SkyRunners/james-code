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

# Determine repository root (one level up from this script's directory)
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

# Check if config.json exists
if [ ! -f "$REPO_ROOT/config.json" ]; then
    echo "Error: config.json not found at $REPO_ROOT/config.json"
    echo "Please create config.json from the template:"
    echo "  cp $REPO_ROOT/config.json.example $REPO_ROOT/config.json"
    echo "  nano $REPO_ROOT/config.json"
    echo ""
    echo "Then edit it with your username/repo and email settings."
    exit 1
fi

# Make the Python script executable
echo "Making status_monitor.py executable..."
chmod +x "$REPO_ROOT/status-scripts/status_monitor.py"

# Copy systemd service file
echo "Installing systemd service..."
# Fill placeholders in the service template using values from config.json.
# Prefer jq; fall back to python3; otherwise use the current user.
REPO_DIR="$REPO_ROOT"
USER_NAME=""
if command -v jq >/dev/null 2>&1; then
    USER_NAME=$(jq -r '.username' "$REPO_ROOT/config.json" 2>/dev/null || true)
fi
if [ -z "$USER_NAME" ] && command -v python3 >/dev/null 2>&1; then
    USER_NAME=$(python3 -c "import json,sys;print(json.load(open('$REPO_ROOT/config.json')).get('username',''))" 2>/dev/null || true)
fi
if [ -z "$USER_NAME" ]; then
    echo "Warning: could not read 'username' from config.json; falling back to current user ($(whoami))."
    USER_NAME="$(whoami)"
fi

# Substitute placeholders and write the unit file
sed \
  -e "s|__USER__|${USER_NAME}|g" \
  -e "s|__REPO_ROOT__|${REPO_DIR}|g" \
  "$REPO_ROOT/status-scripts/status-monitor.service" | sudo tee /etc/systemd/system/status-monitor.service >/dev/null

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
