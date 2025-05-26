# 🌧️ FloodGuard-AI

FloodGuard-AI is a real-time dashboard that predicts flood-prone areas in Singapore and alerts transport managers when nearby bus stops may be affected. It integrates weather data, machine learning, and geospatial analysis to provide actionable insights for emergency and transport operations.

## 🧠 Project Objective

This repository contains the work of our NAISC project, a flood data scraper and prediction model that tells emergency response organisations where their assistance is needed the most.

> "How can we detect flood-prone areas and proactively deploy additional, key bus services to reduce commuter congestion and minimize transport disruption before it escalates?"

FloodGuard-AI was built for the **NAISC Smart Nation initiative** to support:

- Emergency response teams
- Public transport operators
- Urban planners

## 🛰️ Features

- 🔮 **Flood Prediction**: ML model predicts flooded areas based on real-time rainfall & forecast data
- 🚌 **Bus Stop Alert System**: Highlights bus stops within 200 meters of predicted floods
- 🗺️ **Interactive Map**: View affected locations and nearby bus routes on a live map
- 🤖 **LLM Summary**: Pulls Telegram and news alerts, summarized by an AI model
- 🧪 **Demo Mode**: Replay historical flood events for testing and simulation

## 🧩 Data Sources

data.gov.sg

- Real time rainfall data API (to determine which areas are flooded)
- 2h, 24h and 4 day weather forecast API (to get our basic prediction)

datamall.lta.gov.sg/

- Bus Routes
- Bus Services
- Bus Stops

Additional sources

- PUB Telegram Channel rainfall reports (Processed with Deepseek LLM through Natural Language Processing)

fetch_api.py - load all APIs into dataframes and are callable as functions

## 🗃️ Project Structure

```bash
FloodGuard-AI/
├── dashboard/
│   ├── flood_dashboard.py              # ✅ Main Streamlit dashboard (entry point)
│   ├── app.py                          # Wrapper to run dashboard via Streamlit
│   ├── BusRerouter.py                  # Logic for detecting bus stops near floods
│   ├── floodguard_dual_route_map.html  # Exported static map visualization
│   └── nea_session.session             # Saved session state for NEA scraping
│
├── data/
│   ├── historical_data.csv             # Demo mode input data
│   ├── predicted_data.csv              # Live mode output predictions
│   ├── bus-stops.json                  # All known SG bus stop locations
│   └── bus-services/                   # Route JSON files per bus service
│
├── models/
│   └── flood_predictor_xgb.pkl         # Trained flood prediction model (XGBoost)
│
├── data_processing/
│   ├── fetch_api.py                    # Fetches rainfall & weather forecast APIs
│   ├── feature_engineering.py          # Adds time/location-based features for ML
│   └── forecast_map.py                 # Map generation utilities (Folium)
│
├── inference/
│   └── flood_inference.py              # Headless script for model-based flood prediction
│
├── llm/
│   ├── webscraper.py                   # Scrapes PUB Telegram & NEA alerts
│   ├── deepseek.txt                    # AI-generated summary of alerts
│   └── nea_session.session             # Session storage for scraping reuse
│
├── testing/
│   ├── test_api.py                     # Tests API data fetching logic
│   └── test_historical_data.py         # Validates historical dataset and labels
│
└── README.md                           # 📄 You're here!

