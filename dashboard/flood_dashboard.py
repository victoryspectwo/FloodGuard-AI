import streamlit as st
import pandas as pd
import joblib
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# --- Import shared functions ---
from data_processing.fetch_api import fetch_rainfall_df, fetch_forecast_df
from data_processing.feature_engineering import fuzzy_merge_forecast, apply_time_features
from data_processing.forecast_map import forecast_map

# --- Load trained model ---
model = joblib.load("models/flood_predictor_xgb.pkl")

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

# --- Streamlit UI ---
st.set_page_config(page_title="FloodGuard AI", layout="wide")
st.title("🌧️ FloodGuard AI — Flood Prediction Dashboard")

simulate = st.checkbox("🕓 Backtest mode (use historical_data.csv instead of live APIs)")

if simulate:
    st.info("🕓 Backtesting mode ON — loading historical_data.csv...")
    df = pd.read_csv("historical_data.csv")
else:
    df = get_live_data()

st.write("📍 Rainfall Stations near/at Roads")
st.map(df[['latitude', 'longitude']], zoom=10)

if st.button("🔄 Run Flood Prediction"):
    with st.spinner("Predicting flood risk..."):
        df = predict_flood(df)
        flood_df = df[df['flood_prediction'] == 1]

        if flood_df.empty:
            st.success("✅ No flood risk predicted.")
        else:
            st.error(f"🚨 Flood risk at {len(flood_df)} location(s)!")
            st.dataframe(flood_df[['location', 'rainfall', 'forecast', 'latitude', 'longitude']])
            st.map(flood_df[['latitude', 'longitude']])

        st.subheader("📋 All Station Data")
        st.dataframe(df[['location', 'rainfall', 'forecast', 'flood_prediction']])
