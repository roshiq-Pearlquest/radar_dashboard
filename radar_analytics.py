from __future__ import annotations

import base64
from datetime import date, datetime, time, timedelta, timezone
import json
from pathlib import Path
import re
import warnings

import pandas as pd
import plotly.graph_objects as go
import requests
import streamlit as st

try:
    from PIL import Image
except ImportError:  # pragma: no cover - favicon fallback
    Image = None

warnings.filterwarnings("ignore", category=FutureWarning)

ROOT_DIR = Path(__file__).parent
LOGO_PATH = ROOT_DIR / "assets" / "pearlquest-logo.png"
HERO_IMAGE_PATH = ROOT_DIR / "assets" / "wow-pasta.png"
DEFAULT_ICON = "📡"
API_KEY = "abdtsmfubvzj19l39i0uis5oyzerof71"
BASE_URL = "https://app.datarealities.com"
DEFAULT_MAC_ADDRESS = "64:63:06:EE:4B:80"
HEADERS = {"x-api-key": API_KEY}
LIVE_LOOKBACK_MINUTES = 10
MAX_ENGAGEMENT_DISTANCE = 10.0
DEFAULT_ZONE_ORDER = ["Zone 1", "Zone 2", "Zone 3"]


def load_page_icon():
    if Image is not None and LOGO_PATH.exists():
        return Image.open(LOGO_PATH)
    return DEFAULT_ICON


def image_to_base64(path: Path) -> str:
    return base64.b64encode(path.read_bytes()).decode("utf-8")


def get_default_campaign_window(today_value: date) -> tuple[date, date]:
    start_date = today_value.replace(day=1)
    target_year = start_date.year + 1
    target_month = start_date.month
    if target_month == 12:
        next_month = date(target_year + 1, 1, 1)
    else:
        next_month = date(target_year, target_month + 1, 1)
    end_date = next_month - timedelta(days=1)
    return start_date, end_date


st.set_page_config(
    page_title="Zing Marketing Pilot Campaign",
    page_icon=load_page_icon(),
    layout="wide",
    initial_sidebar_state="expanded",
)


def inject_styles():
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;700&family=IBM+Plex+Sans:wght@400;500;600&display=swap');

        :root {
            --bg-0: #06070a;
            --bg-1: #10131b;
            --glass: rgba(18, 24, 36, 0.62);
            --glass-strong: rgba(26, 34, 50, 0.72);
            --glass-border: rgba(255, 255, 255, 0.14);
            --text-0: #f4f7fb;
            --text-1: #9aa7bd;
            --red: #ff4242;
            --orange: #ff9a3d;
            --cyan: #56d5ff;
            --mint: #55e6b1;
        }

        .stApp {
            color: var(--text-0);
            background:
                radial-gradient(circle at 15% 15%, rgba(255, 66, 66, 0.18), transparent 22%),
                radial-gradient(circle at 85% 10%, rgba(86, 213, 255, 0.16), transparent 24%),
                radial-gradient(circle at 50% 100%, rgba(255, 154, 61, 0.12), transparent 24%),
                linear-gradient(180deg, var(--bg-0) 0%, #0a1018 45%, #06070a 100%);
        }

        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, rgba(6, 7, 10, 0.95), rgba(10, 16, 24, 0.94));
            border-right: 1px solid rgba(255, 255, 255, 0.08);
        }

        [data-testid="stSidebar"] * {
            color: var(--text-0) !important;
            font-family: "IBM Plex Sans", sans-serif;
        }

        [data-testid="stSidebar"] [data-baseweb="input"] > div,
        [data-testid="stSidebar"] [data-baseweb="select"] > div {
            background: rgba(255, 255, 255, 0.05) !important;
            border: 1px solid rgba(255, 255, 255, 0.12) !important;
            border-radius: 14px !important;
        }

        .block-container {
            padding-top: 1.5rem;
            padding-bottom: 2.2rem;
        }

        h1, h2, h3, h4 {
            font-family: "Space Grotesk", sans-serif !important;
            color: var(--text-0) !important;
            letter-spacing: -0.03em;
        }

        p, li, label, div, span {
            font-family: "IBM Plex Sans", sans-serif;
        }

        .hero-shell,
        .glass-card,
        .metric-card,
        .bento-card,
        .status-card {
            backdrop-filter: blur(22px);
            -webkit-backdrop-filter: blur(22px);
            border: 1px solid var(--glass-border);
            box-shadow: 0 24px 60px rgba(0, 0, 0, 0.28);
        }

        .hero-shell {
            background: linear-gradient(135deg, rgba(10, 14, 20, 0.88), rgba(24, 30, 45, 0.72));
            border-radius: 32px;
            padding: 1.6rem 1.8rem;
            min-height: 250px;
        }

        .hero-grid {
            display: grid;
            grid-template-columns: minmax(180px, 260px) minmax(0, 1fr);
            gap: 1.2rem;
            align-items: center;
        }

        .hero-logo-shell {
            display: flex;
            align-items: center;
            justify-content: center;
            min-height: 170px;
            border-radius: 24px;
            background: linear-gradient(180deg, rgba(255,255,255,0.03), rgba(255,255,255,0.01));
            border: 1px solid rgba(255,255,255,0.06);
            padding: 1rem;
        }

        .hero-logo-shell img {
            width: 100%;
            max-width: 220px;
            height: auto;
            object-fit: contain;
        }

        .hero-shell .eyebrow {
            color: var(--orange);
            text-transform: uppercase;
            letter-spacing: 0.24em;
            font-size: 0.76rem;
            margin-bottom: 0.7rem;
        }

        .hero-shell h1 {
            margin: 0 0 0.7rem 0;
            font-size: 3rem;
            line-height: 0.98;
        }

        .hero-shell p {
            color: var(--text-1);
            font-size: 1rem;
            max-width: 46rem;
            margin-bottom: 1rem;
        }

        .hero-tags {
            display: flex;
            flex-wrap: wrap;
            gap: 0.6rem;
        }

        .hero-tags span {
            background: rgba(255, 255, 255, 0.06);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 999px;
            padding: 0.42rem 0.8rem;
            color: #eef3ff;
            font-size: 0.82rem;
        }

        .section-title {
            margin: 0 0 0.15rem 0;
            font-size: 1.15rem;
        }

        .section-subtitle {
            color: var(--text-1);
            margin: 0 0 0.95rem 0;
            font-size: 0.92rem;
        }

        .glass-card {
            background: var(--glass);
            border-radius: 26px;
            padding: 1.1rem 1.2rem 0.5rem 1.2rem;
            margin-bottom: 1rem;
        }

        .panel-stack {
            display: grid;
            gap: 1rem;
        }

        .responsive-card-grid {
            display: grid;
            gap: 1rem;
            margin-bottom: 1rem;
        }

        .responsive-card-grid.metrics {
            grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
        }

        .responsive-card-grid.bento {
            grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
        }

        .metric-card {
            background: linear-gradient(180deg, rgba(18, 24, 36, 0.8), rgba(12, 16, 26, 0.7));
            border-radius: 24px;
            padding: 1rem 1.1rem;
            min-height: 140px;
        }

        .metric-card .label {
            color: var(--text-1);
            text-transform: uppercase;
            letter-spacing: 0.08em;
            font-size: 0.72rem;
            margin-bottom: 0.6rem;
        }

        .metric-card .value {
            font-family: "Space Grotesk", sans-serif;
            font-size: 2rem;
            color: #ffffff;
            margin-bottom: 0.4rem;
        }

        .metric-card .hint {
            color: #cad3e3;
            font-size: 0.92rem;
            line-height: 1.45;
        }

        .bento-card {
            background: linear-gradient(160deg, rgba(16, 23, 34, 0.86), rgba(34, 17, 18, 0.76));
            border-radius: 28px;
            padding: 1.1rem 1.2rem;
            min-height: 170px;
        }

        .bento-card.alt {
            background: linear-gradient(160deg, rgba(11, 20, 33, 0.86), rgba(20, 37, 44, 0.78));
        }

        .bento-card .label {
            color: rgba(255, 255, 255, 0.74);
            text-transform: uppercase;
            letter-spacing: 0.1em;
            font-size: 0.72rem;
            margin-bottom: 0.6rem;
        }

        .bento-card .value {
            font-family: "Space Grotesk", sans-serif;
            font-size: 2.4rem;
            color: #ffffff;
            margin-bottom: 0.35rem;
        }

        .bento-card .caption {
            color: #d7deea;
            font-size: 0.94rem;
            line-height: 1.45;
        }

        .status-card {
            background: var(--glass-strong);
            border-radius: 28px;
            padding: 1rem 1.15rem;
            min-height: 170px;
        }

        .status-pill {
            display: inline-flex;
            align-items: center;
            gap: 0.45rem;
            border-radius: 999px;
            padding: 0.35rem 0.72rem;
            font-size: 0.82rem;
            margin-bottom: 0.9rem;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }

        .status-pill.online {
            background: rgba(85, 230, 177, 0.12);
            color: #7ef0c4;
        }

        .status-pill.offline {
            background: rgba(255, 66, 66, 0.12);
            color: #ff9191;
        }

        .status-pill.idle {
            background: rgba(255, 154, 61, 0.14);
            color: #ffc487;
        }

        .status-grid {
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 0.8rem;
        }

        .status-cell {
            background: rgba(255, 255, 255, 0.04);
            border-radius: 18px;
            padding: 0.85rem 0.9rem;
        }

        .status-cell .label {
            color: var(--text-1);
            font-size: 0.76rem;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            margin-bottom: 0.35rem;
        }

        .status-cell .value {
            color: #ffffff;
            font-family: "Space Grotesk", sans-serif;
            font-size: 1.15rem;
        }

        .mini-note {
            color: var(--text-1);
            font-size: 0.84rem;
            margin-top: 0.75rem;
        }

        div[data-testid="stDataFrame"] {
            border-radius: 20px;
            overflow: hidden;
            border: 1px solid rgba(255, 255, 255, 0.08);
        }

        .stAlert {
            border-radius: 18px;
        }

        @media (max-width: 1200px) {
            .hero-shell h1 {
                font-size: 2.45rem;
            }
        }

        @media (max-width: 980px) {
            .hero-grid {
                grid-template-columns: 1fr;
            }

            .hero-logo-shell {
                min-height: 120px;
            }

            .hero-shell {
                padding: 1.25rem;
            }

            .hero-shell h1 {
                font-size: 2.1rem;
            }

            .responsive-card-grid.metrics,
            .responsive-card-grid.bento {
                grid-template-columns: 1fr;
            }

            .status-grid {
                grid-template-columns: 1fr;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def format_dt(value) -> str:
    if value is None or pd.isna(value):
        return "N/A"
    if not isinstance(value, pd.Timestamp):
        value = pd.Timestamp(value)
    return value.strftime("%Y-%m-%d %H:%M:%S")


def safe_float(value, fallback: float = 0.0) -> float:
    try:
        if pd.isna(value):
            return fallback
        return float(value)
    except (TypeError, ValueError):
        return fallback


def normalize_zone_name(label: str, fallback_index: int | None = None) -> str:
    cleaned = str(label).strip().strip('"').strip("'")
    if not cleaned:
        return f"Zone {fallback_index}" if fallback_index else "Unknown Zone"

    digits = re.findall(r"\d+", cleaned)
    if digits:
        return f"Zone {digits[0]}"

    lowered = cleaned.lower()
    if lowered in {"near", "inner"}:
        return "Zone 3"
    if lowered in {"mid", "middle", "medium"}:
        return "Zone 2"
    if lowered in {"far", "outer"}:
        return "Zone 1"
    return cleaned.title()


def zone_order(zone_name: str, fallback_index: int = 99) -> int:
    digits = re.findall(r"\d+", str(zone_name))
    if digits:
        return int(digits[0])
    return fallback_index


def proximity_to_zone(proximity_m: float) -> str:
    if proximity_m <= 1.5:
        return "Zone 3"
    if proximity_m <= 3.5:
        return "Zone 2"
    return "Zone 1"


def parse_zone_dwell_times(zone_string) -> list[dict[str, float]]:
    if zone_string is None or pd.isna(zone_string):
        return []

    text = str(zone_string).strip()
    if not text or text == "{}":
        return []

    zone_items = []

    try:
        payload = json.loads(text)
        if isinstance(payload, dict):
            zone_items = list(payload.items())
    except json.JSONDecodeError:
        cleaned = text.strip("{}")
        parts = [part for part in cleaned.split(";") if part.strip()]
        for index, part in enumerate(parts, start=1):
            pieces = [piece.strip() for piece in part.split(",") if piece.strip()]
            if len(pieces) >= 2:
                zone_items.append((pieces[0], pieces[1]))
            else:
                zone_items.append((f"Zone {index}", 0))

    records = []
    for index, (zone_name, seconds) in enumerate(zone_items, start=1):
        records.append(
            {
                "zone": normalize_zone_name(zone_name, fallback_index=index),
                "seconds": safe_float(seconds),
                "sequence": index,
            }
        )
    return records


def build_zone_dataframe(session_df: pd.DataFrame) -> pd.DataFrame:
    zone_rows = []

    for row in session_df.itertuples(index=False):
        parsed_zones = parse_zone_dwell_times(getattr(row, "zone_dwell_times_json", None))
        if parsed_zones:
            for item in parsed_zones:
                zone_rows.append(
                    {
                        "target_id": row.target_id,
                        "log_creation_time": row.log_creation_time,
                        "event_date": row.event_date,
                        "zone": item["zone"],
                        "seconds": item["seconds"],
                        "sequence": item["sequence"],
                        "zone_source": "sensor",
                    }
                )
            continue

        inferred_zone = proximity_to_zone(safe_float(getattr(row, "proximity_m", 0.0)))
        zone_rows.append(
            {
                "target_id": row.target_id,
                "log_creation_time": row.log_creation_time,
                "event_date": row.event_date,
                "zone": inferred_zone,
                "seconds": safe_float(getattr(row, "dwell_tracking_area_sec", 0.0)),
                "sequence": zone_order(inferred_zone),
                "zone_source": "derived",
            }
        )

    zone_df = pd.DataFrame(zone_rows)
    if zone_df.empty:
        return zone_df

    zone_df["sequence"] = zone_df["sequence"].astype(int)
    return zone_df.sort_values(["log_creation_time", "target_id", "sequence"])


def enrich_sessions(raw_df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    df = raw_df.copy()
    if df.empty:
        return df, pd.DataFrame()

    df["log_creation_time"] = pd.to_datetime(df["log_creation_time"], errors="coerce")
    df["dwell_tracking_area_sec"] = pd.to_numeric(
        df["dwell_tracking_area_sec"], errors="coerce"
    ).fillna(0.0)
    df["proximity_m"] = pd.to_numeric(df["proximity_m"], errors="coerce").fillna(0.0)
    df["event_date"] = df["log_creation_time"].dt.date
    df["event_hour"] = df["log_creation_time"].dt.hour.fillna(0).astype(int)
    clamped_distance = df["proximity_m"].clip(lower=0, upper=MAX_ENGAGEMENT_DISTANCE)
    df["engagement_score"] = (
        df["dwell_tracking_area_sec"] * 0.7
        + (MAX_ENGAGEMENT_DISTANCE - clamped_distance) * 0.3
    ).round(2)
    df["is_impression"] = df["dwell_tracking_area_sec"] >= 2
    df["is_engaged"] = df["dwell_tracking_area_sec"] >= 30
    df["touch_risk"] = df["proximity_m"] < 0.5
    df["loitering"] = df["dwell_tracking_area_sec"] > 300
    df["is_anomaly"] = df["touch_risk"] | df["loitering"]
    reasons = []
    for row in df.itertuples(index=False):
        row_reasons = []
        if row.touch_risk:
            row_reasons.append("Potential touch/collision")
        if row.loitering:
            row_reasons.append("Loitering")
        reasons.append(" | ".join(row_reasons))
    df["anomaly_reason"] = reasons
    df["target_short"] = df["target_id"].astype(str).str[:8]
    zone_df = build_zone_dataframe(df)
    return df.sort_values("log_creation_time"), zone_df


def fetch_sessions(start_dt: datetime, end_dt: datetime, mac_address: str) -> pd.DataFrame:
    url = (
        f"{BASE_URL}/api/sensor-logs/sessions?type=json&mac_address={mac_address}"
        f"&start_time={start_dt.strftime('%Y-%m-%dT%H:%M:%S')}"
        f"&end_time={end_dt.strftime('%Y-%m-%dT%H:%M:%S')}"
    )
    response = requests.get(url, headers=HEADERS, timeout=30)
    response.raise_for_status()
    payload = response.json()
    return pd.DataFrame(payload)


@st.cache_data(ttl=300, show_spinner=False)
def load_historical_data(
    mac_address: str, start_date_value: date, end_date_value: date
) -> tuple[pd.DataFrame, pd.DataFrame]:
    start_dt = datetime.combine(start_date_value, time.min)
    end_dt = datetime.combine(end_date_value, time.max)
    raw_df = fetch_sessions(start_dt, end_dt, mac_address)
    return enrich_sessions(raw_df)


def load_live_data(mac_address: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    end_dt = datetime.now(timezone.utc)
    start_dt = end_dt - timedelta(minutes=LIVE_LOOKBACK_MINUTES)
    raw_df = fetch_sessions(start_dt, end_dt, mac_address)
    return enrich_sessions(raw_df)


def init_state():
    st.session_state.setdefault("live_targets", set())
    st.session_state.setdefault("live_initialized", False)
    st.session_state.setdefault("last_successful_heartbeat", None)
    st.session_state.setdefault("last_sensor_event", None)


def render_section_header(title: str, subtitle: str):
    st.markdown(
        f"""
        <h3 class="section-title">{title}</h3>
        <p class="section-subtitle">{subtitle}</p>
        """,
        unsafe_allow_html=True,
    )


def render_metric_card(label: str, value: str, hint: str):
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="label">{label}</div>
            <div class="value">{value}</div>
            <div class="hint">{hint}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_bento_card(label: str, value: str, caption: str, alt: bool = False):
    extra_class = " alt" if alt else ""
    st.markdown(
        f"""
        <div class="bento-card{extra_class}">
            <div class="label">{label}</div>
            <div class="value">{value}</div>
            <div class="caption">{caption}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_card_grid(cards: list[dict[str, str]], kind: str = "metrics"):
    card_class = "metric-card" if kind == "metrics" else "bento-card"
    grid_class = "metrics" if kind == "metrics" else "bento"
    card_markup = []
    for card in cards:
        extra_class = " alt" if card.get("alt") else ""
        if kind == "metrics":
            card_markup.append(
                f'<div class="{card_class}{extra_class}">'
                f'<div class="label">{card["label"]}</div>'
                f'<div class="value">{card["value"]}</div>'
                f'<div class="hint">{card["hint"]}</div>'
                "</div>"
            )
        else:
            card_markup.append(
                f'<div class="{card_class}{extra_class}">'
                f'<div class="label">{card["label"]}</div>'
                f'<div class="value">{card["value"]}</div>'
                f'<div class="caption">{card["caption"]}</div>'
                "</div>"
            )

    html = f'<div class="responsive-card-grid {grid_class}">{"".join(card_markup)}</div>'
    st.markdown(html, unsafe_allow_html=True)


def style_figure(fig: go.Figure) -> go.Figure:
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0, 0, 0, 0)",
        plot_bgcolor="rgba(0, 0, 0, 0)",
        margin=dict(l=20, r=20, t=20, b=20),
        font=dict(family="IBM Plex Sans, sans-serif", color="#e9f0fb"),
    )
    fig.update_xaxes(showgrid=False, zeroline=False)
    fig.update_yaxes(gridcolor="rgba(255,255,255,0.09)", zeroline=False)
    return fig


def build_daily_summary(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(
            columns=["event_date", "total_footfall", "peak_hour", "conversion_rate"]
        )

    grouped = df.groupby("event_date")
    summary = grouped.agg(
        total_footfall=("target_id", "count"),
        engaged_sessions=("is_engaged", "sum"),
        avg_dwell=("dwell_tracking_area_sec", "mean"),
    )
    peak_hour = grouped["event_hour"].agg(
        lambda values: int(pd.Series(values).mode().iat[0]) if not values.empty else 0
    )
    summary["peak_hour"] = peak_hour
    summary["conversion_rate"] = (
        summary["engaged_sessions"] / summary["total_footfall"].replace(0, 1)
    )
    summary = summary.reset_index()
    return summary


def add_week_buckets(df: pd.DataFrame, start_date_value: date) -> pd.DataFrame:
    if df.empty:
        return df

    enriched_df = df.copy()
    base_date = pd.Timestamp(start_date_value).date()
    enriched_df["days_from_start"] = (
        pd.to_datetime(enriched_df["event_date"]) - pd.Timestamp(base_date)
    ).dt.days
    enriched_df["week_index"] = (enriched_df["days_from_start"] // 7).astype(int) + 1
    enriched_df["week_start"] = pd.to_datetime(base_date) + pd.to_timedelta(
        (enriched_df["week_index"] - 1) * 7, unit="D"
    )
    enriched_df["week_end"] = enriched_df["week_start"] + pd.to_timedelta(6, unit="D")
    enriched_df["week_label"] = enriched_df["week_index"].map(lambda value: f"Week {value}")
    enriched_df["week_display"] = (
        enriched_df["week_label"]
        + " ("
        + enriched_df["week_start"].dt.strftime("%b %d")
        + " - "
        + enriched_df["week_end"].dt.strftime("%b %d")
        + ")"
    )
    return enriched_df


def build_weekly_summary(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(
            columns=[
                "week_index",
                "week_label",
                "week_display",
                "week_start",
                "week_end",
                "total_footfall",
                "peak_hour",
                "conversion_rate",
            ]
        )

    grouped = df.groupby(
        ["week_index", "week_label", "week_display", "week_start", "week_end"], as_index=False
    )
    summary = grouped.agg(
        total_footfall=("target_id", "count"),
        engaged_sessions=("is_engaged", "sum"),
        avg_dwell=("dwell_tracking_area_sec", "mean"),
    )
    peak_hour = grouped["event_hour"].agg(
        lambda values: int(pd.Series(values).mode().iat[0]) if not values.empty else 0
    ).rename(columns={"event_hour": "peak_hour"})
    summary = summary.merge(
        peak_hour,
        on=["week_index", "week_label", "week_display", "week_start", "week_end"],
        how="left",
    )
    summary["conversion_rate"] = (
        summary["engaged_sessions"] / summary["total_footfall"].replace(0, 1)
    )
    return summary.sort_values("week_index")


def build_zone_distribution(zone_df: pd.DataFrame) -> pd.DataFrame:
    if zone_df.empty:
        return pd.DataFrame({"zone": DEFAULT_ZONE_ORDER, "seconds": [0.0, 0.0, 0.0]})

    distribution = zone_df.groupby("zone", as_index=False)["seconds"].sum()
    all_zones = pd.DataFrame({"zone": DEFAULT_ZONE_ORDER})
    distribution = all_zones.merge(distribution, on="zone", how="left").fillna(0.0)
    return distribution


def build_zone_sankey(zone_df: pd.DataFrame, focus_df: pd.DataFrame) -> go.Figure:
    transition_counts: dict[tuple[str, str], int] = {}

    if not zone_df.empty:
        grouped = zone_df.groupby(["target_id", "log_creation_time"], sort=False)
        for _, group in grouped:
            ordered = group.sort_values("sequence")["zone"].tolist()
            if len(ordered) > 1:
                for left, right in zip(ordered[:-1], ordered[1:]):
                    transition_counts[(left, right)] = transition_counts.get((left, right), 0) + 1

    if not transition_counts:
        zone_two_reached = int((focus_df["proximity_m"] <= 3.5).sum())
        zone_three_reached = int((focus_df["proximity_m"] <= 1.5).sum())
        transition_counts[("Zone 1", "Zone 2")] = zone_two_reached
        transition_counts[("Zone 2", "Zone 3")] = zone_three_reached

    labels = DEFAULT_ZONE_ORDER
    label_to_index = {label: idx for idx, label in enumerate(labels)}
    sources = []
    targets = []
    values = []

    for (source, target), value in transition_counts.items():
        if value <= 0:
            continue
        if source not in label_to_index or target not in label_to_index:
            continue
        sources.append(label_to_index[source])
        targets.append(label_to_index[target])
        values.append(value)

    if not values:
        values = [0]
        sources = [0]
        targets = [1]

    fig = go.Figure(
        data=[
            go.Sankey(
                arrangement="snap",
                node=dict(
                    label=labels,
                    pad=22,
                    thickness=18,
                    color=["#374151", "#ff9a3d", "#ff4242"],
                    line=dict(color="rgba(255,255,255,0.1)", width=1),
                ),
                link=dict(
                    source=sources,
                    target=targets,
                    value=values,
                    color=[
                        "rgba(86, 213, 255, 0.35)"
                        if labels[source] == "Zone 1"
                        else "rgba(255, 154, 61, 0.35)"
                        for source in sources
                    ],
                ),
            )
        ]
    )
    return style_figure(fig)


def build_anomaly_table(df: pd.DataFrame) -> pd.DataFrame:
    anomaly_df = df.loc[df["is_anomaly"]].copy()
    if anomaly_df.empty:
        return anomaly_df

    anomaly_df["log_creation_time"] = anomaly_df["log_creation_time"].dt.strftime(
        "%Y-%m-%d %H:%M:%S"
    )
    return anomaly_df[
        [
            "log_creation_time",
            "target_short",
            "dwell_tracking_area_sec",
            "proximity_m",
            "engagement_score",
            "anomaly_reason",
        ]
    ].rename(
        columns={
            "log_creation_time": "Timestamp",
            "target_short": "Target",
            "dwell_tracking_area_sec": "Dwell (s)",
            "proximity_m": "Proximity (m)",
            "engagement_score": "Engagement Score",
            "anomaly_reason": "Flag",
        }
    )


def render_header(start_date_value: date, end_date_value: date):
    logo_markup = ""
    hero_image_path = HERO_IMAGE_PATH if HERO_IMAGE_PATH.exists() else LOGO_PATH
    if hero_image_path.exists():
        logo_markup = (
            f'<div class="hero-logo-shell"><img src="data:image/png;base64,{image_to_base64(hero_image_path)}" '
            'alt="Campaign logo"></div>'
        )

    st.markdown(
        f"""
        <div class="hero-shell">
            <div class="hero-grid">
                {logo_markup}
                <div>
                    <div class="eyebrow">Powered by PearlQuest</div>
                    <h1>Zing Marketing Pilot Campaign, Powered by PearlQuest</h1>
                    <p>
                        Weekly campaign performance, engagement intelligence, and live audience monitoring
                        for the WOW Pasta pilot activation powered by PearlQuest.
                    </p>
                    <div class="hero-tags">
                        <span>Campaign window: {start_date_value} to {end_date_value}</span>
                    </div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_status_card(
    status: str,
    latest_target: str,
    current_target_count: int,
    new_target_count: int,
    last_seen_value,
    heartbeat_value,
    message: str,
):
    status_class = {"ONLINE": "online", "OFFLINE": "offline"}.get(status, "idle")
    st.markdown(
        f"""
        <div class="status-card">
            <div class="status-pill {status_class}">{status}</div>
            <div class="status-grid">
                <div class="status-cell">
                    <div class="label">Latest Target</div>
                    <div class="value">{latest_target}</div>
                </div>
                <div class="status-cell">
                    <div class="label">Active Targets</div>
                    <div class="value">{current_target_count}</div>
                </div>
                <div class="status-cell">
                    <div class="label">New This Poll</div>
                    <div class="value">{new_target_count}</div>
                </div>
                <div class="status-cell">
                    <div class="label">Last Sensor Event</div>
                    <div class="value">{format_dt(last_seen_value)}</div>
                </div>
            </div>
            <div class="mini-note">Last successful heartbeat: {format_dt(heartbeat_value)}</div>
            <div class="mini-note">{message}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


init_state()
inject_styles()

mac_address = DEFAULT_MAC_ADDRESS
today = date.today()
start_date_value, end_date_value = get_default_campaign_window(today)

if start_date_value > end_date_value:
    st.error("Start date must be before or equal to the end date.")
    st.stop()

render_header(start_date_value, end_date_value)

try:
    historical_df, historical_zone_df = load_historical_data(
        mac_address, start_date_value, end_date_value
    )
except requests.RequestException as exc:
    st.error(f"Unable to load historical sessions from the sensor API: {exc}")
    st.stop()

if historical_df.empty:
    st.warning("No historical sessions were returned for the selected range.")
    st.stop()

historical_df = add_week_buckets(historical_df, start_date_value)
historical_zone_df = historical_zone_df.merge(
    historical_df[
        ["target_id", "log_creation_time", "week_index", "week_label", "week_display", "week_start", "week_end"]
    ],
    on=["target_id", "log_creation_time"],
    how="left",
)
weekly_summary = build_weekly_summary(historical_df)

if weekly_summary.empty:
    st.warning("No weekly buckets were generated for the selected range.")
    st.stop()

with st.sidebar:
    if LOGO_PATH.exists():
        st.image(str(LOGO_PATH), width="stretch")
    st.markdown("## Focus Week")
    week_options = weekly_summary["week_index"].tolist()
    focus_week_index = st.selectbox(
        "Focus Week",
        options=week_options,
        index=len(week_options) - 1,
        format_func=lambda value: weekly_summary.loc[
            weekly_summary["week_index"] == value, "week_display"
        ].iloc[0],
    )
    st.caption("Campaign period is fixed from the start of this month through the same month next year.")

focus_week_meta = weekly_summary.loc[
    weekly_summary["week_index"] == focus_week_index
].iloc[0]
focus_df = historical_df.loc[historical_df["week_index"] == focus_week_index].copy()
focus_zone_df = historical_zone_df.loc[
    historical_zone_df["week_index"] == focus_week_index
].copy()

if focus_df.empty:
    st.warning("No sessions were found for the selected focus week.")
    st.stop()

total_footfall = int(len(focus_df))
peak_hour = int(focus_df["event_hour"].mode().iat[0]) if not focus_df.empty else 0
conversion_rate = (
    float(focus_df["is_engaged"].mean()) if total_footfall else 0.0
)
impressions = int(focus_df["is_impression"].sum())
engagements = int(focus_df["is_engaged"].sum())
avg_dwell = float(focus_df["dwell_tracking_area_sec"].mean()) if total_footfall else 0.0
avg_engagement_score = (
    float(focus_df["engagement_score"].mean()) if total_footfall else 0.0
)
anomaly_count = int(focus_df["is_anomaly"].sum())

summary_cards = [
    {
        "label": "Total Footfall",
        "value": f"{total_footfall:,}",
        "hint": "Total visitor sessions recorded within the selected week.",
    },
    {
        "label": "Peak Hour",
        "value": f"{peak_hour:02d}:00",
        "hint": "Most active hour across all sessions in the selected week.",
    },
    {
        "label": "Average Dwell Time",
        "value": f"{avg_dwell:.1f}s",
        "hint": "Average time spent inside the tracking area for the selected week.",
    },
    {
        "label": "Avg Engagement Score",
        "value": f"{avg_engagement_score:.1f}",
        "hint": "Blended dwell and proximity score per session.",
    },
]

bento_cards = [
    {
        "label": "Impressions (2s+)",
        "value": f"{impressions:,}",
        "caption": "Targets that remained in view long enough to register attention this week.",
    },
    {
        "label": "Engagements (30s+)",
        "value": f"{engagements:,}",
        "caption": "High-intent sessions that crossed the engagement threshold this week.",
        "alt": True,
    },
]


@st.fragment(run_every="2s")
def render_live_monitor():
    render_section_header(
        "Live Sensor Feed",
        "Polling every 2 seconds with diff-based new target detection.",
    )
    try:
        live_df, _ = load_live_data(mac_address)
        heartbeat_now = pd.Timestamp.utcnow().tz_localize(None)
        st.session_state["last_successful_heartbeat"] = heartbeat_now
        status = "ONLINE"
        message = "API reachable and live polling is healthy."

        if live_df.empty:
            st.session_state["live_targets"] = set()
            render_status_card(
                status="IDLE",
                latest_target="No recent targets",
                current_target_count=0,
                new_target_count=0,
                last_seen_value=st.session_state["last_sensor_event"],
                heartbeat_value=st.session_state["last_successful_heartbeat"],
                message="API is responding, but no targets were seen in the last 10 minutes.",
            )
            return

        live_df = live_df.sort_values("log_creation_time")
        current_targets = set(live_df["target_id"].astype(str))
        previous_targets = st.session_state.get("live_targets", set())
        new_targets = sorted(current_targets - previous_targets)

        if st.session_state["live_initialized"] and new_targets:
            st.toast(
                f"New Target Detected: {new_targets[0][:8]} ({len(new_targets)} new)",
                icon="🚨",
            )

        st.session_state["live_targets"] = current_targets
        st.session_state["live_initialized"] = True
        latest_row = live_df.iloc[-1]
        st.session_state["last_sensor_event"] = latest_row["log_creation_time"]

        render_status_card(
            status=status,
            latest_target=str(latest_row["target_id"])[:8],
            current_target_count=len(current_targets),
            new_target_count=len(new_targets),
            last_seen_value=latest_row["log_creation_time"],
            heartbeat_value=st.session_state["last_successful_heartbeat"],
            message=message,
        )
    except requests.RequestException as exc:
        render_status_card(
            status="OFFLINE",
            latest_target="Unavailable",
            current_target_count=0,
            new_target_count=0,
            last_seen_value=st.session_state["last_sensor_event"],
            heartbeat_value=st.session_state["last_successful_heartbeat"],
            message=f"Sensor Offline: {exc}",
        )


overview_left, overview_right = st.columns([1.7, 1.0], gap="large")
with overview_left:
    st.markdown(
        f'<p class="mini-note">Viewing {focus_week_meta["week_display"]}.</p>',
        unsafe_allow_html=True,
    )
    render_card_grid(summary_cards, kind="metrics")
    render_card_grid(bento_cards, kind="bento")

with overview_right:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    render_live_monitor()
    st.markdown("</div>", unsafe_allow_html=True)

chart_top = st.columns(2, gap="large")

with chart_top[0]:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    render_section_header(
        "Week-Wise Footfall Trend",
        "Weekly rollup across the selected date range for quick performance comparison.",
    )
    trend_df = weekly_summary.copy()
    fig_daily = go.Figure()
    fig_daily.add_trace(
        go.Scatter(
            x=trend_df["week_label"],
            y=trend_df["total_footfall"],
            mode="lines+markers",
            fill="tozeroy",
            line=dict(color="#56d5ff", width=3),
            marker=dict(size=8, color="#ff9a3d"),
            name="Weekly Footfall",
            text=trend_df["week_display"],
            hovertemplate="%{text}<br>Footfall: %{y}<extra></extra>",
        )
    )
    fig_daily.update_xaxes(title="Week")
    fig_daily.update_yaxes(title="Sessions")
    st.plotly_chart(style_figure(fig_daily), use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

with chart_top[1]:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    render_section_header(
        "Zone Dwell Radar",
        "Weekly zone dwell distribution using sensor zones when available, otherwise proximity-derived fallback zones.",
    )
    zone_distribution = build_zone_distribution(focus_zone_df)
    polar_theta = zone_distribution["zone"].tolist()
    polar_r = zone_distribution["seconds"].tolist()
    fig_radar = go.Figure()
    fig_radar.add_trace(
        go.Scatterpolar(
            r=polar_r + polar_r[:1],
            theta=polar_theta + polar_theta[:1],
            fill="toself",
            line=dict(color="#ff4242", width=3),
            marker=dict(color="#ff9a3d", size=9),
            name="Zone Dwell",
        )
    )
    fig_radar.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        polar=dict(
            bgcolor="rgba(0,0,0,0)",
            radialaxis=dict(
                gridcolor="rgba(255,255,255,0.12)",
                linecolor="rgba(255,255,255,0.16)",
            ),
            angularaxis=dict(gridcolor="rgba(255,255,255,0.08)"),
        ),
        margin=dict(l=20, r=20, t=20, b=20),
        font=dict(family="IBM Plex Sans, sans-serif", color="#e9f0fb"),
    )
    st.plotly_chart(fig_radar, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

chart_middle = st.columns(2, gap="large")

with chart_middle[0]:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    render_section_header(
        "Zone Progression Flow",
        "Sankey view of zone movement during the selected week. Falls back to inferred progression from proximity when path data is missing.",
    )
    st.plotly_chart(build_zone_sankey(focus_zone_df, focus_df), use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

with chart_middle[1]:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    render_section_header(
        "Hourly Engagement Heatmap",
        "Hour-by-hour pattern of average engagement score across the selected week.",
    )
    heatmap_df = (
        focus_df.groupby("event_hour", as_index=False)["engagement_score"].mean()
        .rename(columns={"event_hour": "Hour", "engagement_score": "Avg Score"})
    )
    heat_values = [heatmap_df["Avg Score"].tolist()]
    fig_heatmap = go.Figure(
        data=
        [
            go.Heatmap(
                z=heat_values,
                x=heatmap_df["Hour"].tolist(),
                y=["Engagement Score"],
                colorscale=[
                    [0.0, "#132135"],
                    [0.4, "#235c93"],
                    [0.7, "#ff9a3d"],
                    [1.0, "#ff4242"],
                ],
                colorbar=dict(title="Score"),
            )
        ]
    )
    fig_heatmap.update_xaxes(title="Hour of Day")
    st.plotly_chart(style_figure(fig_heatmap), use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

chart_bottom = st.columns(2, gap="large")

with chart_bottom[0]:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    render_section_header(
        "Session Scatter",
        "Weekly dwell time versus proximity.",
    )
    fig_scatter = go.Figure()
    fig_scatter.add_trace(
        go.Scatter(
            x=focus_df["proximity_m"],
            y=focus_df["dwell_tracking_area_sec"],
            mode="markers",
            marker=dict(color="#56d5ff", size=8, opacity=0.65),
            name="Sessions",
            text=focus_df["target_short"],
        )
    )
    fig_scatter.update_xaxes(title="Proximity (m)")
    fig_scatter.update_yaxes(title="Dwell Time (s)")
    st.plotly_chart(style_figure(fig_scatter), use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

with chart_bottom[1]:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    render_section_header(
        f"View Structured Session Table For {focus_week_meta['week_label']}",
        "Detailed session records for the selected week.",
    )
    session_table = focus_df[
        [
            "log_creation_time",
            "target_id",
            "dwell_tracking_area_sec",
            "proximity_m",
            "engagement_score",
            "is_anomaly",
            "anomaly_reason",
        ]
    ].sort_values("log_creation_time", ascending=False)
    st.dataframe(session_table, use_container_width=True, hide_index=True)
    st.markdown("</div>", unsafe_allow_html=True)
