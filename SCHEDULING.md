# Scheduling Automated Downloads

This guide shows how to schedule the application to run automatically using cron (Linux/Mac) or Task Scheduler (Windows).

## Daily Download of Previous Day's Recordings

### Option 1: Using a Shell Script with Dynamic Dates (Linux/Mac)

Create a wrapper script that calculates yesterday's date and runs the application.

#### 1. Create the wrapper script

Create a file named `download-yesterday.sh`:

```bash
#!/bin/bash

# Navigate to the project directory
cd /path/to/zoom-to-sharepoint/src

# Activate virtual environment
source ../venv/bin/activate

# Calculate yesterday's date
YESTERDAY=$(date -d "yesterday" +%Y-%m-%d)

# Run the application for yesterday's recordings
python main.py "$YESTERDAY" "$YESTERDAY" --download-only --download-dir /path/to/recordings

# Deactivate virtual environment
deactivate

# Optional: Log the completion
echo "$(date): Completed download for $YESTERDAY" >> /var/log/zoom-download.log
```

#### 2. Make the script executable

```bash
chmod +x download-yesterday.sh
```

#### 3. Test the script

```bash
./download-yesterday.sh
```

#### 4. Schedule with cron

Open your crontab:

```bash
crontab -e
```

Add a line to run the script daily at 2 AM:

```cron
# Download yesterday's Zoom recordings every day at 2 AM
0 2 * * * /path/to/zoom-to-sharepoint/download-yesterday.sh

# Alternative: Run at 6 AM on weekdays only
0 6 * * 1-5 /path/to/zoom-to-sharepoint/download-yesterday.sh
```

### Option 2: Using a PowerShell Script (Windows)

Create a wrapper script that calculates yesterday's date and runs the application.

#### 1. Create the wrapper script

Create a file named `download-yesterday.ps1`:

```powershell
# Set error action preference
$ErrorActionPreference = "Stop"

# Navigate to the project directory
Set-Location "D:\Work\zoom-to-sharepoint\src"

# Activate virtual environment
& "..\venv\Scripts\Activate.ps1"

# Calculate yesterday's date
$yesterday = (Get-Date).AddDays(-1).ToString("yyyy-MM-dd")

# Run the application for yesterday's recordings
python main.py $yesterday $yesterday --download-only --download-dir "D:\ZoomRecordings"

# Deactivate virtual environment
deactivate

# Log the completion
$logMessage = "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss'): Completed download for $yesterday"
Add-Content -Path "D:\Logs\zoom-download.log" -Value $logMessage
```

#### 2. Test the script

```powershell
.\download-yesterday.ps1
```

#### 3. Schedule with Task Scheduler

**Using PowerShell:**

```powershell
# Create a scheduled task to run daily at 2 AM
$action = New-ScheduledTaskAction -Execute "PowerShell.exe" `
    -Argument "-ExecutionPolicy Bypass -File D:\Work\zoom-to-sharepoint\download-yesterday.ps1"

$trigger = New-ScheduledTaskTrigger -Daily -At 2am

$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -DontStopOnIdleEnd

$principal = New-ScheduledTaskPrincipal -UserId "DOMAIN\Username" -RunLevel Highest

Register-ScheduledTask -TaskName "Zoom Recording Download" `
    -Action $action `
    -Trigger $trigger `
    -Settings $settings `
    -Principal $principal `
    -Description "Downloads previous day's Zoom recordings"
```

**Using Task Scheduler GUI:**

1. Open Task Scheduler
2. Click "Create Task"
3. **General tab:**
   - Name: "Zoom Recording Download"
   - Run whether user is logged on or not
   - Run with highest privileges
4. **Triggers tab:**
   - New → Daily
   - Start time: 2:00 AM
   - Recur every: 1 days
5. **Actions tab:**
   - New → Start a program
   - Program: `PowerShell.exe`
   - Arguments: `-ExecutionPolicy Bypass -File "D:\Work\zoom-to-sharepoint\download-yesterday.ps1"`
6. **Settings tab:**
   - Allow task to be run on demand
   - If task fails, restart every: 10 minutes
   - Attempt to restart up to: 3 times

## Alternative: Upload to SharePoint Instead of Download-Only

If you want to automatically upload to SharePoint instead of just downloading, modify the scripts:

### Linux/Mac (upload-yesterday.sh)

```bash
#!/bin/bash

cd /path/to/zoom-to-sharepoint/src
source ../venv/bin/activate

YESTERDAY=$(date -d "yesterday" +%Y-%m-%d)

# Remove --download-only flag to enable SharePoint upload
python main.py "$YESTERDAY" "$YESTERDAY"

deactivate
echo "$(date): Completed upload for $YESTERDAY" >> /var/log/zoom-upload.log
```

### Windows (upload-yesterday.ps1)

```powershell
Set-Location "D:\Work\zoom-to-sharepoint\src"
& "..\venv\Scripts\Activate.ps1"

$yesterday = (Get-Date).AddDays(-1).ToString("yyyy-MM-dd")

# Remove --download-only flag to enable SharePoint upload
python main.py $yesterday $yesterday

deactivate
Add-Content -Path "D:\Logs\zoom-upload.log" `
    -Value "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss'): Completed upload for $yesterday"
```

## Weekly Downloads (e.g., Every Monday for Previous Week)

### Linux/Mac (download-last-week.sh)

```bash
#!/bin/bash

cd /path/to/zoom-to-sharepoint/src
source ../venv/bin/activate

# Calculate last Monday and Sunday
LAST_MONDAY=$(date -d "last monday -7 days" +%Y-%m-%d)
LAST_SUNDAY=$(date -d "last sunday" +%Y-%m-%d)

python main.py "$LAST_MONDAY" "$LAST_SUNDAY" --download-only --download-dir /path/to/recordings

deactivate
echo "$(date): Completed download for week $LAST_MONDAY to $LAST_SUNDAY" >> /var/log/zoom-download.log
```

Cron entry (runs every Monday at 3 AM):

```cron
0 3 * * 1 /path/to/zoom-to-sharepoint/download-last-week.sh
```

### Windows (download-last-week.ps1)

```powershell
Set-Location "D:\Work\zoom-to-sharepoint\src"
& "..\venv\Scripts\Activate.ps1"

# Calculate last week's date range
$today = Get-Date
$lastMonday = $today.AddDays(-($today.DayOfWeek.value__ + 6))
$lastSunday = $lastMonday.AddDays(6)

$fromDate = $lastMonday.ToString("yyyy-MM-dd")
$toDate = $lastSunday.ToString("yyyy-MM-dd")

python main.py $fromDate $toDate --download-only --download-dir "D:\ZoomRecordings"

deactivate
Add-Content -Path "D:\Logs\zoom-download.log" `
    -Value "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss'): Completed download for week $fromDate to $toDate"
```

## Monthly Downloads (First Day of Month for Previous Month)

### Linux/Mac (download-last-month.sh)

```bash
#!/bin/bash

cd /path/to/zoom-to-sharepoint/src
source ../venv/bin/activate

# Calculate first and last day of previous month
FIRST_DAY=$(date -d "$(date +%Y-%m-01) -1 month" +%Y-%m-01)
LAST_DAY=$(date -d "$(date +%Y-%m-01) -1 day" +%Y-%m-%d)

python main.py "$FIRST_DAY" "$LAST_DAY" --download-only --download-dir /path/to/recordings

deactivate
echo "$(date): Completed download for month $FIRST_DAY to $LAST_DAY" >> /var/log/zoom-download.log
```

Cron entry (runs on the first day of each month at 4 AM):

```cron
0 4 1 * * /path/to/zoom-to-sharepoint/download-last-month.sh
```

## Error Handling and Notifications

### Add Email Notifications (Linux/Mac)

Install `mailutils` or `sendmail`, then modify the script:

```bash
#!/bin/bash

cd /path/to/zoom-to-sharepoint/src
source ../venv/bin/activate

YESTERDAY=$(date -d "yesterday" +%Y-%m-%d)
LOG_FILE="/tmp/zoom-download-$YESTERDAY.log"

# Run the application and capture output
python main.py "$YESTERDAY" "$YESTERDAY" --download-only --download-dir /path/to/recordings > "$LOG_FILE" 2>&1

# Check exit code
if [ $? -eq 0 ]; then
    echo "Success: Zoom recordings downloaded for $YESTERDAY" | mail -s "Zoom Download Success" your@email.com
else
    echo "Failed to download Zoom recordings for $YESTERDAY. See attached log." | mail -s "Zoom Download FAILED" -A "$LOG_FILE" your@email.com
fi

deactivate
```

### Add Email Notifications (Windows)

```powershell
Set-Location "D:\Work\zoom-to-sharepoint\src"
& "..\venv\Scripts\Activate.ps1"

$yesterday = (Get-Date).AddDays(-1).ToString("yyyy-MM-dd")
$logFile = "D:\Logs\zoom-download-$yesterday.log"

# Run the application and capture output
python main.py $yesterday $yesterday --download-only --download-dir "D:\ZoomRecordings" *> $logFile

# Check if successful
if ($LASTEXITCODE -eq 0) {
    $subject = "Zoom Download Success - $yesterday"
    $body = "Successfully downloaded Zoom recordings for $yesterday"
} else {
    $subject = "Zoom Download FAILED - $yesterday"
    $body = "Failed to download recordings. Check log at: $logFile"
}

# Send email using Send-MailMessage
Send-MailMessage -From "automation@company.com" `
    -To "admin@company.com" `
    -Subject $subject `
    -Body $body `
    -SmtpServer "smtp.company.com" `
    -Attachments $logFile

deactivate
```

## Common Cron Schedule Examples

```cron
# Daily at 2 AM
0 2 * * * /path/to/script.sh

# Every weekday at 6 AM
0 6 * * 1-5 /path/to/script.sh

# Every Monday at 3 AM
0 3 * * 1 /path/to/script.sh

# First day of every month at 4 AM
0 4 1 * * /path/to/script.sh

# Every 6 hours
0 */6 * * * /path/to/script.sh

# Every day at 2 AM and 2 PM
0 2,14 * * * /path/to/script.sh
```

## Best Practices

1. **Timing**: Schedule downloads to run during off-peak hours (e.g., 2-4 AM)

2. **Delay**: Wait at least a few hours after midnight to ensure all recordings are processed by Zoom

3. **Logging**: Always log execution to help with troubleshooting
   ```bash
   python main.py ... >> /var/log/zoom-download.log 2>&1
   ```

4. **Virtual Environment**: Always activate the virtual environment in scripts

5. **Absolute Paths**: Use absolute paths in cron jobs (cron has limited PATH)

6. **Error Handling**: Include error notification mechanisms

7. **Test First**: Always test scripts manually before scheduling

8. **Storage**: Monitor disk space in the download directory

9. **Retention**: Implement a retention policy to clean up old downloads
   ```bash
   # Delete recordings older than 90 days
   find /path/to/recordings -name "*.mp4" -mtime +90 -delete
   ```

10. **Permissions**: Ensure the user running the cron job has:
    - Read access to `.env` file
    - Write access to download directory
    - Execute permission on Python and scripts

## Troubleshooting Scheduled Jobs

### Cron issues (Linux/Mac)

```bash
# Check if cron is running
systemctl status cron

# View cron logs
tail -f /var/log/syslog | grep CRON

# Test script with same environment as cron
env -i /bin/bash --noprofile --norc /path/to/script.sh
```

### Task Scheduler issues (Windows)

1. Check "Task Scheduler Library" → "History" tab
2. View "Last Run Result" (0x0 = success)
3. Run manually: Right-click task → "Run"
4. Check Windows Event Viewer → "Windows Logs" → "Application"

## Example: Complete Daily Download Setup

**File: `/home/user/zoom-automation/daily-download.sh`**

```bash
#!/bin/bash
set -e  # Exit on error

# Configuration
PROJECT_DIR="/home/user/zoom-to-sharepoint"
VENV_DIR="$PROJECT_DIR/venv"
DOWNLOAD_DIR="/mnt/storage/zoom-recordings"
LOG_DIR="/var/log/zoom-automation"
RETENTION_DAYS=90

# Create directories if they don't exist
mkdir -p "$DOWNLOAD_DIR"
mkdir -p "$LOG_DIR"

# Calculate yesterday's date
YESTERDAY=$(date -d "yesterday" +%Y-%m-%d)
LOG_FILE="$LOG_DIR/download-$YESTERDAY.log"

# Log start
echo "==================================================" | tee -a "$LOG_FILE"
echo "Started at: $(date)" | tee -a "$LOG_FILE"
echo "Downloading recordings for: $YESTERDAY" | tee -a "$LOG_FILE"
echo "==================================================" | tee -a "$LOG_FILE"

# Navigate and activate
cd "$PROJECT_DIR/src"
source "$VENV_DIR/bin/activate"

# Run the application
if python main.py "$YESTERDAY" "$YESTERDAY" --download-only --download-dir "$DOWNLOAD_DIR" 2>&1 | tee -a "$LOG_FILE"; then
    echo "SUCCESS: Download completed" | tee -a "$LOG_FILE"
    EXIT_CODE=0
else
    echo "ERROR: Download failed" | tee -a "$LOG_FILE"
    EXIT_CODE=1
fi

# Cleanup old recordings
echo "Cleaning up recordings older than $RETENTION_DAYS days..." | tee -a "$LOG_FILE"
find "$DOWNLOAD_DIR" -name "*.mp4" -mtime +$RETENTION_DAYS -delete
find "$DOWNLOAD_DIR" -name "*.m4a" -mtime +$RETENTION_DAYS -delete

# Cleanup old logs
find "$LOG_DIR" -name "*.log" -mtime +30 -delete

# Deactivate
deactivate

# Log completion
echo "Completed at: $(date)" | tee -a "$LOG_FILE"
echo "==================================================" | tee -a "$LOG_FILE"

exit $EXIT_CODE
```

**Crontab entry:**

```cron
# Download yesterday's Zoom recordings daily at 2 AM
0 2 * * * /home/user/zoom-automation/daily-download.sh
```
