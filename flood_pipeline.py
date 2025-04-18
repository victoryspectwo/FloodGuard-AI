import requests
import pandas as pd
import joblib
from datetime import datetime
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
from xgboost import XGBClassifier

# -------------------------------
# Step 1: Get Rainfall Data
# -------------------------------
def get_rainfall_data():
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
            'rainfall': r['value'],
            'latitude': stations[sid]['latitude'],
            'longitude': stations[sid]['longitude'],
            'location': stations[sid]['name']
        })
    df = pd.DataFrame(rows)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    return df

# -------------------------------
# Step 2: Get Forecast Data
# -------------------------------
def get_forecast_data():
    url = "https://api-open.data.gov.sg/v2/real-time/api/two-hr-forecast"
    response = requests.get(url)
    data = response.json()
    print(data)
    forecast_map = {
        "Thundery Showers": 2,
        "Showers": 1,
        "Cloudy": 0,
        "Partly Cloudy (Day)": 0,
        "Partly Cloudy (Night)": 0,
        "Fair (Day)": 0,
        "Fair (Night)": 0
    }
    items = data['data']['items'][0]['forecasts']
    df_forecast = pd.DataFrame(items)
    df_forecast.columns = ['location', 'forecast']
    df_forecast['forecast_num'] = df_forecast['forecast'].map(forecast_map).fillna(0)
    return df_forecast

# -------------------------------
# Step 3: Merge + Simulate Floods
# -------------------------------
def prepare_training_data(rain, forecast):
    # Fuzzy match forecast to rainfall location
    rain['forecast'] = ''
    rain['forecast_num'] = 0
    for _, f in forecast.iterrows():
        area = f['location'].lower()
        for i in range(len(rain)):
            if area in rain.at[i, 'location'].lower():
                rain.at[i, 'forecast'] = f['forecast']
                rain.at[i, 'forecast_num'] = f['forecast_num']

    # Time features
    rain['hour'] = rain['timestamp'].dt.hour
    rain['dayofweek'] = rain['timestamp'].dt.dayofweek

    # Label: flood if rainfall > 5mm (sensitive)
    rain['flood_label'] = (rain['rainfall'] > 5).astype(int)

    # Add simulated flood cases
    simulated = rain.sample(10).copy()
    simulated['rainfall'] = [35 + i for i in range(10)]
    simulated['forecast_num'] = 2
    simulated['flood_label'] = 1

    return pd.concat([rain, simulated], ignore_index=True)

# -------------------------------
# Step 4: Train Model
# -------------------------------
def train_model(df):
    features = ['rainfall', 'forecast_num', 'latitude', 'longitude', 'hour', 'dayofweek']
    X = df[features]
    y = df['flood_label']
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    model = XGBClassifier(use_label_encoder=False, eval_metric='logloss')
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    print("🧾 Classification Report:")
    print(classification_report(y_test, y_pred))
    joblib.dump(model, 'flood_predictor_xgb.pkl')
    print("✅ Model saved to flood_predictor_xgb.pkl")

# -------------------------------
# Main Pipeline
# -------------------------------
if __name__ == "__main__":
    print("📥 Fetching rainfall data...")
    rain_df = get_rainfall_data()
    print("☁️ Fetching forecast data...")
    forecast_df = get_forecast_data()
    print("🧹 Preparing data with simulated floods...")
    train_df = prepare_training_data(rain_df, forecast_df)
    print("🧠 Training model...")
    train_model(train_df)
    print("✅ Done.")
