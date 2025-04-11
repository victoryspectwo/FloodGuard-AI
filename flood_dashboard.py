import streamlit as st
import pandas as pd
import requests
import joblib
from datetime import datetime

# Load model
model = joblib.load("flood_predictor_xgb.pkl")

# Forecast mapping
forecast_map = {
    "Thundery Showers": 2,
    "Showers": 1,
    "Cloudy": 0,
    "Partly Cloudy (Day)": 0,
    "Partly Cloudy (Night)": 0,
    "Fair (Day)": 0,
    "Fair (Night)": 0
}

# ----------------------------------------
# Get rainfall and forecast data
# ----------------------------------------
def get_live_data():
    # Rainfall API
    rain_url = "https://api-open.data.gov.sg/v2/real-time/api/rainfall"
    r = requests.get(rain_url)
    rain_json = r.json()

    stations = {s['id']: {
        'name': s['name'],
        'latitude': s['location']['latitude'],
        'longitude': s['location']['longitude']
    } for s in rain_json['data']['stations']}

    readings = rain_json['data']['readings'][0]
    timestamp = readings['timestamp']
    rain_rows = []
    for r in readings['data']:
        sid = r['stationId']
        rain_rows.append({
            'timestamp': timestamp,
            'station_id': sid,
            'rainfall': r['value'],
            'latitude': stations[sid]['latitude'],
            'longitude': stations[sid]['longitude'],
            'location': stations[sid]['name']
        })

    df_rain = pd.DataFrame(rain_rows)
    df_rain['timestamp'] = pd.to_datetime(df_rain['timestamp'])

    # Forecast API
    forecast_url = "https://api-open.data.gov.sg/v2/real-time/api/two-hr-forecast"
    f = requests.get(forecast_url)
    forecast_json = f.json()
    forecast_items = forecast_json['data']['items'][0]['forecasts']

    df_forecast = pd.DataFrame(forecast_items)
    df_forecast.columns = ['location', 'forecast']
    df_forecast['forecast_num'] = df_forecast['forecast'].map(forecast_map).fillna(0)

    # Fuzzy merge forecasts
    df_rain['forecast'] = ''
    df_rain['forecast_num'] = 0
    for _, forecast_row in df_forecast.iterrows():
        area = forecast_row['location'].lower()
        for i in range(len(df_rain)):
            if area in df_rain.at[i, 'location'].lower():
                df_rain.at[i, 'forecast'] = forecast_row['forecast']
                df_rain.at[i, 'forecast_num'] = forecast_row['forecast_num']

    # Time features
    df_rain['hour'] = df_rain['timestamp'].dt.hour
    df_rain['dayofweek'] = df_rain['timestamp'].dt.dayofweek

    return df_rain

# ----------------------------------------
# Predict floods with XGBoost
# ----------------------------------------
def predict_flood(df):
    features = ['rainfall', 'forecast_num', 'latitude', 'longitude', 'hour', 'dayofweek']
    X = df[features]
    df['flood_prediction'] = model.predict(X)
    return df

# ----------------------------------------
# Streamlit UI
# ----------------------------------------
st.set_page_config(page_title="FloodGuard AI", layout="wide")
st.title("🌧️ FloodGuard AI — Live Flood Prediction Dashboard")
st.markdown("Predict floods across Singapore using real-time or simulated rainfall and forecast data.")

simulate = st.checkbox("🌧️ Enable Simulation Mode (Yishun, Pasir Ris, Toa Payoh)")

if st.button("🔄 Refresh Predictions"):
    with st.spinner("Fetching data and running model..."):
        df = get_live_data()

        # Apply simulation if toggled
        if simulate:
            st.info("🚨 Simulation Mode ON — heavy rain at selected locations.")
            df.loc[df['location'].str.contains("Yishun", case=False), 'rainfall'] = 42.0
            df.loc[df['location'].str.contains("Pasir Ris", case=False), 'rainfall'] = 38.0
            df.loc[df['location'].str.contains("Toa Payoh", case=False), 'rainfall'] = 36.0

        df = predict_flood(df)

        flood_areas = df[df['flood_prediction'] == 1]

        if flood_areas.empty:
            st.success("✅ No floods predicted at this time.")
        else:
            st.error(f"🚨 Flood risk predicted at {len(flood_areas)} location(s)!")
            st.dataframe(flood_areas[['location', 'rainfall', 'forecast', 'latitude', 'longitude']])
            st.map(flood_areas[['latitude', 'longitude']])

        st.subheader("📋 All Station Data")
        st.dataframe(df[['location', 'rainfall', 'forecast', 'flood_prediction']])
