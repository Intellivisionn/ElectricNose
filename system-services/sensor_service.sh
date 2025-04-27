#!/bin/bash

# Define paths
REPO_DIR="/home/admin/ElectricNose/SensorReader"
VENV_DIR="$REPO_DIR/venv/bin/activate"
PYTHON_SCRIPT="$REPO_DIR/main.py"
LOG_FILE="$REPO_DIR/sensor_service.log"

echo "$(date): Starting sensor service..." >> "$LOG_FILE"

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
