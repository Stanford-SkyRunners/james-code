#!/bin/bash
# Setup script for Vantir WebSocket Client service

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
pip3 install websockets

# Make the Python script executable
echo "🔧 Making Python script executable..."
chmod +x /home/james/skyrunners/backend-client/websocket_client.py

# Copy service file to systemd directory
echo "📋 Installing systemd service..."
cp /home/james/skyrunners/services/vantir-websocket-client.service /etc/systemd/system/

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
echo "    /home/james/skyrunners/config.json"
echo ""
