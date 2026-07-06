"""
db.py -- database schema and operations.
"""
import sqlite3
from datetime import date


def init_db(conn):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS stocks (
            symbol      TEXT PRIMARY KEY,
            name        TEXT,
            first_seen  TEXT,
            last_seen   TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS daily_prices (
            date            TEXT    NOT NULL,
            symbol          TEXT    NOT NULL,
            price           REAL,
            change          REAL,
            change_pct      REAL,
            volume          INTEGER,
            market_cap      INTEGER,
            pe_ratio        REAL,
            wk52_change_pct REAL,
            wk52_low        REAL,
            wk52_high       REAL,
            source          TEXT DEFAULT 'most_active',
            PRIMARY KEY (date, symbol),
            FOREIGN KEY (symbol) REFERENCES stocks(symbol)
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_dp_symbol_date ON daily_prices(symbol, date)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_dp_date       ON daily_prices(date)")
    conn.commit()


def upsert_stock(conn, symbol, name, today):
    conn.execute("""
        INSERT INTO stocks (symbol, name, first_seen, last_seen)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(symbol) DO UPDATE SET
            name      = excluded.name,
            last_seen = excluded.last_seen
    """, (symbol, name, today, today))


def get_tracked_symbols(conn):
    return [r[0] for r in conn.execute("SELECT symbol FROM stocks").fetchall()]


def insert_rows(conn, rows, source="most_active"):
    today = date.today().isoformat()
    inserted = 0
    for r in rows:
        symbol = r.get("symbol")
        if not symbol:
            continue
        upsert_stock(conn, symbol, r.get("name", ""), today)
        try:
            conn.execute("""
                INSERT OR IGNORE INTO daily_prices
                    (date, symbol, price, change, change_pct, volume,
                     market_cap, pe_ratio, wk52_change_pct, wk52_low, wk52_high, source)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                r.get("date", today),
                symbol,
                r.get("price"),
                r.get("change"),
                r.get("change_pct"),
                r.get("volume"),
                r.get("market_cap"),
                r.get("pe_ratio"),
                r.get("wk52_change_pct"),
                r.get("wk52_low"),
                r.get("wk52_high"),
                source,
            ))
            inserted += conn.execute("SELECT changes()").fetchone()[0]
        except sqlite3.Error as e:
            print(f"  DB error for {symbol}: {e}")
    conn.commit()
    return inserted
