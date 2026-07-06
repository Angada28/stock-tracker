"""
config.py -- reads settings from config.ini.
Import this anywhere you need the tracker settings.
"""
import configparser
from pathlib import Path

_BASE = Path(__file__).parent
_INI  = _BASE / "config.ini"

_DEFAULTS = {
    "backfill_start":  "2026-06-25",
    "weekly_fill_day": "0",
}

_cfg = configparser.ConfigParser(defaults=_DEFAULTS)
_cfg.read(_INI)

def _get(key):
    try:
        return _cfg.get("tracker", key)
    except configparser.NoSectionError:
        return _DEFAULTS[key]

# Earliest date to backfill from (string "YYYY-MM-DD")
BACKFILL_START  = _get("backfill_start")

# Weekday for automatic weekly gap-fill (0=Mon ... 6=Sun)
WEEKLY_FILL_DAY = int(_get("weekly_fill_day"))
