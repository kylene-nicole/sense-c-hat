#!/bin/bash

CLONE_DIR="/home/$(whoami)/logging"
PYTHON_SCRIPT_PATH="$CLONE_DIR/update_time.py"
SERVICE_FILE_PATH="/etc/systemd/system/update_time.service"
CURRENT_USER=$(whoami)

# Make the Python script executable
chmod +x $PYTHON_SCRIPT_PATH

# Create the systemd service file
cat << EOF | sudo tee $SERVICE_FILE_PATH > /dev/null
[Unit]
Description=Update the time on the Raspberry Pi on Boot
After=network.target

[Service]
ExecStart=/usr/bin/python3 $PYTHON_SCRIPT_PATH
WorkingDirectory=$CLONE_DIR
StandardOutput=inherit
StandardError=inherit
Restart=always
RestartSec=1200
User=$CURRENT_USER

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd, enable and start the service
sudo systemctl daemon-reload
sudo systemctl enable record_time.service
sudo systemctl start record_time.service

# Check the status of the service
sudo systemctl status record_time.service
