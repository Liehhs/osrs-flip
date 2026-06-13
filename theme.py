THEME = {
    "bg": "#0f172a",
    "panel": "#111827",
    "panel_alt": "#1f2937",
    "border": "#334155",
    "text": "#e5e7eb",
    "muted": "#94a3b8",
    "accent": "#38bdf8",
    "positive": "#22c55e",
    "positive_soft": "#86efac",
    "warning": "#f59e0b",
    "caution": "#facc15",
    "negative": "#ef4444",
    "negative_soft": "#fca5a5",
    "neutral": "#64748b",
}


def inject_theme(st):
    st.markdown(
        f"""
        <style>
            :root {{
                --bg: {THEME['bg']};
                --panel: {THEME['panel']};
                --panel-alt: {THEME['panel_alt']};
                --border: {THEME['border']};
                --text: {THEME['text']};
                --muted: {THEME['muted']};
                --accent: {THEME['accent']};
                --positive: {THEME['positive']};
                --warning: {THEME['warning']};
                --caution: {THEME['caution']};
                --negative: {THEME['negative']};
                --neutral: {THEME['neutral']};
            }}
            .stApp {{ background: var(--bg); color: var(--text); }}
            .block-container {{ padding-top: 1.2rem; padding-bottom: 2rem; max-width: 1440px; }}
            div[data-testid="stMetric"] {{
                background: linear-gradient(180deg, rgba(17,24,39,0.95), rgba(15,23,42,0.98));
                border: 1px solid var(--border);
                border-radius: 14px;
                padding: 0.6rem 0.8rem;
            }}
            .hero-card {{
                background: linear-gradient(180deg, rgba(17,24,39,0.98), rgba(15,23,42,0.98));
                border: 1px solid var(--border);
                border-radius: 16px;
                padding: 1rem 1.1rem;
                box-shadow: 0 8px 30px rgba(2, 6, 23, 0.22);
                margin-bottom: 1rem;
            }}
            .hero-title {{ font-size: 1.8rem; font-weight: 700; margin-bottom: 0.25rem; }}
            .hero-subtitle {{ color: var(--muted); font-size: 0.96rem; line-height: 1.45; }}
            .badge {{
                display: inline-block;
                padding: 0.25rem 0.55rem;
                border-radius: 999px;
                font-size: 0.78rem;
                font-weight: 700;
                border: 1px solid transparent;
                margin-right: 0.35rem;
            }}
            .badge-accent {{ background: rgba(56,189,248,0.12); color: var(--accent); border-color: rgba(56,189,248,0.25); }}
            .badge-positive {{ background: rgba(34,197,94,0.12); color: var(--positive); border-color: rgba(34,197,94,0.25); }}
            .badge-warning {{ background: rgba(245,158,11,0.14); color: var(--warning); border-color: rgba(245,158,11,0.28); }}
            .badge-negative {{ background: rgba(239,68,68,0.14); color: var(--negative); border-color: rgba(239,68,68,0.28); }}
            .badge-neutral {{ background: rgba(100,116,139,0.16); color: #cbd5e1; border-color: rgba(148,163,184,0.24); }}
            .badge-caution {{ background: rgba(250,204,21,0.14); color: var(--caution); border-color: rgba(250,204,21,0.28); }}
            .section-title {{ font-size: 1.05rem; font-weight: 700; margin-bottom: 0.4rem; }}
            .section-subtitle {{ color: var(--muted); margin-bottom: 0.9rem; font-size: 0.93rem; line-height: 1.5; }}
            .tab-intro {{ max-width: 980px; }}
            .small-note {{ color: var(--muted); font-size: 0.82rem; margin-top: 0.4rem; }}
            .stTabs [data-baseweb="tab-list"] {{ gap: 0.35rem; }}
            .stTabs [data-baseweb="tab"] {{
                background: rgba(31,41,55,0.75);
                border: 1px solid var(--border);
                border-radius: 12px;
                padding: 0.45rem 0.85rem;
            }}
            .stTabs [aria-selected="true"] {{
                background: rgba(56,189,248,0.12);
                border-color: rgba(56,189,248,0.35);
            }}
            div[data-testid="stDataFrame"] {{ border: 1px solid var(--border); border-radius: 14px; overflow: hidden; }}
            section[data-testid="stSidebar"] {{ background: #0b1220; border-right: 1px solid var(--border); }}
        </style>
        """,
        unsafe_allow_html=True,
    )