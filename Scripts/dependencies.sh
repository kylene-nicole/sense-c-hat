#!/bin/bash

# Update and upgrade the system
sudo apt update && sudo apt upgrade -y

# Download the lg library from GitHub
wget https://github.com/joan2937/lg/archive/master.zip

# Unzip the downloaded file
unzip master.zip

# Navigate to the lg-master directory
cd lg-master

# Install the lg library
sudo make install

# Install the Python library for Raspberry Pi GPIO
sudo apt install -y python3-rpi-lgpio

# Clean up the downloaded zip file and extracted directory
cd ..
rm -rf master.zip lg-master

