# FloodGuard-AI

This repository contains the work of our NAISC project, a flood data scraper and prediction model that tells emergency response organisations where their assistance is needed the most.

How can we detect flood-prone areas and proactively deploy additional, key bus services to reduce commuter congestion and minimize transport disruption before it escalates?

We take data from various sources:

data.gov.sg

- Real time rainfall data API (to determine which areas are flooded)
- 2h, 24h and 4 day weather forecast API (to get our basic prediction)

Additional sources

- PUB Telegram Channel rainfall reports (Processed with Deepseek LLM through Natural Language Processing)

fetch_api.py - load all APIs into dataframes and are callable as functions
