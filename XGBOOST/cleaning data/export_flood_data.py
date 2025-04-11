import requests
import pandas as pd
from datetime import datetime

# Forecast map
forecast_map = {
    "Thundery Showers": 2,
    "Showers": 1,
    "Cloudy": 0,
    "Partly Cloudy (Day)": 0,
    "Partly Cloudy (Night)": 0,
    "Fair (Day)": 0,
    "Fair (Night)": 0
}

def get_rain_and_forecast():
    # Rainfall API
    rain_url = "https://api-open.data.gov.sg/v2/real-time/api/rainfall"
    rain_data = requests.get(rain_url).json()

    stations = {s['id']: {
        'name': s['name'],
        'latitude': s['location']['latitude'],
        'longitude': s['location']['longitude']
    } for s in rain_data['data']['stations']}

    readings = rain_data['data']['readings'][0]
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
    forecast_data = requests.get(forecast_url).json()
    forecasts = forecast_data['data']['items'][0]['forecasts']

    df_forecast = pd.DataFrame(forecasts)
    df_forecast.columns = ['forecast_area', 'forecast']
    df_forecast['forecast_num'] = df_forecast['forecast'].map(forecast_map).fillna(0)

    # Fuzzy merge forecasts
    df_rain['forecast'] = ''
    df_rain['forecast_num'] = 0
    for _, row in df_forecast.iterrows():
        area = row['forecast_area'].lower()
        for i in range(len(df_rain)):
            if area in df_rain.at[i, 'location'].lower():
                df_rain.at[i, 'forecast'] = row['forecast']
                df_rain.at[i, 'forecast_num'] = row['forecast_num']

    df_rain['hour'] = df_rain['timestamp'].dt.hour
    df_rain['dayofweek'] = df_rain['timestamp'].dt.dayofweek

    return df_rain

# Run and save
df = get_rain_and_forecast()
df.to_csv("real_time_flood_data.csv", index=False)
print("✅ Data saved to real_time_flood_data.csv")
