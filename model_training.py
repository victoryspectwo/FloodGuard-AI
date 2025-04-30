import pandas as pd
import joblib
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
from xgboost import XGBClassifier

import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from data_processing.fetch_api import fetch_rainfall_df, fetch_forecast_df
#fetch the real time APIs in dataframe format

from data_processing.feature_engineering import fuzzy_merge_forecast, apply_time_features
#fuzzy merge forecast data with rain

from data_processing.forecast_map import forecast_map

# -------------------------------
# Step 1: Prepare Training Data
# -------------------------------
"""
def prepare_training_data_realtime():

    rain_df = fetch_rainfall_df()
    forecast_df = fetch_forecast_df()

    rain_df = fuzzy_merge_forecast(rain_df, forecast_df)
    rain_df = apply_time_features(rain_df)

    # Label: flood if rainfall > 10mm
    rain_df['flood_label'] = (rain_df['rainfall'] > 10).astype(int)

    # Add simulated floods
    simulated = rain_df.sample(10).copy()
    simulated['rainfall'] = [35 + i for i in range(10)]
    simulated['forecast_num'] = 2
    simulated['flood_label'] = 1

    return pd.concat([rain_df, simulated], ignore_index=True)"""

def prepare_training_data():
    print("📄 Loading historical_data.csv...")
    df = pd.read_csv("historical_data.csv")

    # Ensure flood_label is present or recompute it if needed
    if 'flood_label' not in df.columns:
        df['flood_label'] = (df['rainfall'] > 5).astype(int)

    print(df['flood_label'].value_counts())

    return df

# -------------------------------
# Step 2: Train Model
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

    joblib.dump(model, "models/flood_predictor_xgb.pkl")
    print("✅ Model saved to models/flood_predictor_xgb.pkl")

# -------------------------------
# Main
# -------------------------------
if __name__ == "__main__":
    print("📡 Loading training data...")
    df = prepare_training_data()

    print("🧠 Training flood prediction model...")
    train_model(df)

    print("✅ Done.")
