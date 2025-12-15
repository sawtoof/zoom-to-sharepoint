# Automation Scripts

This directory contains ready-to-use scripts for automating Zoom recording downloads and uploads.

## Available Scripts

### Linux/Mac Scripts

- **`download-yesterday.sh`** - Downloads recordings from the previous day (download-only mode)
- **`upload-yesterday.sh`** - Downloads and uploads recordings from the previous day to SharePoint

### Windows Scripts

- **`download-yesterday.ps1`** - Downloads recordings from the previous day (download-only mode)
- **`upload-yesterday.ps1`** - Downloads and uploads recordings from the previous day to SharePoint

## Quick Start

### Linux/Mac

1. Make the script executable:
   ```bash
   chmod +x scripts/download-yesterday.sh
   ```

2. Test the script:
   ```bash
   ./scripts/download-yesterday.sh
   ```

3. Schedule with cron (runs daily at 2 AM):
   ```bash
   crontab -e
   ```

   Add this line:
   ```cron
   0 2 * * * /full/path/to/zoom-to-sharepoint/scripts/download-yesterday.sh
   ```

### Windows

1. Test the script:
   ```powershell
   .\scripts\download-yesterday.ps1
   ```

2. Schedule with Task Scheduler:
   ```powershell
   $action = New-ScheduledTaskAction -Execute "PowerShell.exe" `
       -Argument "-ExecutionPolicy Bypass -File C:\path\to\zoom-to-sharepoint\scripts\download-yesterday.ps1"

   $trigger = New-ScheduledTaskTrigger -Daily -At 2am

   Register-ScheduledTask -TaskName "Zoom Recording Download" `
       -Action $action `
       -Trigger $trigger `
       -RunLevel Highest
   ```

## Script Features

All scripts include:
- ✅ Automatic date calculation (yesterday's date)
- ✅ Virtual environment activation
- ✅ Detailed logging to `logs/` directory
- ✅ Error handling and exit codes
- ✅ Timestamps for start and completion

## Logs

Logs are saved to the `logs/` directory with filenames like:
- `download-2024-12-12.log`
- `upload-2024-12-12.log`

## Customization

You can modify the following variables in each script:

### Bash Scripts
```bash
VENV_DIR="$PROJECT_DIR/venv"           # Virtual environment location
SRC_DIR="$PROJECT_DIR/src"             # Source code location
DOWNLOAD_DIR="$PROJECT_DIR/downloads"  # Download directory
LOG_DIR="$PROJECT_DIR/logs"            # Log directory
```

### PowerShell Scripts
```powershell
$VenvDir = Join-Path $ProjectDir "venv"
$SrcDir = Join-Path $ProjectDir "src"
$DownloadDir = Join-Path $ProjectDir "downloads"
$LogDir = Join-Path $ProjectDir "logs"
```

## Advanced Usage

For more advanced scheduling options (weekly, monthly, with email notifications, etc.), see the main [SCHEDULING.md](../SCHEDULING.md) documentation.

## Troubleshooting

### Script doesn't run in cron
- Use absolute paths in the script
- Ensure the script has execute permissions (`chmod +x`)
- Check cron logs: `tail -f /var/log/syslog | grep CRON`

### PowerShell script fails in Task Scheduler
- Set "Run whether user is logged on or not"
- Check "Run with highest privileges"
- Ensure execution policy allows scripts: `Set-ExecutionPolicy RemoteSigned`

### Virtual environment not found
- Ensure you've created the virtual environment: `python -m venv venv`
- Check the path in the script matches your setup

### Logs not being created
- Ensure the `logs/` directory exists or the script has permission to create it
- Check disk space
