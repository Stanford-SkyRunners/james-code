# Raspberry Pi Status Monitor

Automatically sends email notifications when your Raspberry Pi connects to WiFi, followed by periodic status updates every 5 minutes.

## Features

- Sends email notification immediately upon WiFi connection
- Includes network details (SSID, IP address, signal strength)
- Sends comprehensive status updates every 5 minutes including:
  - CPU temperature and usage
  - Memory usage
  - Disk usage
  - System uptime
  - Load averages
  - Network information
- Automatically starts on boot
- Restarts automatically if it crashes

## Files

- `status_monitor.py` - Main Python script
- `status-monitor.service` - Systemd service file
- `config.json.example` - Example configuration file
- `install.sh` - Installation script
- `README.md` - This file

## Installation

### 1. Configure Email Settings

First, copy the example configuration file:

```bash
cd /home/james/status-scripts
cp config.json.example config.json
nano config.json
```

Edit `config.json` with your email settings:

```json
{
  "email": {
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "from_address": "your-email@gmail.com",
    "to_address": "recipient@example.com",
    "password": "your-app-password-here"
  }
}
```

#### For Gmail Users:

1. Enable 2-factor authentication on your Google account
2. Generate an App Password at: https://myaccount.google.com/apppasswords
3. Use the generated app password in the config file (not your regular password)

#### For Other Email Providers:

Update `smtp_server` and `smtp_port` according to your provider:
- **Outlook/Hotmail**: `smtp.office365.com`, port `587`
- **Yahoo**: `smtp.mail.yahoo.com`, port `587`
- **Custom SMTP**: Use your provider's settings

### 2. Run the Installation Script

Make the install script executable and run it:

```bash
chmod +x install.sh
./install.sh
```

The script will:
- Make the Python script executable
- Install the systemd service
- Enable auto-start on boot
- Start the service immediately

### 3. Verify Installation

Check that the service is running:

```bash
sudo systemctl status status-monitor
```

You should receive your first email shortly!

## Usage

### View Real-time Logs

```bash
# Using journalctl (systemd logs)
sudo journalctl -u status-monitor -f

# Using the log file
tail -f /home/james/status-scripts/status_monitor.log
```

### Control the Service

```bash
# Start the service
sudo systemctl start status-monitor

# Stop the service
sudo systemctl stop status-monitor

# Restart the service
sudo systemctl restart status-monitor

# Check service status
sudo systemctl status status-monitor

# Disable auto-start on boot
sudo systemctl disable status-monitor

# Enable auto-start on boot
sudo systemctl enable status-monitor
```

### Update Configuration

If you need to change email settings:

1. Edit the config file:
   ```bash
   nano /home/james/status-scripts/config.json
   ```

2. Restart the service:
   ```bash
   sudo systemctl restart status-monitor
   ```

## Troubleshooting

### No emails being sent

1. Check the logs:
   ```bash
   sudo journalctl -u status-monitor -n 50
   ```

2. Verify your email credentials in `config.json`

3. For Gmail, ensure you're using an App Password, not your regular password

### Service not starting

1. Check for Python errors:
   ```bash
   python3 /home/james/status-scripts/status_monitor.py
   ```

2. Verify config.json exists and has correct format

### WiFi not detected

1. Verify your WiFi interface name:
   ```bash
   iwconfig
   ```

2. If your WiFi interface is not `wlan0`, you may need to edit the script

## Customization

### Change Update Frequency

Edit `status_monitor.py` and modify this line:

```python
time.sleep(300)  # 5 minutes = 300 seconds
```

Change `300` to your desired interval in seconds:
- 1 minute = 60
- 10 minutes = 600
- 30 minutes = 1800

Then restart the service:
```bash
sudo systemctl restart status-monitor
```

### Add More Metrics

You can add custom metrics by editing the `get_system_metrics()` function in `status_monitor.py`.

## Uninstallation

To completely remove the status monitor:

```bash
# Stop and disable the service
sudo systemctl stop status-monitor
sudo systemctl disable status-monitor

# Remove the service file
sudo rm /etc/systemd/system/status-monitor.service

# Reload systemd
sudo systemctl daemon-reload

# Optionally, remove the scripts directory
rm -rf /home/james/status-scripts
```

## Security Notes

- Keep your `config.json` file secure - it contains your email password
- The config file has restricted permissions (only readable by you)
- Consider using a dedicated email account for system notifications
- Never commit `config.json` to version control

## License

Free to use and modify for personal use.
