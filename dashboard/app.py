import os
import json
import pandas as pd
import folium
import requests
from streamlit_folium import st_folium
from folium.plugins import Fullscreen
import streamlit as st
from geopy.distance import geodesic

@st.cache_data
def load_data():
    base_path = r"C:\Users\aqwro\Downloads\FloodGuard-AI-main\FloodGuard-AI-main\data"
    flood_csv_path = os.path.join(base_path, "2025-05-25T10-10_export.csv")
    bus_stops_file = os.path.join(base_path, "bus-stops.json")
    bus_services_dir = os.path.join(base_path, "bus-services")

    flood_df = pd.read_csv(flood_csv_path)
    flood_df = flood_df[flood_df['flood_prediction'] == 1]

    # Fetch station coordinates from API
    api_url = "https://api.data.gov.sg/v1/environment/rainfall"
    try:
        response = requests.get(api_url)
        stations_data = response.json().get("metadata", {}).get("stations", [])
        station_coords = {station["name"]: (station["location"]["latitude"], station["location"]["longitude"]) for station in stations_data}
    except Exception as e:
        station_coords = {}

    flood_locations = []
    for road in flood_df['location'].unique():
        if road in station_coords:
            lat, lon = station_coords[road]
            flood_locations.append((road, lat, lon))

    with open(bus_stops_file, "r") as f:
        bus_stops = json.load(f)

    bus_stops_dict = {
        sid: {
            "stop_id": sid,
            "name": data["name"],
            "lat": float(data["coords"].split(",")[1]),
            "lon": float(data["coords"].split(",")[0])
        }
        for sid, data in bus_stops.items()
    }

    flooded_stops = []
    for stop in bus_stops_dict.values():
        for _, lat, lon in flood_locations:
            if geodesic((stop["lat"], stop["lon"]), (lat, lon)).meters < 200:
                flooded_stops.append(stop)
                break
    flooded_ids = {s["stop_id"] for s in flooded_stops}

    affected_bus_data = {}

    for fname in os.listdir(bus_services_dir):
        if not fname.endswith(".json"):
            continue

        bus_number = fname.replace(".json", "")
        with open(os.path.join(bus_services_dir, fname), "r") as f:
            data = json.load(f)

        route_data = data.get("1", {})
        route_coords = route_data.get("route", [])
        stop_ids = route_data.get("stops", [])

        if not route_coords or not stop_ids:
            continue

        if not any(stop_id in flooded_ids for stop_id in stop_ids):
            continue

        affected_bus_data[bus_number] = {
            "coords": route_coords,
            "stops": stop_ids
        }

    return flood_locations, bus_stops_dict, flooded_ids, affected_bus_data

# === Streamlit UI ===
st.set_page_config(layout="wide")
st.title("Singapore Bus Rerouting System")
st.markdown("This map shows bus routes affected by flood-prone areas in Singapore.")

flood_locations, bus_stops_dict, flooded_ids, affected_bus_data = load_data()

affected_bus_numbers = sorted(affected_bus_data.keys())
bus_selection = st.sidebar.multiselect("Select Affected Bus Numbers:", options=["Select All"] + affected_bus_numbers, default=["Select All"])

if "Select All" in bus_selection:
    selected_buses = affected_bus_numbers
else:
    selected_buses = [b for b in bus_selection if b in affected_bus_numbers]

m = folium.Map(location=[1.3521, 103.8198], zoom_start=12)
folium.TileLayer("cartodbpositron").add_to(m)
Fullscreen(position='topright').add_to(m)

for road, lat, lon in flood_locations:
    folium.Marker(
        location=[lat, lon],
        popup=f"Flood at {road}",
        icon=folium.Icon(color='orange', icon='tint', prefix='fa')
    ).add_to(m)

for bus_number in selected_buses:
    data = affected_bus_data[bus_number]
    route_coords = data["coords"]
    stop_ids = data["stops"]

    fg = folium.FeatureGroup(name=f"Bus {bus_number}")
    latlons = [(float(latlng.split(",")[1]), float(latlng.split(",")[0])) for latlng in route_coords]
    folium.PolyLine(latlons, color='blue', weight=4, tooltip=f"Bus {bus_number} Route").add_to(fg)

    for sid in stop_ids:
        if sid not in bus_stops_dict:
            continue
        stop = bus_stops_dict[sid]
        is_flooded = sid in flooded_ids
        marker_text = f"Flooded: {stop['name']}" if is_flooded else stop['name']
        folium.Marker(
            location=[stop["lat"], stop["lon"]],
            popup=marker_text,
            icon=folium.Icon(color='red' if is_flooded else 'green', icon='bus', prefix='fa')
        ).add_to(fg)

    fg.add_to(m)

folium.LayerControl(collapsed=False).add_to(m)
st_data = st_folium(m, width=1200, height=700, returned_objects=[])
