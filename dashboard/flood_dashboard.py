import streamlit as st
import pandas as pd
import joblib
import sys
import os
import streamlit.components.v1 as components
from datetime import datetime
import subprocess
import json
import requests
import folium
from geopy.distance import geodesic
from folium.plugins import Fullscreen
from streamlit_folium import folium_static, st_folium
from streamlit_autorefresh import st_autorefresh


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# --- Import shared functions ---
from data_processing.fetch_api import fetch_rainfall_df, fetch_forecast_df
from data_processing.feature_engineering import fuzzy_merge_forecast, apply_time_features
from data_processing.forecast_map import forecast_map

# --- Load trained model ---
model = joblib.load(os.path.join(os.path.dirname(__file__), '..', 'models', 'flood_predictor_xgb.pkl'))

now = datetime.now()
current_time = now.strftime("%H:%M:%S")


# --- Telegram Alert Function ---
def send_telegram_alert(affected_bus_data, flooded_ids, bus_stops_dict):
    bot_token = "7584074211:AAFhJiQhp72hpxGp3QV3Aqo-eOKAAyc6v8M"
    chat_ids = ["1201658699", "5178625508"]

    alert_lines = []
    for bus_number, data in affected_bus_data.items():
        flooded_stops = [sid for sid in data["stops"] if sid in flooded_ids]
        if flooded_stops:
            stop_names = [bus_stops_dict[sid]["name"] for sid in flooded_stops if sid in bus_stops_dict]
            alert_lines.append(f"• *Bus {bus_number}* — {', '.join(stop_names)}")

    if not alert_lines:
        st.info("✅ No flooded stops to alert.")
        return

    message = (
        "*🚨 URGENT FLOOD ALERT:*\n\n"
        "The following bus services are currently affected by possible flooding at nearby stops:\n\n"
        f"{chr(10).join(alert_lines)}\n\n"
        "⚠️ Please *inform all relevant bus drivers immediately* and monitor traffic along these routes. "
        "Drivers are advised to approach with caution or take alternate paths if necessary.\n\n"
        "— FloodGuard AI"
    )

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    for chat_id in chat_ids:
        payload = {"chat_id": chat_id, "text": message, "parse_mode": "Markdown"}
        r = requests.post(url, data=payload)

    if r.status_code == 200:
        st.success(f"✅ Alert successfully sent to bus operators")
    else:
        st.error(f"❌ Failed to send alert to {chat_id}: {r.text}")

# --- Live data pipeline ---
def get_live_data():
    rain_df = fetch_rainfall_df()
    forecast_df = fetch_forecast_df()

    rain_df = rain_df[rain_df['location'].str.contains(
        "Road|Street|Avenue|Drive|Expressway|Ave|Lane", case=False, na=False
    )]

    rain_df = fuzzy_merge_forecast(rain_df, forecast_df)
    rain_df = apply_time_features(rain_df)
    return rain_df

# --- Prediction wrapper ---
def predict_flood(df):
    features = ['rainfall', 'forecast_num', 'latitude', 'longitude', 'hour', 'dayofweek']
    df['flood_prediction'] = model.predict(df[features])
    return df

# --- Rerouting logic ---
def load_reroute_data():
    base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data'))
    
    # ✅ Select appropriate file and label based on mode
    if st.session_state.get("demo_mode_on", False):
        data_file = os.path.join(base_path, "historical_data.csv")
        label_column = "flood_label"
    else:
        data_file = os.path.join(base_path, "predicted_data.csv")
        label_column = "flood_prediction"

    bus_stops_file = os.path.join(base_path, "bus-stops.json")
    bus_services_dir = os.path.join(base_path, "bus-services")

    flood_df = pd.read_csv(data_file)
    flood_df = flood_df[flood_df[label_column] == 1]

    # Fetch station coordinates from API
    api_url = "https://api.data.gov.sg/v1/environment/rainfall"
    try:
        response = requests.get(api_url)
        stations_data = response.json().get("metadata", {}).get("stations", [])
        station_coords = {
            station["name"]: (
                station["location"]["latitude"],
                station["location"]["longitude"]
            ) for station in stations_data
        }
    except Exception:
        station_coords = {}

    flood_locations = []
    for road in flood_df['location'].unique():
        if road in station_coords:
            lat, lon = station_coords[road]
            flood_locations.append((road, lat, lon))

    with open(bus_stops_file, "r") as f:
        bus_stops = json.load(f)

    bus_stops_dict = {
        sid: {
            "stop_id": sid,
            "name": data["name"],
            "lat": float(data["coords"].split(",")[1]),
            "lon": float(data["coords"].split(",")[0])
        }
        for sid, data in bus_stops.items()
    }

    flooded_stops = []
    for stop in bus_stops_dict.values():
        for _, lat, lon in flood_locations:
            if geodesic((stop["lat"], stop["lon"]), (lat, lon)).meters < 200:
                flooded_stops.append(stop)
                break
    flooded_ids = {s["stop_id"] for s in flooded_stops}

    affected_bus_data = {}

    for fname in os.listdir(bus_services_dir):
        if not fname.endswith(".json"):
            continue

        bus_number = fname.replace(".json", "")
        with open(os.path.join(bus_services_dir, fname), "r") as f:
            data = json.load(f)

        route_data = data.get("1", {})
        route_coords = route_data.get("route", [])
        stop_ids = route_data.get("stops", [])

        if not route_coords or not stop_ids:
            continue

        if not any(stop_id in flooded_ids for stop_id in stop_ids):
            continue

        affected_bus_data[bus_number] = {
            "coords": route_coords,
            "stops": stop_ids
        }

    return flood_locations, bus_stops_dict, flooded_ids, affected_bus_data

# --- Streamlit UI and tabs ---
st.set_page_config(page_title="FloodGuard AI", layout="wide")

if 'flood_df' not in st.session_state:
    st.session_state.flood_df = pd.DataFrame()
if 'flooding_flag' not in st.session_state:
    st.session_state.flooding_flag = False
if 'demo_mode_on' not in st.session_state:
    st.session_state.demo_mode_on = False

st.title("🌧️ FloodGuard AI — Flood Prediction Dashboard")

tab1, tab2, tab3 = st.tabs(["🌧️ Prediction", "🧠 AI Summary", "🗺️ Bus Routes Affected"])

with tab1:
    simulate = st.checkbox("🕓 Demo mode (use historical_data.csv instead of live APIs)")
    if simulate:
        st.session_state.demo_mode_on = True
        st.info("🕓 Demo mode ON — loading historical_data.csv...")
        df = pd.read_csv("../data/historical_data.csv")
        st.session_state.df = df
    else:
        st.session_state.demo_mode_on = False
        st.session_state.df = None

    st.markdown("### 📍 Rainfall Stations near/at Roads")
    st.caption(f"🔁 Auto-refreshes every 60 seconds — Last updated at {current_time}")

    # 🔁 Auto-refresh every 60 seconds
    count = st_autorefresh(interval=60 * 1000, key="auto_refresh")

    # Always show rainfall map first
    try:
        raw_df = get_live_data()
        rain_map = folium.Map(location=[1.3521, 103.8198], zoom_start=11)
        for _, row in raw_df.iterrows():
            folium.Marker(
                [row['latitude'], row['longitude']],
                popup=f"{row['location']}<br>Rainfall: {row['rainfall']:.2f} mm",
                icon=folium.Icon(color="blue", icon="cloud")
            ).add_to(rain_map)
        folium_static(rain_map, width=1600, height=600)
    except Exception as e:
        st.warning(f"⚠️ Could not load rainfall station map: {e}")

    # Run flood prediction logic every refresh
    with st.spinner("Auto-refreshing flood prediction..."):
        if not st.session_state.demo_mode_on:
            df = get_live_data()
        else:
            df = st.session_state.df

        df = predict_flood(df)
        st.session_state.df = df
        df.to_csv("../data/predicted_data.csv", index=False)  # ✅ Save predictions

        # ✅ Use correct column depending on mode
        if st.session_state.demo_mode_on:
            st.session_state.flood_df = df[df['flood_label'] == 1]
        else:
            st.session_state.flood_df = df[df['flood_prediction'] == 1]

        if st.session_state.flood_df.empty:
            st.success(f"✅ No flood risk predicted as of {current_time}, {now.date()}")
        else:
            st.error(f"🚨 Flood risk at {len(st.session_state.flood_df)} location(s)!")
            st.dataframe(st.session_state.flood_df[['location', 'rainfall', 'forecast', 'latitude', 'longitude']])
            st.markdown("### 📍 Rainfall Stations recording flooded areas")

            # Only show flood-specific markers if flood detected
            flood_map = folium.Map(location=[1.3521, 103.8198], zoom_start=11)
            for _, row in st.session_state.flood_df.iterrows():
                folium.Marker(
                    [row['latitude'], row['longitude']],
                    popup=f"{row['location']}<br>Rainfall: {row['rainfall']:.2f} mm",
                    icon=folium.Icon(color="red", icon="exclamation-sign")
                ).add_to(flood_map)
            folium_static(flood_map, width=1600, height=600)

        st.subheader("📋 All Station Data")
        st.dataframe(df[['location', 'rainfall', 'forecast', 'flood_prediction']])

with tab2:
    st.markdown("### 🧠 AI Summary from News + Telegram")
    if st.session_state.demo_mode_on:
        st.caption("📡 Fetching latest alerts and generating summary...")
        try:
            subprocess.run([sys.executable, "webscraper.py"], check=True, cwd="../llm")
            st.success("✅ Summary refreshed.")
        except Exception as e:
            st.warning(f"⚠️ Could not update summary: {e}")
    try:
        with open("../llm/deepseek.txt", "r", encoding="utf-8") as f:
            summary = f.read()
        st.info(summary)
    except FileNotFoundError:
        st.warning("No DeepSeek summary file found.")

with tab3:
    st.markdown("### 🗺️ Bus Routes Affected Map")

    flood_locations, bus_stops_dict, flooded_ids, affected_bus_data = load_reroute_data()

    affected_bus_numbers = sorted(affected_bus_data.keys())
    bus_selection = st.multiselect(
        "Select Affected Bus Numbers:",
        options=["Select All"] + affected_bus_numbers,
        default=["Select All"]
    )

    if "Select All" in bus_selection:
        selected_buses = affected_bus_numbers
    else:
        selected_buses = [b for b in bus_selection if b in affected_bus_numbers]

    m = folium.Map(location=[1.3521, 103.8198], zoom_start=12)
    folium.TileLayer("cartodbpositron").add_to(m)
    Fullscreen(position='topright').add_to(m)

    for road, lat, lon in flood_locations:
        folium.Marker(
            location=[lat, lon],
            popup=f"Flood at {road}",
            icon=folium.Icon(color='orange', icon='tint', prefix='fa')
        ).add_to(m)

    for bus_number in selected_buses:
        data = affected_bus_data[bus_number]
        route_coords = data["coords"]
        stop_ids = data["stops"]

        fg = folium.FeatureGroup(name=f"Bus {bus_number}")
        latlons = [(float(latlng.split(",")[1]), float(latlng.split(",")[0])) for latlng in route_coords]
        folium.PolyLine(latlons, color='blue', weight=4, tooltip=f"Bus {bus_number} Route").add_to(fg)

        for sid in stop_ids:
            if sid not in bus_stops_dict:
                continue
            stop = bus_stops_dict[sid]
            is_flooded = sid in flooded_ids
            marker_text = f"Flooded: {stop['name']}" if is_flooded else stop['name']
            folium.Marker(
                location=[stop["lat"], stop["lon"]],
                popup=marker_text,
                icon=folium.Icon(color='red' if is_flooded else 'green', icon='bus', prefix='fa')
            ).add_to(fg)

        fg.add_to(m)

    folium.LayerControl(collapsed=False).add_to(m)
    st_data = st_folium(m, use_container_width=True, height=700, returned_objects=[])
    if affected_bus_data and flooded_ids:
        send_telegram_alert(affected_bus_data, flooded_ids, bus_stops_dict)
