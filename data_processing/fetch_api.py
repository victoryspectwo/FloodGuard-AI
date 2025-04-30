import requests
import pandas as pd
from data_processing.forecast_map import forecast_map

def fetch_rainfall_df(): #real-time rainfall - dependent variable

    #calling the API in json format
    url = "https://api-open.data.gov.sg/v2/real-time/api/rainfall"
    response = requests.get(url)
    data = response.json()

    stations = {s['id']: {
        'name': s['name'],
        'latitude': s['location']['latitude'],
        'longitude': s['location']['longitude']
    } for s in data['data']['stations']}

    readings = data['data']['readings'][0]
    timestamp = readings['timestamp']

    rows = []
    for r in readings['data']:
        sid = r['stationId']
        rows.append({
            'timestamp': timestamp,
            'station_id': sid,
            'rainfall': r['value'], #recorded in mm of rainfall
            'latitude': stations[sid]['latitude'],
            'longitude': stations[sid]['longitude'],
            'location': stations[sid]['name']
        })

    df = pd.DataFrame(rows)
    df['timestamp'] = pd.to_datetime(df['timestamp'])

    return df


def fetch_forecast_df(): #2 hour forecast - independent variable

    #calling the API in json format
    url = "https://api-open.data.gov.sg/v2/real-time/api/two-hr-forecast"
    response = requests.get(url)
    data = response.json()

    forecasts = data['data']['items'][0]['forecasts']

    df = pd.DataFrame(forecasts)
    df.columns = ['location', 'forecast']

    def map_forecast_to_num(text): #mapping the forecast to a number
        
        text = text.lower()
        if "heavy" in text and "thundery" in text:
            return 3
        elif "thundery" in text:
            return 2
        elif "showers" in text:
            return 1
        elif "cloudy" in text:
            return 0.5
        else:
            return 0

    df['forecast_num'] = df['forecast'].apply(map_forecast_to_num)

    return df
