"""
backfill.py -- fetch historical price/volume for all tracked symbols.

Standalone usage:
    python backfill.py                  # fills from config backfill_start
    python backfill.py 2026-06-25       # fills from a specific date

Also importable: call run_backfill(conn, start_str, symbols) from main.py.
Only fetches what is actually missing -- skips symbols already up to date.
"""
import sqlite3
import sys
import time
from datetime import date, datetime, timedelta
from pathlib import Path

BASE = Path(__file__).parent
DB   = BASE / "stocks.db"


def _business_days(start_str, end_str):
    """Return sorted list of YYYY-MM-DD strings for all weekdays in range."""
    days = []
    cur = datetime.strptime(start_str, "%Y-%m-%d").date()
    end = datetime.strptime(end_str,   "%Y-%m-%d").date()
    while cur <= end:
        if cur.weekday() < 5:
            days.append(cur.isoformat())
        cur += timedelta(days=1)
    return days


def _missing_range(conn, symbol, start_str, end_str):
    """
    Return (fetch_start, fetch_end) covering missing dates, or None if complete.

    Compares all expected business days against what we have in the DB.
    If any dates are missing (including holes in the middle), returns a range
    from the earliest missing date to end_str. INSERT OR IGNORE handles any
    already-present dates within that span.
    """
    expected = set(_business_days(start_str, end_str))
    if not expected:
        return None

    existing = set(r[0] for r in conn.execute(
        "SELECT date FROM daily_prices WHERE symbol=? AND date>=? AND date<=?",
        (symbol, start_str, end_str)
    ))

    missing = sorted(expected - existing)
    if not missing:
        return None

    # Fetch from earliest missing date to end -- INSERT OR IGNORE skips
    # any dates we already have that fall within this span
    return (missing[0], end_str)


def run_backfill(conn, start_str=None, symbols=None):
    """
    Backfill daily price/volume history into an open connection.
    start_str : "YYYY-MM-DD" or None (uses config.BACKFILL_START).
    symbols   : list of symbols, or None to backfill all tracked.
    """
    from fetch import fetch_chart_history
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
    fetched = 0
    for i, sym in enumerate(symbols, 1):
        fetch_range = _missing_range(conn, sym, start_str, end_str)

        if fetch_range is None:
            print(f"  [{i:>3}/{len(symbols)}] {sym:<10} already up to date")
            continue

        fetched += 1
        rows = fetch_chart_history(sym, fetch_range[0], fetch_range[1])
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
        label = f"+{inserted} rows" if inserted else "nothing new"
        print(f"  [{i:>3}/{len(symbols)}] {sym:<10} {label}")
        time.sleep(0.15)

    print(f"  Backfill complete: {total} new rows inserted ({fetched} symbols fetched, {len(symbols)-fetched} skipped).")


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
