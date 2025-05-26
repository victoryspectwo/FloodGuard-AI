# FloodGuard-AI

FloodGuard-AI is a real-time dashboard that predicts flood-prone areas in Singapore and alerts transport managers when nearby bus stops may be affected. It integrates weather data, machine learning, and geospatial analysis to provide actionable insights for emergency and transport operations.

This repository contains the work of our NAISC project, a flood data scraper and prediction model that tells emergency response organisations where their assistance is needed the most.

How can we detect flood-prone areas and proactively deploy additional, key bus services to reduce commuter congestion and minimize transport disruption before it escalates?

FloodGuard-AI was built for the **NAISC Smart Nation initiative** to support:

- Emergency response teams
- Public transport operators
- Urban planners

We take data from various sources:

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
