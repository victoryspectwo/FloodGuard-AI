from data_processing.fetch_api import fetch_rainfall_df, fetch_forecast_df
#from data.data_pipeline import get_water_level_sensor_locations

from model_training import prepare_training_data

rain_df = fetch_rainfall_df()
forecast_df = fetch_forecast_df()

rain_df_processed = prepare_training_data()
#sensor_locations = get_water_level_sensor_locations()

print("🌧️ Rainfall Data Sample:")
print(rain_df)

print("\n📡 Forecast Data Sample:")
print(forecast_df)

#print("\n🌧️ Processed Rainfall Data Sample:")
#print(rain_df_processed)

#print("\n📡 Water Level Sensor Location Sample:")
#print(sensor_locations.head())
