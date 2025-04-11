import requests
import json
import pandas as pd
from datetime import datetime

# --- Rainfall API ---
rainfall_url = "https://api-open.data.gov.sg/v2/real-time/api/rainfall"
r1 = requests.get(rainfall_url)
rain_json = r1.json()

# Flatten stations metadata
stations = {s['id']: {
    'name': s['name'],
    'latitude': s['location']['latitude'],
    'longitude': s['location']['longitude']
} for s in rain_json['data']['stations']}

# Extract rainfall readings
rain_df_rows = []
timestamp = rain_json['data']['readings'][0]['timestamp']
for reading in rain_json['data']['readings'][0]['data']:
    sid = reading['stationId']
    rain_df_rows.append({
        'timestamp': timestamp,
        'station_id': sid,
        'rainfall': reading['value'],
        'lat': stations[sid]['latitude'],
        'lon': stations[sid]['longitude'],
        'location': stations[sid]['name']
    })

rain_df = pd.DataFrame(rain_df_rows)
rain_df['timestamp'] = pd.to_datetime(rain_df['timestamp'])

# --- Weather Forecast API ---
forecast_url = "https://api-open.data.gov.sg/v2/real-time/api/two-hr-forecast"
r2 = requests.get(forecast_url)
forecast_json = r2.json()

# Extract forecasts
forecast_time = forecast_json['data']['items'][0]['timestamp']
forecast_rows = forecast_json['data']['items'][0]['forecasts']
forecast_df = pd.DataFrame(forecast_rows)
forecast_df.columns = ['location', 'forecast']
forecast_df['forecast_time'] = pd.to_datetime(forecast_time)

# Optional: Map forecasts to numerical values for ML use
forecast_map = {
    "Thundery Showers": 2,
    "Showers": 1,
    "Cloudy": 0,
    "Partly Cloudy (Day)": 0,
    "Partly Cloudy (Night)": 0,
    "Fair (Day)": 0,
    "Fair (Night)": 0
}
forecast_df['forecast_num'] = forecast_df['forecast'].map(forecast_map).fillna(0)

# Preview results
print("\nRainfall Data Sample:")
print(rain_df.head())

print("\nWeather Forecast Sample:")
print(forecast_df.head())
