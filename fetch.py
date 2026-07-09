"""
fetch.py -- Yahoo Finance API calls.
"""
import requests
import time
from datetime import date, datetime, timezone

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0 Safari/537.36"
    ),
    "Accept": "application/json",
}

SCREENER_URL = "https://query1.finance.yahoo.com/v1/finance/screener/predefined/saved"
CHART_URL    = "https://query2.finance.yahoo.com/v8/finance/chart/{symbol}"


def _parse_quote(q, today):
    wk52 = q.get("fiftyTwoWeekChangePercent")
    return {
        "date":            today,
        "symbol":          q.get("symbol"),
        "name":            q.get("shortName") or q.get("longName", ""),
        "price":           q.get("regularMarketPrice"),
        "change":          q.get("regularMarketChange"),
        "change_pct":      q.get("regularMarketChangePercent"),
        "volume":          q.get("regularMarketVolume"),
        "market_cap":      q.get("marketCap"),
        "pe_ratio":        q.get("trailingPE"),
        "wk52_change_pct": wk52 if wk52 is not None else None,
        "wk52_low":        q.get("fiftyTwoWeekLow"),
        "wk52_high":       q.get("fiftyTwoWeekHigh"),
    }


def fetch_most_active():
    """Fetch top 100 most active US stocks from Yahoo Finance screener."""
    today = date.today().isoformat()
    params = {"scrIds": "most_actives", "count": 100, "start": 0,
              "region": "US", "lang": "en-US"}
    try:
        resp = requests.get(SCREENER_URL, headers=HEADERS, params=params, timeout=20)
        resp.raise_for_status()
        quotes = (resp.json()
                  .get("finance", {})
                  .get("result", [{}])[0]
                  .get("quotes", []))
        return [_parse_quote(q, today) for q in quotes]
    except Exception as e:
        print(f"  fetch_most_active failed: {e}")
        return []


def fetch_quotes_for_symbols(symbols):
    """Gap-fill: fetch today's price/volume for each symbol via chart history.
    Uses the same reliable endpoint as backfill -- no auth required.
    Market cap, P/E, and 52wk are not needed for gap-fill rows.
    """
    today = date.today().isoformat()
    rows = []
    for sym in symbols:
        history = fetch_chart_history(sym, today, today)
        if history:
            rows.append(history[-1])
        time.sleep(0.15)
    return rows


def fetch_chart_history(symbol, start_str, end_str):
    """
    Fetch daily price/volume history for a symbol between two dates.
    Returns list of dicts: {date, symbol, price, change, change_pct, volume}.
    """
    def to_unix(s):
        return int(datetime.strptime(s, "%Y-%m-%d").replace(tzinfo=timezone.utc).timestamp())

    params = {
        "period1":  to_unix(start_str),
        "period2":  to_unix(end_str) + 86400,
        "interval": "1d",
        "events":   "history",
    }
    try:
        resp = requests.get(CHART_URL.format(symbol=symbol),
                            headers=HEADERS, params=params, timeout=20)
        resp.raise_for_status()
        result = resp.json().get("chart", {}).get("result", [])
        if not result:
            return []
        r       = result[0]
        stamps  = r.get("timestamp", [])
        closes  = r["indicators"]["quote"][0].get("close",  [])
        volumes = r["indicators"]["quote"][0].get("volume", [])
    except Exception as e:
        print(f"    WARNING: {symbol} history fetch failed: {e}")
        return []

    rows = []
    prev = None
    for ts, close, vol in zip(stamps, closes, volumes):
        if close is None:
            prev = close
            continue
        day     = datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d")
        chg     = round(close - prev, 4) if prev is not None else 0.0
        chg_pct = round(chg / prev * 100, 4) if prev else 0.0
        rows.append({
            "date":       day,
            "symbol":     symbol,
            "price":      round(close, 4),
            "change":     chg,
            "change_pct": chg_pct,
            "volume":     int(vol) if vol is not None else None,
        })
        prev = close
    return rows
