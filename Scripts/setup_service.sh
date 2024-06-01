#!/bin/bash

# Define variables
REPO_URL="https://github.com/yourusername/yourrepo.git"
CLONE_DIR="/home/$(whoami)/yourrepo"
PYTHON_SCRIPT_PATH="$CLONE_DIR/record_time.py"
SERVICE_FILE_PATH="/etc/systemd/system/record_time.service"
CURRENT_USER=$(whoami)

# Update package list and install git if not already installed
sudo apt-get update
sudo apt-get install -y git

# Ensure Python3 and pip3 are installed
sudo apt-get install -y python3 python3-pip

# Clone the GitHub repository
if [ -d "$CLONE_DIR" ]; then
    rm -rf "$CLONE_DIR"
fi

git clone $REPO_URL $CLONE_DIR

# Ensure the Python script exists
if [ ! -f "$PYTHON_SCRIPT_PATH" ]; then
    echo "Python script not found in the repository!"
    exit 1
fi

# Install any dependencies for the Python script
if [ -f "$CLONE_DIR/requirements.txt" ]; then
    pip3 install -r "$CLONE_DIR/requirements.txt"
else
    echo "No requirements.txt found, skipping dependency installation."
fi

# Make the Python script executable
chmod +x $PYTHON_SCRIPT_PATH

# Create the systemd service file
cat << EOF | sudo tee $SERVICE_FILE_PATH > /dev/null
[Unit]
Description=Record Time Every 5 Seconds
After=network.target

[Service]
ExecStart=/usr/bin/python3 $PYTHON_SCRIPT_PATH
WorkingDirectory=$CLONE_DIR
StandardOutput=inherit
StandardError=inherit
Restart=always
RestartSec=5
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
