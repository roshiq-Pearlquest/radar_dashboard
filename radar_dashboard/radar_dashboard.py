import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import warnings

warnings.filterwarnings("ignore", category=FutureWarning)

# Configuration
st.set_page_config(page_title="Radar Analytics", layout="wide")
API_KEY = "abdtsmfubvzj19l39i0uis5oyzerof71"
BASE_URL = "https://app.datarealities.com"

st.sidebar.header("API Settings")
mac_address = st.sidebar.text_input("MAC Address", value="64:63:06:EE:4B:80")
start_time = st.sidebar.text_input("Start Time", value="2026-04-01T00:00:00")
end_time = st.sidebar.text_input("End Time", value="2026-04-10T23:59:59")

HEADERS = {"x-api-key": API_KEY}


def parse_zones(zone_string):
    """Helper to turn the strange JSON string into a clean dictionary"""
    try:
        cleaned = zone_string.replace("{", "").replace("}", "").replace('"', "")
        pairs = cleaned.split(";")
        return {p.split(",")[0]: float(p.split(",")[1]) for p in pairs if "," in p}
    except:
        return {}


st.title("📡 Radar Session Intelligence")


@st.fragment(run_every="3s")
def build_dashboard():
    try:
        api_url = f"{BASE_URL}/api/sensor-logs/sessions?type=json&mac_address={mac_address}&start_time={start_time}&end_time={end_time}"
        response = requests.get(api_url, headers=HEADERS, timeout=5)
        all_sessions = response.json()
        df = pd.DataFrame(all_sessions)

        if df.empty:
            st.warning("No session data found yet.")
            return

        latest = df.iloc[0]
        st.subheader(f"Latest Target: {latest['target_id'][:8]}...")

        m1, m2, m3 = st.columns(3)
        m1.metric("Time in View", f"{latest['dwell_tracking_area_sec']}s")
        m2.metric("Min Proximity", f"{latest['proximity_m']}m")
        m3.metric("Sensor Status", "Online", delta="Active")

        st.divider()
        col_left, col_right = st.columns(2)

        with col_left:
            st.write("### ⏱️ Dwell Time per Session")
            st.bar_chart(df, x="log_creation_time", y="dwell_tracking_area_sec")

        with col_right:
            st.write("### 📍 Zone Breakdown (Latest)")
            zones = parse_zones(latest["zone_dwell_times_json"])
            if zones:
                zone_df = pd.DataFrame(list(zones.items()), columns=["Zone", "Seconds"])
                fig = px.pie(zone_df, values="Seconds", names="Zone", hole=0.4)
                st.plotly_chart(fig, width="stretch")

        with st.expander("View Raw Session Logs"):
            st.dataframe(df, width="stretch")

    except Exception as e:
        st.error(f"Connection Error: {e}")


build_dashboard()
