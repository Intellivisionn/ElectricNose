#!/bin/bash

echo "Starting Data Reader..."

# Change to project directory
cd /home/pi/ElectricNose-DataReader

# Try to pull updates (only if network is available)
if ping -c 1 github.com &> /dev/null; then
    echo "Network available, pulling latest updates..."
    git pull origin main
else
    echo "No network, using existing version."
fi

# Activate the virtual environment
source /home/admin/data-receiver/bin/activate

# Run the Data Reader
python data_reader.py
