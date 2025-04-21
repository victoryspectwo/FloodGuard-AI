import pandas as pd
from data_processing.fetch_api import fetch_rainfall_df, fetch_forecast_df
from data_processing.feature_engineering import fuzzy_merge_forecast, apply_time_features

# Step 1: Get current data
rain_df = fetch_rainfall_df()
forecast_df = fetch_forecast_df()
rain_df = fuzzy_merge_forecast(rain_df, forecast_df)
rain_df = apply_time_features(rain_df)

# Step 2: Save snapshot
rain_df.to_csv("now_snapshot.csv", index=False)
print("✅ Saved current data to now_snapshot.csv")
