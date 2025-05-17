#!/bin/bash

# Define paths
REPO_DIR="/home/admin/ElectricNose"
VENV_DIR="$REPO_DIR/DisplayController/venv/bin/activate"
LOG_FILE="$REPO_DIR/iohandler.log"

# Activate the Python environment
if [ -f "$VENV_DIR" ]; then
    source "$VENV_DIR"
else
    echo "$(date): Virtual environment not found, exiting."
    exit 1
fi

# Install dependencies
pip install -r "$REPO_DIR/DisplayController/requirements.txt"

# Run the Python script
echo "$(date): Starting Python script..."
cd "$REPO_DIR"
python3 -m DisplayController.io.io-main
