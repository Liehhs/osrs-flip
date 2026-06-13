import pandas as pd

from theme import THEME


def status_badge(kind, text):
    return f'<span class="badge badge-{kind}">{text}</span>'


def ratio_state(ratio):
    if ratio is None:
        return "neutral", "No data"
    if 0.8 <= ratio <= 1.5:
        return "positive", "Balanced"
    if 1.5 < ratio <= 3.0:
        return "warning", "High demand"
    if ratio > 3.0:
        return "negative", "Hard buy"
    if 0.4 <= ratio < 0.8:
        return "caution", "Slight flood"
    return "negative", "Flooded"


def trend_state(trend):
    return {
        "Building": "positive",
        "Pullback": "warning",
        "Extended": "warning",
        "Weakening": "negative",
        "Flat": "neutral",
    }.get(trend, "neutral")


def compute_score(row):
    realistic = min((row.get("realistic_profit", 0) or 0) / 1_000_000, 20)
    roi = min(row.get("roi", 0) or 0, 20)
    liquidity = min((row.get("total_hr", 0) or 0) / 1000, 10)
    fill = (row.get("fq_mult", 0) or 0) * 10
    priority = (row.get("priority", 0) or 0) * 2
    return round(realistic * 0.35 + roi * 0.25 + liquidity * 0.2 + fill * 0.1 + priority * 0.1, 2)


def add_score(rows):
    enriched = []
    for row in rows:
        item = dict(row)
        item["score"] = compute_score(item)
        enriched.append(item)
    return enriched


def to_df(rows, columns):
    if not rows:
        return pd.DataFrame(columns=columns)
    df = pd.DataFrame(rows)
    existing = [col for col in columns if col in df.columns]
    return df[existing].copy()


def style_dataframe(df, formatters=None):
    formatters = formatters or {}

    def color_trend(val):
        state = trend_state(val)
        color = {
            "positive": THEME["positive"],
            "warning": THEME["warning"],
            "negative": THEME["negative"],
            "neutral": "#cbd5e1",
        }.get(state, "#cbd5e1")
        weight = "600" if state != "neutral" else "500"
        return f"color: {color}; font-weight: {weight}"

    def color_ratio(val):
        state, _ = ratio_state(val)
        color = {
            "positive": THEME["positive"],
            "warning": THEME["warning"],
            "caution": THEME["caution"],
            "negative": THEME["negative"],
            "neutral": THEME["muted"],
        }.get(state, THEME["muted"])
        return f"color: {color}; font-weight: 600"

    def color_pct(val):
        if val is None:
            return f"color: {THEME['muted']}"
        if val >= 10:
            return f"color: {THEME['positive']}; font-weight: 700"
        if val > 0:
            return f"color: {THEME['positive_soft']}"
        if val <= -10:
            return f"color: {THEME['negative']}; font-weight: 700"
        if val < 0:
            return f"color: {THEME['negative_soft']}"
        return "color: #cbd5e1"

    def color_flag(val):
        val = str(val)
        if val == "Quiet":
            return f"color: {THEME['muted']}"
        if "1D shock" in val or "7D move" in val or "30D regime" in val:
            return f"color: {THEME['warning']}; font-weight: 700"
        if "Wide spread" in val or "High gp/item" in val:
            return f"color: {THEME['positive']}; font-weight: 700"
        return "color: #cbd5e1"

    styler = (
        df.style.format(formatters)
        .set_properties(
            **{
                "background-color": THEME["panel"],
                "color": THEME["text"],
                "border-color": THEME["border"],
                "text-align": "left",
            }
        )
        .set_table_styles(
            [
                {"selector": "th", "props": [("background-color", THEME["panel_alt"]), ("color", THEME["text"]), ("border", f"1px solid {THEME['border']}"), ("font-weight", "700")]},
                {"selector": "td", "props": [("border", f"1px solid {THEME['border']}")]},
            ]
        )
    )

    if "ratio" in df.columns:
        styler = styler.map(color_ratio, subset=["ratio"])
    for col in ["roi", "chg_1d", "chg_7d", "chg_30d", "1D", "7D"]:
        if col in df.columns:
            styler = styler.map(color_pct, subset=[col])
    for col in ["trend", "Trend"]:
        if col in df.columns:
            styler = styler.map(color_trend, subset=[col])
    for col in ["flags", "Flags"]:
        if col in df.columns:
            styler = styler.map(color_flag, subset=[col])
    return styler