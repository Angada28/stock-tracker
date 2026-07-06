# Stock Tracker

Fetches the top 100 most active US stocks from Yahoo Finance daily, stores them in a local SQLite database, and generates an interactive HTML dashboard and an Excel snapshot.

---

## Prerequisites

- **Python 3.8 or higher** — download from [python.org](https://www.python.org/downloads/). During installation, check **"Add Python to PATH"**.
- **Windows** — the automated scheduling uses Windows Task Scheduler via PowerShell. The Python scripts themselves work on any OS; only `setup_schedule.ps1` is Windows-specific.

To confirm Python is installed correctly, open a terminal and run:

```
python --version
```

---

## Files

| File                 | Purpose                                       |
| -------------------- | --------------------------------------------- |
| `main.py`            | Entry point — runs the full pipeline          |
| `fetch.py`           | Yahoo Finance API calls                       |
| `db.py`              | Database setup and inserts                    |
| `backfill.py`        | Historical data fetching                      |
| `export_excel.py`    | Generates `stocks.xlsx`                       |
| `export_html.py`     | Generates `dashboard.html`                    |
| `config.py`          | Reads settings from `config.ini`              |
| `config.ini`         | User-editable settings (start date, fill day) |
| `setup_schedule.ps1` | One-time Windows Task Scheduler setup         |
| `requirements.txt`   | Python dependencies                           |

---

## Setup

### 1. Install dependencies

Open a terminal in the project folder and run:

```
pip install -r requirements.txt
```

### 2. Configure your start date

Open `config.ini` in any text editor:

```ini
[tracker]
backfill_start = 2026-06-25
weekly_fill_day = 0
```

- **`backfill_start`** — the earliest date you want price history from. Change this to your preferred start date in `YYYY-MM-DD` format.
- **`weekly_fill_day`** — day of the week to automatically fill any missing entries (0 = Monday, 1 = Tuesday, ... 6 = Sunday).

### 3. Run the initial backfill

On first run, fetch today's data and populate history from your configured start date:

```
python main.py --backfill
```

This will take a few minutes depending on how many symbols are tracked and how far back your start date is.

### 4. (Optional) Set up automatic daily scheduling

Run the following once in PowerShell **as Administrator**:

```
powershell -ExecutionPolicy Bypass -File setup_schedule.ps1
```

This creates two Windows Task Scheduler tasks:

- **StockTracker_Daily** — runs `main.py` every weekday at 4:30 PM
- **StockTracker_Catchup** — runs every hour and fetches data if today's hasn't been collected yet (handles missed runs)

To confirm the tasks work:

```
Get-ScheduledTask -TaskName "StockTracker_Daily"
Get-ScheduledTask -TaskName "StockTracker_Catchup"
```

To remove the scheduled tasks later:

```
Unregister-ScheduledTask -TaskName 'StockTracker_Daily'
Unregister-ScheduledTask -TaskName 'StockTracker_Catchup'
```

---

## Running the program

### Normal daily run

Fetches today's top 100, gap-fills any tracked symbols not in the list, and regenerates the dashboard:

```
python main.py
```

### Backfill history

Fetch missing historical data from your configured start date:

```
python main.py --backfill
```

Or from a specific date:

```
python main.py --backfill 2026-01-01
```

### Regenerate dashboard only

Rebuild `dashboard.html` and `stocks.xlsx` from existing data without fetching anything:

```
python main.py --dashboard-only
```

### Backfill only (standalone)

Run the backfill script directly without going through the full pipeline:

```
python backfill.py
python backfill.py 2026-01-01
```

---

## Viewing the dashboard

Open `dashboard.html` in any web browser. It requires no server — it's a self-contained file.

The dashboard has four views:

- **Today** — sortable table of today's most active stocks with price, change, volume, market cap, P/E, and 52-week change
- **Detail** — price and volume chart for a single symbol with adjustable date range
- **Compare** — overlaid percentage-change chart for multiple symbols; search and add symbols one at a time
- **Movers** — top gainers and losers over the selected range

A light/dark mode toggle is available in the top-right corner of the header.

---

## How gap-filling works

The tracker keeps every symbol it has ever seen, not just today's top 100. Each daily run:

1. Fetches the current top 100 and inserts them as `most_active`
2. For any previously tracked symbol not in today's list, fetches a single quote and inserts it as `gap_fill` — keeping the chart history continuous
3. Auto-backfills any brand-new symbols from `backfill_start` so they have full history immediately
4. On the configured weekly day, runs a full backfill for all symbols to fill any remaining holes

All inserts use `INSERT OR IGNORE`, so data is never duplicated and any step is safe to re-run.

---

## Data notes

- Market cap, P/E ratio, and 52-week change are only available from the live screener (`most_active` rows). Backfilled and gap-filled rows will show `--` for these fields.
- Price and volume are available for all rows including backfilled history.
- The database (`stocks.db`) and generated files (`dashboard.html`, `stocks.xlsx`) are created automatically on first run and should not be committed to version control — add them to `.gitignore`.

---
