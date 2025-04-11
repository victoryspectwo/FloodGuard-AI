import requests
import pandas as pd
import joblib
from datetime import datetime

# Load trained model
model = joblib.load("flood_predictor_xgb.pkl")

# Forecast label mapping (same as training)
forecast_map = {
    "Thundery Showers": 2,
    "Showers": 1,
    "Cloudy": 0,
    "Partly Cloudy (Day)": 0,
    "Partly Cloudy (Night)": 0,
    "Fair (Day)": 0,
    "Fair (Night)": 0
}

# -------------------------------
# Pull live rainfall and forecast data
# -------------------------------
def get_live_data():
    # Get rainfall
    rain_url = "https://api-open.data.gov.sg/v2/real-time/api/rainfall"
    r = requests.get(rain_url)
    rain_json = r.json()

    # Get stations
    stations = {s['id']: {
        'name': s['name'],
        'latitude': s['location']['latitude'],
        'longitude': s['location']['longitude']
    } for s in rain_json['data']['stations']}

    # Get readings
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

    # Get forecast
    forecast_url = "https://api-open.data.gov.sg/v2/real-time/api/two-hr-forecast"
    f = requests.get(forecast_url)
    forecast_json = f.json()
    forecast_items = forecast_json['data']['items'][0]['forecasts']
    df_forecast = pd.DataFrame(forecast_items)
    df_forecast.columns = ['location', 'forecast']
    df_forecast['forecast_num'] = df_forecast['forecast'].map(forecast_map).fillna(0)

    # Merge
    df = pd.merge(df_rain, df_forecast, on="location", how="left")
    df['hour'] = df['timestamp'].dt.hour
    df['dayofweek'] = df['timestamp'].dt.dayofweek

    return df

# -------------------------------
# Predict flood risk per location
# -------------------------------
def run_inference():
    df = get_live_data()

    features = ['rainfall', 'forecast_num', 'latitude', 'longitude', 'hour', 'dayofweek']
    X = df[features]
    preds = model.predict(X)

    df['flood_prediction'] = preds
    flood_areas = df[df['flood_prediction'] == 1]

    print("🚨 Flood Warning Predictions:")
    if flood_areas.empty:
        print("✅ No floods predicted at this time.")
    else:
        for _, row in flood_areas.iterrows():
            print(f"- {row['location']} (Rainfall: {row['rainfall']} mm, Forecast: {row['forecast']})")

# -------------------------------
# Main
# -------------------------------
if __name__ == "__main__":
    print("📡 Running real-time flood prediction...")
    run_inference()
