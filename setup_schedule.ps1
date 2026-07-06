# setup_schedule.ps1
# Run this ONCE (as Administrator) to schedule daily stock tracking.
#
# Creates TWO tasks:
#   StockTracker_Daily   - runs main.py at 4:30 PM every weekday
#   StockTracker_Catchup - runs every hour; skips if today's data already exists
#
# Usage:  powershell -ExecutionPolicy Bypass -File setup_schedule.ps1

$ScriptDir   = Split-Path -Parent $MyInvocation.MyCommand.Path
$PythonExe   = (Get-Command python).Source
$MainScript  = Join-Path $ScriptDir "main.py"
$CatchupScript = Join-Path $ScriptDir "catchup.py"
$LogFile     = Join-Path $ScriptDir "tracker.log"

# -- Install Python deps -------------------------------------------------------
Write-Host "Installing Python dependencies ..."
& $PythonExe -m pip install -r "$ScriptDir\requirements.txt" --quiet

# -- Write the catch-up helper script -----------------------------------------
@"
"""
catchup.py - run hourly; only calls main.py if today's data is missing.
"""
import sqlite3, sys, subprocess
from datetime import date
from pathlib import Path

BASE  = Path(__file__).parent
DB    = BASE / "stocks.db"
TODAY = date.today().isoformat()

if DB.exists():
    conn = sqlite3.connect(DB)
    row  = conn.execute(
        "SELECT 1 FROM daily_prices WHERE date=? LIMIT 1", (TODAY,)
    ).fetchone()
    conn.close()
    if row:
        print(f"Already have data for {TODAY}, skipping.")
        sys.exit(0)

print(f"No data for {TODAY} yet - running main.py ...")
subprocess.run([sys.executable, str(BASE / "main.py")], check=True)
"@ | Set-Content -Path $CatchupScript -Encoding UTF8

# -- Task 1: Daily at 4:30 PM on weekdays -------------------------------------
$TaskName1 = "StockTracker_Daily"
$Action1   = New-ScheduledTaskAction `
    -Execute $PythonExe `
    -Argument "`"$MainScript`" >> `"$LogFile`" 2>&1" `
    -WorkingDirectory $ScriptDir
$Trigger1  = New-ScheduledTaskTrigger -Weekly `
    -DaysOfWeek Monday,Tuesday,Wednesday,Thursday,Friday -At "4:30PM"
$Settings1 = New-ScheduledTaskSettingsSet `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 5) `
    -StartWhenAvailable `
    -RunOnlyIfNetworkAvailable

if (Get-ScheduledTask -TaskName $TaskName1 -ErrorAction SilentlyContinue) {
    Unregister-ScheduledTask -TaskName $TaskName1 -Confirm:$false
}
Register-ScheduledTask `
    -TaskName    $TaskName1 `
    -Action      $Action1 `
    -Trigger     $Trigger1 `
    -Settings    $Settings1 `
    -Description "Fetches Yahoo Finance most active stocks weekdays at 4:30 PM" `
    -RunLevel    Highest | Out-Null
Write-Host "  [OK] $TaskName1 - weekdays at 4:30 PM"

# -- Task 2: Catch-up every hour, skips if already ran today ------------------
$TaskName2 = "StockTracker_Catchup"
$Action2   = New-ScheduledTaskAction `
    -Execute $PythonExe `
    -Argument "`"$CatchupScript`" >> `"$LogFile`" 2>&1" `
    -WorkingDirectory $ScriptDir
$Trigger2  = New-ScheduledTaskTrigger -Daily -At "12:00AM"
$Trigger2.Repetition.Interval = "PT1H"
$Trigger2.Repetition.Duration = "P1D"
$Settings2 = New-ScheduledTaskSettingsSet `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 5) `
    -StartWhenAvailable `
    -RunOnlyIfNetworkAvailable

if (Get-ScheduledTask -TaskName $TaskName2 -ErrorAction SilentlyContinue) {
    Unregister-ScheduledTask -TaskName $TaskName2 -Confirm:$false
}
Register-ScheduledTask `
    -TaskName    $TaskName2 `
    -Action      $Action2 `
    -Trigger     $Trigger2 `
    -Settings    $Settings2 `
    -Description "Hourly catch-up: runs main.py only if today's data is missing" `
    -RunLevel    Highest | Out-Null
Write-Host "  [OK] $TaskName2 - every hour (skips if already ran today)"

Write-Host ""
Write-Host "Setup complete. Logs -> $LogFile"
Write-Host ""
Write-Host "To run immediately:      python `"$MainScript`""
Write-Host "To backfill history:     python `"$MainScript`" --backfill 2026-06-25"
Write-Host "To refresh dashboard:    python `"$MainScript`" --dashboard-only"
Write-Host "To remove both tasks:"
Write-Host "  Unregister-ScheduledTask -TaskName '$TaskName1'"
Write-Host "  Unregister-ScheduledTask -TaskName '$TaskName2'"
