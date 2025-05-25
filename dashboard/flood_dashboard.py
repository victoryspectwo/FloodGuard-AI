import streamlit as st
import pandas as pd
import joblib
import sys
import os
import streamlit.components.v1 as components
from datetime import datetime
import subprocess

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# --- Import shared functions ---
from data_processing.fetch_api import fetch_rainfall_df, fetch_forecast_df
from data_processing.feature_engineering import fuzzy_merge_forecast, apply_time_features
from data_processing.forecast_map import forecast_map

# --- Load trained model ---
model = joblib.load(os.path.join(os.path.dirname(__file__), '..', 'models', 'flood_predictor_xgb.pkl'))

now = datetime.now()
current_time = now.strftime("%H:%M:%S")

flooding_flag = False
demo_mode_on = False

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

# --- Streamlit UI and tabs ---
st.set_page_config(page_title="FloodGuard AI", layout="wide")

if 'flood_df' not in st.session_state:
    st.session_state.flood_df = pd.DataFrame()
if 'flooding_flag' not in st.session_state:
    st.session_state.flooding_flag = False
if 'demo_mode_on' not in st.session_state:
    st.session_state.demo_mode_on = False

st.title("🌧️ FloodGuard AI — Flood Prediction Dashboard")

tab1, tab2, tab3 = st.tabs(["🌧️ Prediction", "🧠 AI Summary", "🗺️ Rerouting"])

with tab1:
    simulate = st.checkbox("🕓 Demo mode (use historical_data.csv instead of live APIs)")
    if simulate:
        st.session_state.demo_mode_on = True
        st.info("🕓 Demo mode ON — loading historical_data.csv...")
        df = pd.read_csv("../historical_data.csv")
        st.session_state.df = df

    else:
        st.session_state.demo_mode_on = False
        st.session_state.df = None

    st.markdown("### 📍 Rainfall Stations near/at Roads")
    try:
        display_df = get_live_data()
        st.map(display_df[['latitude', 'longitude']], zoom=10)
    except Exception as e:
        st.warning(f"⚠️ Unable to load rainfall map. {str(e)}")


    if st.button("🔄 Run Flood Prediction", key="predict_btn"):
        with st.spinner("Predicting flood risk..."):
            if not st.session_state.demo_mode_on:
                df = get_live_data()

            df = predict_flood(df)
            st.session_state.df = df 
            print(df)
            st.session_state.flood_df = df[df['flood_prediction'] == 1]

            if st.session_state.flood_df.empty:
                st.success(f"✅ No flood risk predicted as of {current_time}, {now.date()}")
                flooding_flag = False
            else:
                st.error(f"🚨 Flood risk at {len(st.session_state.flood_df)} location(s)!")
                st.dataframe(st.session_state.flood_df[['location', 'rainfall', 'forecast', 'latitude', 'longitude']])
                st.markdown("### 📍 Rainfall Stations recording flooded areas")
                st.map(st.session_state.flood_df[['latitude', 'longitude']])
                flooding_flag = True

            st.subheader("📋 All Station Data")
            st.dataframe(df[['location', 'rainfall', 'forecast', 'flood_prediction']])

with tab2:
    st.markdown("### 🧠 AI Summary from News + Telegram")
    
    if st.session_state.demo_mode_on:
        st.caption("📡 Fetching latest alerts and generating summary...")
        try:
            import subprocess
            subprocess.run(["python", "../webscraper.py"], check=True)
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
    if st.session_state.demo_mode_on or not st.session_state.flood_df.empty:
        if st.button("🚍 Reroute flooded bus", key="reroute_btn"):
            st.markdown("### 🗺️ Bus Rerouting Map")
            map_path = os.path.abspath("floodguard_dual_route_map.html")
            with open(map_path, 'r', encoding='utf-8') as HtmlFile:
                source_code = HtmlFile.read()
                components.html(source_code, height=500, scrolling=True)
    else:
        st.info("⚠️ Run flood prediction or enable demo mode before accessing rerouting.")
