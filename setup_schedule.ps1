# setup_schedule.ps1
# Run this ONCE (as Administrator) to schedule daily stock tracking.
#
# Creates TWO tasks:
#   StockTracker_Daily   - runs main.py at 4:30 PM every weekday
#   StockTracker_Catchup - runs every hour after 4 PM; skips if data exists
#
# Usage:  powershell -ExecutionPolicy Bypass -File setup_schedule.ps1

$ScriptDir     = Split-Path -Parent $MyInvocation.MyCommand.Path
$PythonExe     = (Get-Command python).Source
$MainScript    = Join-Path $ScriptDir "main.py"
$CatchupScript = Join-Path $ScriptDir "catchup.py"
$LogFile       = Join-Path $ScriptDir "tracker.log"
$DailyWrapper  = Join-Path $ScriptDir "run_daily.ps1"
$CatchupWrapper= Join-Path $ScriptDir "run_catchup.ps1"
$DailyVbs      = Join-Path $ScriptDir "run_daily.vbs"
$CatchupVbs    = Join-Path $ScriptDir "run_catchup.vbs"

# -- Install Python deps -------------------------------------------------------
Write-Host "Installing Python dependencies ..."
& $PythonExe -m pip install -r "$ScriptDir\requirements.txt" --quiet

# -- Write catchup.py ----------------------------------------------------------
@"
"""
catchup.py - run hourly after 4 PM; only calls main.py if today's data is missing.
"""
import sqlite3, sys, subprocess
from datetime import date, datetime
from pathlib import Path

BASE  = Path(__file__).parent
DB    = BASE / "stocks.db"
TODAY = date.today().isoformat()

if datetime.now().hour < 16:
    print(f"Before 4 PM - skipping until market close.")
    sys.exit(0)

if DB.exists():
    conn = sqlite3.connect(DB)
    count = conn.execute(
        "SELECT COUNT(*) FROM daily_prices WHERE date=? AND source='most_active'", (TODAY,)
    ).fetchone()[0]
    conn.close()
    if count >= 50:
        print(f"Already have data for {TODAY} ({count} rows), skipping.")
        sys.exit(0)
    elif count > 0:
        print(f"Only {count} rows for {TODAY} - looks like a partial run, retrying ...")

print(f"No data for {TODAY} yet - running main.py ...")
subprocess.run([sys.executable, str(BASE / "main.py")], check=True)
"@ | Set-Content -Path $CatchupScript -Encoding UTF8

# -- Write run_daily.ps1 wrapper -----------------------------------------------
@"
`$LogFile  = "$LogFile"
`$PythonExe = "$PythonExe"
`$MainScript = "$MainScript"

Add-Content -Path `$LogFile -Value ""
Add-Content -Path `$LogFile -Value "[`$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] --- Daily run started ---"
& `$PythonExe `$MainScript 2>&1 | ForEach-Object {
    Add-Content -Path `$LogFile -Value `$_
    Write-Output `$_
}
Add-Content -Path `$LogFile -Value "[`$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] --- Daily run finished ---"
"@ | Set-Content -Path $DailyWrapper -Encoding UTF8

# -- Write run_catchup.ps1 wrapper ---------------------------------------------
@"
`$LogFile  = "$LogFile"
`$PythonExe = "$PythonExe"
`$CatchupScript = "$CatchupScript"

Add-Content -Path `$LogFile -Value ""
Add-Content -Path `$LogFile -Value "[`$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] --- Catchup run started ---"
& `$PythonExe `$CatchupScript 2>&1 | ForEach-Object {
    Add-Content -Path `$LogFile -Value `$_
    Write-Output `$_
}
Add-Content -Path `$LogFile -Value "[`$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] --- Catchup run finished ---"
"@ | Set-Content -Path $CatchupWrapper -Encoding UTF8

# -- Write VBScript launchers (run PowerShell with no visible window) ----------
@"
Set WShell = CreateObject("WScript.Shell")
WShell.Run "powershell.exe -WindowStyle Hidden -ExecutionPolicy Bypass -File ""$DailyWrapper""", 0, False
"@ | Set-Content -Path $DailyVbs -Encoding ASCII

@"
Set WShell = CreateObject("WScript.Shell")
WShell.Run "powershell.exe -WindowStyle Hidden -ExecutionPolicy Bypass -File ""$CatchupWrapper""", 0, False
"@ | Set-Content -Path $CatchupVbs -Encoding ASCII

# -- Task 1: Daily at 4:30 PM on weekdays -------------------------------------
$TaskName1 = "StockTracker_Daily"
$Action1   = New-ScheduledTaskAction `
    -Execute "wscript.exe" `
    -Argument "`"$DailyVbs`"" `
    -WorkingDirectory $ScriptDir
$Trigger1  = New-ScheduledTaskTrigger -Weekly `
    -DaysOfWeek Monday,Tuesday,Wednesday,Thursday,Friday -At "4:30PM"
$Settings1 = New-ScheduledTaskSettingsSet `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 10) `
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
    -Execute "wscript.exe" `
    -Argument "`"$CatchupVbs`"" `
    -WorkingDirectory $ScriptDir
$Trigger2  = New-ScheduledTaskTrigger -Once -At "12:00AM" `
    -RepetitionInterval (New-TimeSpan -Hours 1) `
    -RepetitionDuration (New-TimeSpan -Days 3650)
$Settings2 = New-ScheduledTaskSettingsSet `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 10) `
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
Write-Host "To backfill history:     python `"$MainScript`" --backfill"
Write-Host "To refresh dashboard:    python `"$MainScript`" --dashboard-only"
Write-Host "To remove both tasks:"
Write-Host "  Unregister-ScheduledTask -TaskName '$TaskName1'"
Write-Host "  Unregister-ScheduledTask -TaskName '$TaskName2'"
