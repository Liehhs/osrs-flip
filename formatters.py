import time
from datetime import datetime

import pytz


def fmt_gp(value):
    if value is None:
        return "—"
    try:
        value = int(value)
    except Exception:
        return "—"
    if abs(value) >= 1_000_000_000:
        return f"{value / 1_000_000_000:.2f}B"
    if abs(value) >= 1_000_000:
        return f"{value / 1_000_000:.2f}M"
    if abs(value) >= 1_000:
        return f"{value / 1_000:.1f}K"
    return f"{value:,}"


def fmt_int(value):
    try:
        return f"{int(value):,}"
    except Exception:
        return "—"


def fmt_pct(value):
    if value is None:
        return "—"
    try:
        return f"{float(value):.2f}%"
    except Exception:
        return "—"


def now_ts():
    return time.time()


def secs_ago(ts):
    return int(now_ts() - ts) if ts else None


def fmt_ago(seconds):
    if seconds is None:
        return "never"
    if seconds < 60:
        return f"{seconds}s ago"
    return f"{seconds // 60}m {seconds % 60}s ago"


def get_timing():
    est = pytz.timezone("America/New_York")
    now = datetime.now(est)
    hour = now.hour
    timestamp = now.strftime("%I:%M %p ET")
    if 14 <= hour < 22:
        return "positive", "Sell window", f"US/EU peak overlap. Strong time to exit positions. ({timestamp})"
    if 6 <= hour < 14:
        return "warning", "Transition window", f"Moderate activity. Good for placing staged buy orders. ({timestamp})"
    return "negative", "Buy window", f"Off-peak liquidity. Best for setting patient buy orders. ({timestamp})"