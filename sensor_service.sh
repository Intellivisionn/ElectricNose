#!/bin/bash

# Define paths
REPO_DIR="/home/admin/ElectricNose-SensorReader"
VENV_DIR="$REPO_DIR/bin/activate"
PYTHON_SCRIPT="$REPO_DIR/sensor.py"
LOG_FILE="/var/log/sensor_service.log"

echo "$(date): Starting sensor service..." >> "$LOG_FILE"

# Try to update the repository (skip if no network)
if ping -q -c 1 -W 1 github.com >/dev/null 2>&1; then
    echo "$(date): Network detected, pulling latest code..." >> "$LOG_FILE"
    git -C "$REPO_DIR" pull >> "$LOG_FILE" 2>&1
else
    echo "$(date): No network, skipping git pull." >> "$LOG_FILE"
fi

# Activate the Python environment
if [ -f "$VENV_DIR" ]; then
    source "$VENV_DIR"
else
    echo "$(date): Virtual environment not found, exiting." >> "$LOG_FILE"
    exit 1
fi

# Install dependencies
pip install -r "$REPO_DIR/requirements.txt" >> "$LOG_FILE" 2>&1

# Run the Python script
echo "$(date): Starting Python script..." >> "$LOG_FILE"
python "$PYTHON_SCRIPT" >> "$LOG_FILE" 2>&1
