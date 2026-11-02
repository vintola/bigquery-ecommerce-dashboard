"""Visual constants and small formatting helpers for the dashboard."""

from __future__ import annotations

ACCENT = "#cff45a"
ACCENT_BRIGHT = "#e0ff8f"
COOL = "#809bff"
AMBER = "#ffb86b"
RED = "#ff7a7a"
BG = "#0a0b0e"
PANEL = "#101218"
PANEL_2 = "#161a22"
TEXT = "#f2f0e9"
MUTED = "#9aa0ad"
MUTED_STRONG = "#bdc2cc"
GRID = "rgba(238, 237, 232, 0.08)"
LINE = "rgba(238, 237, 232, 0.17)"

SANS = "Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif"
MONO = "'JetBrains Mono', 'SFMono-Regular', Menlo, Consolas, monospace"

PORTFOLIO_URL = "https://alvintola.com"
REPO_URL = "https://github.com/vintola/bigquery-ecommerce-dashboard"
SOURCE_URL = "https://console.cloud.google.com/marketplace/product/bigquery-public-data/thelook-ecommerce"

CSS = f"""
<style>
  .stApp {{
    background:
      radial-gradient(ellipse 70% 45% at 80% -10%, rgba(207, 244, 90, 0.06), transparent 60%),
      {BG};
  }}
  .block-container {{
    padding-top: 2.4rem;
    padding-bottom: 3rem;
    max-width: 1180px;
  }}
  header[data-testid="stHeader"] {{
    background: transparent;
  }}
  #MainMenu, footer {{ visibility: hidden; }}
  [data-testid="stToolbar"], [data-testid="stDecoration"] {{ display: none; }}

  .dash-header {{
    border-bottom: 1px solid {LINE};
    padding-bottom: 1.4rem;
    margin-bottom: 1.2rem;
  }}
  .dash-eyebrow {{
    font-family: {MONO};
    font-size: 0.72rem;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: {ACCENT};
    margin: 0 0 0.6rem;
  }}
  .dash-title {{
    font-family: 'Fraunces', Georgia, serif;
    font-weight: 500;
    font-size: clamp(2rem, 4vw, 3.1rem);
    line-height: 1.06;
    letter-spacing: -0.02em;
    color: {TEXT};
    margin: 0 0 0.7rem;
  }}
  .dash-sub {{
    color: {MUTED_STRONG};
    font-size: 0.98rem;
    line-height: 1.6;
    max-width: 72ch;
    margin: 0;
  }}
  .dash-sub a, .dash-link a {{ color: {ACCENT}; text-decoration: none; }}
  .dash-sub a:hover, .dash-link a:hover {{ text-decoration: underline; }}

  [data-testid="stMetric"] {{
    background: linear-gradient(180deg, {PANEL_2}, {PANEL});
    border: 1px solid {LINE};
    border-radius: 10px;
    padding: 0.9rem 1rem;
  }}
  [data-testid="stMetricLabel"] {{
    font-family: {MONO};
    font-size: 0.68rem !important;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: {MUTED} !important;
  }}
  [data-testid="stMetricValue"] {{
    font-family: {SANS};
    font-weight: 600;
    letter-spacing: -0.02em;
    color: {TEXT};
  }}
  [data-testid="stMetricDelta"] {{
    font-family: {MONO};
    font-size: 0.72rem !important;
  }}

  .insight {{
    background: {PANEL};
    border: 1px solid {LINE};
    border-left: 3px solid {ACCENT};
    border-radius: 8px;
    padding: 0.9rem 1.05rem;
    margin: 0.4rem 0 1rem;
    color: {MUTED_STRONG};
    font-size: 0.92rem;
    line-height: 1.6;
  }}
  .insight strong {{ color: {TEXT}; }}
  .insight .label {{
    display: block;
    font-family: {MONO};
    font-size: 0.66rem;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: {ACCENT};
    margin-bottom: 0.35rem;
  }}

  .method-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
    gap: 0.8rem;
    margin: 0.6rem 0 1.2rem;
  }}
  .method-card {{
    background: {PANEL};
    border: 1px solid {LINE};
    border-radius: 9px;
    padding: 1rem;
  }}
  .method-card .step {{
    font-family: {MONO};
    font-size: 0.66rem;
    letter-spacing: 0.12em;
    color: {ACCENT};
    text-transform: uppercase;
  }}
  .method-card h4 {{
    font-family: {SANS};
    font-size: 1rem;
    color: {TEXT};
    margin: 0.35rem 0 0.4rem;
  }}
  .method-card p {{
    color: {MUTED};
    font-size: 0.86rem;
    line-height: 1.55;
    margin: 0;
  }}

  .dash-link {{
    font-family: {MONO};
    font-size: 0.76rem;
    color: {MUTED};
  }}

  [data-testid="stSidebar"] {{
    background: {PANEL};
    border-right: 1px solid {LINE};
  }}
  [data-testid="stSidebar"] h3 {{
    font-family: {MONO};
    font-size: 0.72rem;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: {MUTED};
  }}
</style>
"""


def compact_money(value: float) -> str:
    if value is None:
        return "—"
    value = float(value)
    if abs(value) >= 1_000_000:
        return f"${value / 1_000_000:,.2f}M"
    if abs(value) >= 1_000:
        return f"${value / 1_000:,.1f}K"
    return f"${value:,.0f}"


def money(value: float) -> str:
    return "—" if value is None else f"${float(value):,.2f}"


def number(value: float) -> str:
    return "—" if value is None else f"{float(value):,.0f}"


def pct(value: float, digits: int = 1) -> str:
    return "—" if value is None else f"{float(value):,.{digits}f}%"
