import requests
import pandas as pd
from datetime import datetime, timedelta
import time

# Forecast mapping (within shared module)
from data_processing.forecast_map import forecast_map

FLOOD_THRESHOLD = 5.0  # Adjust this as needed
SYNTHETIC_COUNT = 50   # Number of simulated flood entries


def fetch_past_data(timestamp):
    time_str = timestamp.strftime("%Y-%m-%dT%H:%M:%S")

    # --- Rainfall ---
    rain_url = f"https://api-open.data.gov.sg/v2/real-time/api/rainfall?date={time_str}"
    rain_resp = requests.get(rain_url).json()

    if not rain_resp['data']['readings']:
        return None  # No data for this timestamp

    stations = {s['id']: {
        'name': s['name'],
        'latitude': s['location']['latitude'],
        'longitude': s['location']['longitude']
    } for s in rain_resp['data']['stations']}

    readings = rain_resp['data']['readings'][0]
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
    df_rain = df_rain[df_rain['location'].str.contains("Road|Ave|Street|Drive|Expressway", case=False, na=False)]
    df_rain = df_rain.reset_index(drop=True)  # ✅ THIS FIXES THE KeyError


    # --- Forecast ---
    forecast_url = f"https://api-open.data.gov.sg/v2/real-time/api/two-hr-forecast?date={time_str}"
    forecast_resp = requests.get(forecast_url).json()

    if not forecast_resp['data']['items']:
        return None

    forecasts = forecast_resp['data']['items'][0]['forecasts']
    df_forecast = pd.DataFrame(forecasts)
    df_forecast.columns = ['location', 'forecast']
    df_forecast['forecast_num'] = df_forecast['forecast'].map(forecast_map).fillna(0)

    # Merge (fuzzy match)
    df_rain['forecast'] = ''
    df_rain['forecast_num'] = 0.0
    for _, f_row in df_forecast.iterrows():
        area = f_row['location'].lower()
        for i in range(len(df_rain)):
            if area in df_rain.at[i, 'location'].lower():
                df_rain.at[i, 'forecast'] = f_row['forecast']
                df_rain.at[i, 'forecast_num'] = float(f_row['forecast_num'])

    df_rain['hour'] = timestamp.hour
    df_rain['dayofweek'] = timestamp.weekday()
    df_rain['flood_label'] = (df_rain['rainfall'] > FLOOD_THRESHOLD).astype(int)
    df_rain['source_timestamp'] = time_str

    return df_rain


if __name__ == "__main__":
    all_data = []
    print("📦 Exporting historical data...")

    base_time = datetime(2025, 4, 19, 0, 0)
    for i in range(72):  # 1 days hourly
        ts = base_time + timedelta(hours=i)
        print(f"⏳ Fetching {ts}...")
        df = fetch_past_data(ts)
        if df is not None and not df.empty:
            all_data.append(df)
        time.sleep(1)  # Be nice to the API

    if all_data:
        final_df = pd.concat(all_data, ignore_index=True)

        # Add synthetic floods to help train model better
        simulated = final_df.sample(SYNTHETIC_COUNT).copy()
        simulated['rainfall'] = [15 + i % 10 for i in range(SYNTHETIC_COUNT)]
        simulated['forecast_num'] = 2.0
        simulated['flood_label'] = 1

        final_df = pd.concat([final_df, simulated], ignore_index=True)
        final_df.to_csv("historical_data.csv", index=False)

        print("✅ historical_data.csv saved!")
        print(final_df.head())
    else:
        print("❌ No data collected.")
