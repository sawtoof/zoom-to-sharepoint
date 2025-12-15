#
# Downloads Zoom recordings from the previous day
#
# Usage: .\download-yesterday.ps1
#
# This script should be scheduled to run daily via Task Scheduler
#

# Set error action preference
$ErrorActionPreference = "Stop"

# Get the directory where this script is located
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectDir = Split-Path -Parent $ScriptDir

# Configuration - modify these paths as needed
$VenvDir = Join-Path $ProjectDir "venv"
$SrcDir = Join-Path $ProjectDir "src"
$DownloadDir = Join-Path $ProjectDir "downloads"
$LogDir = Join-Path $ProjectDir "logs"

# Create directories if they don't exist
New-Item -ItemType Directory -Force -Path $DownloadDir | Out-Null
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

# Calculate yesterday's date
$yesterday = (Get-Date).AddDays(-1).ToString("yyyy-MM-dd")
$logFile = Join-Path $LogDir "download-$yesterday.log"

# Log start
$separator = "=" * 50
$logStart = @"
$separator
Zoom Recording Download Script
Started at: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')
Downloading recordings for: $yesterday
$separator
"@
$logStart | Tee-Object -FilePath $logFile

# Navigate to source directory
Set-Location $SrcDir

# Activate virtual environment
$activateScript = Join-Path $VenvDir "Scripts\Activate.ps1"
if (Test-Path $activateScript) {
    & $activateScript
    "Virtual environment activated" | Tee-Object -FilePath $logFile -Append
} else {
    "ERROR: Virtual environment not found at $VenvDir" | Tee-Object -FilePath $logFile -Append
    exit 1
}

# Run the application
"Running download for $yesterday..." | Tee-Object -FilePath $logFile -Append

try {
    python main.py $yesterday $yesterday --download-only --download-dir $DownloadDir 2>&1 | Tee-Object -FilePath $logFile -Append

    if ($LASTEXITCODE -eq 0) {
        "SUCCESS: Download completed for $yesterday" | Tee-Object -FilePath $logFile -Append
        $exitCode = 0
    } else {
        "ERROR: Download failed for $yesterday (exit code: $LASTEXITCODE)" | Tee-Object -FilePath $logFile -Append
        $exitCode = 1
    }
} catch {
    "ERROR: Download failed for $yesterday - $_" | Tee-Object -FilePath $logFile -Append
    $exitCode = 1
}

# Deactivate virtual environment
deactivate

# Log completion
$logEnd = @"
Completed at: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')
$separator
"@
$logEnd | Tee-Object -FilePath $logFile -Append

exit $exitCode
