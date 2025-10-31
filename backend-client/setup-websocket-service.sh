#!/bin/bash
# Setup script for Vantir WebSocket Client service

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Get the repository root (parent of backend-client)
REPO_ROOT="$(dirname "$SCRIPT_DIR")"

echo "=========================================="
echo "Vantir WebSocket Client Service Setup"
echo "=========================================="
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "❌ Please run as root (use sudo)"
    exit 1
fi

# Install websockets library if not already installed
echo "📦 Installing Python dependencies..."
pip3 install websockets aiohttp

# Make the Python script executable
echo "🔧 Making Python script executable..."
chmod +x "$SCRIPT_DIR/websocket_client.py"

# Generate service file with correct paths
echo "📋 Generating systemd service file..."
cat > /tmp/vantir-websocket-client.service <<EOF
[Unit]
Description=Vantir WebSocket Client for Raspberry Pi
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=$SUDO_USER
WorkingDirectory=$REPO_ROOT
ExecStart=/usr/bin/python3 $SCRIPT_DIR/websocket_client.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Copy service file to systemd directory
cp /tmp/vantir-websocket-client.service /etc/systemd/system/
rm /tmp/vantir-websocket-client.service

# Reload systemd
echo "🔄 Reloading systemd..."
systemctl daemon-reload

# Enable service to start on boot
echo "✅ Enabling service to start on boot..."
systemctl enable vantir-websocket-client.service

# Start the service
echo "🚀 Starting service..."
systemctl start vantir-websocket-client.service

# Check status
echo ""
echo "=========================================="
echo "Service Status:"
echo "=========================================="
systemctl status vantir-websocket-client.service --no-pager

echo ""
echo "=========================================="
echo "✅ Setup Complete!"
echo "=========================================="
echo ""
echo "Useful commands:"
echo "  • Check status:  sudo systemctl status vantir-websocket-client.service"
echo "  • View logs:     sudo journalctl -u vantir-websocket-client.service -f"
echo "  • Restart:       sudo systemctl restart vantir-websocket-client.service"
echo "  • Stop:          sudo systemctl stop vantir-websocket-client.service"
echo "  • Disable:       sudo systemctl disable vantir-websocket-client.service"
echo ""
echo "⚙️  Don't forget to update the backend WebSocket URL in:"
echo "    $REPO_ROOT/config.json"
echo ""
