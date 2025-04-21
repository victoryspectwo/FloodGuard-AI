import difflib

def fuzzy_merge_forecast(rain_df, forecast_df):
    rain_df = rain_df.copy()
    rain_df['forecast'] = ''
    rain_df['forecast_num'] = 0.0

    forecast_locations = forecast_df['location'].str.lower().tolist()

    for i in range(len(rain_df)):
        station_name = rain_df.iloc[i]['location'].lower()
        best_match = difflib.get_close_matches(station_name, forecast_locations, n=1, cutoff=0.6)

        if best_match:
            match_row = forecast_df[forecast_df['location'].str.lower() == best_match[0]].iloc[0]
            rain_df.iloc[i, rain_df.columns.get_loc('forecast')] = match_row['forecast']
            rain_df.iloc[i, rain_df.columns.get_loc('forecast_num')] = float(match_row['forecast_num'])

    return rain_df

def apply_time_features(df):
    df['hour'] = df['timestamp'].dt.hour
    df['dayofweek'] = df['timestamp'].dt.dayofweek
    return df
