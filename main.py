"""
main.py -- Stock Tracker entry point.

Usage:
  python main.py                       # normal daily run
  python main.py --backfill            # daily run + backfill from config start date
  python main.py --backfill 2026-06-25 # daily run + backfill from a specific date
  python main.py --dashboard-only      # regenerate Excel + HTML (no fetch)
"""
import argparse
import sqlite3
from datetime import date
from pathlib import Path

import config
from db           import init_db, get_tracked_symbols, insert_rows, get_metadata, set_metadata
from fetch        import fetch_most_active, fetch_quotes_for_symbols
from export_excel import export_excel
from export_html  import export_html
from backfill     import run_backfill

BASE    = Path(__file__).parent
DB_PATH = BASE / "stocks.db"


def main():
    parser = argparse.ArgumentParser(description="Stock Tracker")
    parser.add_argument(
        "--backfill", nargs="?", const=True, metavar="DATE",
        help="Backfill history. Optionally pass YYYY-MM-DD "
             "(default: config backfill_start)."
    )
    parser.add_argument(
        "--dashboard-only", action="store_true",
        help="Skip fetching; just regenerate Excel + HTML from the existing DB."
    )
    args = parser.parse_args()

    conn = sqlite3.connect(DB_PATH)
    init_db(conn)

    if not args.dashboard_only:
        # capture symbols tracked before today so we can detect new ones
        previously_tracked = set(get_tracked_symbols(conn))

        # Step 1: fetch today's most active
        print("Fetching most active stocks ...")
        active_rows = fetch_most_active()
        if active_rows:
            n = insert_rows(conn, active_rows, source="most_active")
            print(f"  {len(active_rows)} fetched, {n} new rows inserted")
        else:
            print("  WARNING: no data fetched -- Yahoo Finance may be unavailable.")

        # Step 2: gap-fill symbols that were tracked but missing today
        today_symbols = {r["symbol"] for r in active_rows}
        tracked       = get_tracked_symbols(conn)
        missing       = [s for s in tracked if s not in today_symbols]
        if missing:
            print(f"Gap-filling {len(missing)} symbols ...")
            gap_rows = fetch_quotes_for_symbols(missing)
            n2 = insert_rows(conn, gap_rows, source="gap_fill")
            print(f"  {n2} rows inserted")
        else:
            print("No gap-fill needed -- all tracked symbols appeared today.")

        # Step 3: auto-backfill any brand-new symbols
        new_symbols = [s for s in today_symbols if s not in previously_tracked]
        if new_symbols:
            print(f"Auto-backfilling {len(new_symbols)} new symbol(s) ...")
            run_backfill(conn, start_str=None, symbols=new_symbols)

        # Step 4: weekly gap-fill on the configured day of week
        # (skipped if --backfill was passed, or if already ran today)
        today_str = date.today().isoformat()
        last_weekly = get_metadata(conn, "last_weekly_fill")
        if (date.today().weekday() == config.WEEKLY_FILL_DAY
                and not args.backfill
                and last_weekly != today_str):
            print(f"Weekly gap-fill (start: {config.BACKFILL_START}) ...")
            run_backfill(conn, start_str=config.BACKFILL_START)
            set_metadata(conn, "last_weekly_fill", today_str)

    # Step 5: optional manual full backfill
    if args.backfill:
        start_str = args.backfill if isinstance(args.backfill, str) else config.BACKFILL_START
        print(f"Running backfill from {start_str} ...")
        run_backfill(conn, start_str=start_str)

    # Step 6: export
    print("Exporting Excel ...")
    export_excel(conn)

    print("Generating HTML dashboard ...")
    export_html(conn)

    conn.close()
    print("Done.")


if __name__ == "__main__":
    main()
