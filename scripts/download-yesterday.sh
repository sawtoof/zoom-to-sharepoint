#!/bin/bash
#
# Downloads Zoom recordings from the previous day
#
# Usage: ./download-yesterday.sh
#
# This script should be scheduled to run daily via cron
# Example crontab entry (runs at 2 AM daily):
#   0 2 * * * /path/to/zoom-to-sharepoint/scripts/download-yesterday.sh
#

# Exit on error
set -e

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Configuration - modify these paths as needed
VENV_DIR="$PROJECT_DIR/venv"
SRC_DIR="$PROJECT_DIR/src"
DOWNLOAD_DIR="$PROJECT_DIR/downloads"
LOG_DIR="$PROJECT_DIR/logs"

# Create directories if they don't exist
mkdir -p "$DOWNLOAD_DIR"
mkdir -p "$LOG_DIR"

# Calculate yesterday's date
YESTERDAY=$(date -d "yesterday" +%Y-%m-%d 2>/dev/null || date -v-1d +%Y-%m-%d)
LOG_FILE="$LOG_DIR/download-$YESTERDAY.log"

# Log start
echo "==================================================" | tee "$LOG_FILE"
echo "Zoom Recording Download Script" | tee -a "$LOG_FILE"
echo "Started at: $(date)" | tee -a "$LOG_FILE"
echo "Downloading recordings for: $YESTERDAY" | tee -a "$LOG_FILE"
echo "==================================================" | tee -a "$LOG_FILE"

# Navigate to source directory
cd "$SRC_DIR"

# Activate virtual environment
if [ -f "$VENV_DIR/bin/activate" ]; then
    source "$VENV_DIR/bin/activate"
    echo "Virtual environment activated" | tee -a "$LOG_FILE"
else
    echo "ERROR: Virtual environment not found at $VENV_DIR" | tee -a "$LOG_FILE"
    exit 1
fi

# Run the application
echo "Running download for $YESTERDAY..." | tee -a "$LOG_FILE"
if python main.py "$YESTERDAY" "$YESTERDAY" --download-only --download-dir "$DOWNLOAD_DIR" 2>&1 | tee -a "$LOG_FILE"; then
    echo "SUCCESS: Download completed for $YESTERDAY" | tee -a "$LOG_FILE"
    EXIT_CODE=0
else
    echo "ERROR: Download failed for $YESTERDAY" | tee -a "$LOG_FILE"
    EXIT_CODE=1
fi

# Deactivate virtual environment
deactivate

# Log completion
echo "Completed at: $(date)" | tee -a "$LOG_FILE"
echo "==================================================" | tee -a "$LOG_FILE"

exit $EXIT_CODE
