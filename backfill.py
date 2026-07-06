"""
backfill.py -- fetch historical price/volume for all tracked symbols.

Standalone usage:
    python backfill.py                  # fills from config backfill_start
    python backfill.py 2026-06-25       # fills from a specific date

Also importable: call run_backfill(conn, start_str, symbols) from main.py.
Only inserts rows that do not already exist (safe to run multiple times).
"""
import sqlite3
import sys
import time
from datetime import date, datetime
from pathlib import Path

BASE = Path(__file__).parent
DB   = BASE / "stocks.db"


def run_backfill(conn, start_str=None, symbols=None):
    """
    Backfill daily price/volume history into an open connection.
    start_str : "YYYY-MM-DD" or None (uses config.BACKFILL_START).
    symbols   : list of symbols, or None to backfill all tracked.
    """
    from fetch  import fetch_chart_history
    import config

    if start_str is None:
        start_str = config.BACKFILL_START
    end_str = date.today().isoformat()

    if symbols is None:
        symbols = [r[0] for r in conn.execute("SELECT symbol FROM stocks ORDER BY symbol")]
    if not symbols:
        print("  No symbols in DB yet -- run main.py first.")
        return

    print(f"  Backfilling {len(symbols)} symbols from {start_str} to {end_str} ...")
    total = 0
    for i, sym in enumerate(symbols, 1):
        rows = fetch_chart_history(sym, start_str, end_str)
        inserted = 0
        for r in rows:
            try:
                conn.execute("""
                    INSERT OR IGNORE INTO daily_prices
                        (date, symbol, price, change, change_pct, volume, source)
                    VALUES (?, ?, ?, ?, ?, ?, 'backfill')
                """, (r["date"], r["symbol"], r["price"],
                      r["change"], r["change_pct"], r["volume"]))
                inserted += conn.execute("SELECT changes()").fetchone()[0]
            except sqlite3.Error as e:
                print(f"    DB error {sym} {r['date']}: {e}")
        conn.commit()
        total += inserted
        label = f"+{inserted} rows" if inserted else "already up to date"
        print(f"  [{i:>3}/{len(symbols)}] {sym:<10} {label}")
        time.sleep(0.15)

    print(f"  Backfill complete: {total} new rows inserted.")


def main():
    import config
    start = sys.argv[1] if len(sys.argv) > 1 else config.BACKFILL_START
    try:
        datetime.strptime(start, "%Y-%m-%d")
    except ValueError:
        print(f"ERROR: invalid date '{start}' -- use YYYY-MM-DD")
        sys.exit(1)

    if not DB.exists():
        print(f"ERROR: database not found at {DB}")
        print("Run main.py at least once first.")
        sys.exit(1)

    import sqlite3 as _sq
    conn = _sq.connect(DB)
    try:
        run_backfill(conn, start)
    finally:
        conn.close()
    print("Done. Run  python main.py --dashboard-only  to refresh the dashboard.")


if __name__ == "__main__":
    main()
