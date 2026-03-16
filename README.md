# Sleep Environment Monitor

Investigating the relationship between bedroom environmental conditions and sleep quality over a 2-week study period (9-22 February 2026).

**Student:** Yasmin Akhmedova
**Programme:** MSc AI Applications and Innovation
**Module:** Internet of Things and Applications

## Overview

This project combines three data sources to examine how sleeping environment conditions affect sleep quality metrics (total sleep, awake time, deep sleep, REM sleep, and light sleep):

| # | Data Source | Method | Frequency | Parameters |
|---|---|---|---|---|
| 1 | Bedroom environment sensors | Heltec WiFi LoRa 32 V3 with DHT11, photoresistor, microphone; logged via USB serial | Every minute | Temperature, humidity, light, sound avg, sound peak |
| 2 | External air quality | Breathe London API (Horseferry Road, BL0046) | Hourly | NO2, PM2.5 |
| 3 | Personal sleep metrics | Ultrahuman Ring wearable, manually exported | Daily | Total sleep, awake time, deep sleep, REM sleep, light sleep |

All data was collected or filtered to the sleep window of 11pm-9am.

## Project Structure

```
sleep-monitor/
├── arduino/
│   └── sleep_monitor/sensors_program/sensors_program.ino   # Arduino sketch for Heltec board
├── data/
│   ├── 2026-02-09_sleep_data.csv ... 2026-02-22_sleep_data.csv  # Raw nightly sensor logs (14 files)
│   ├── bedroom_sensors.csv                                  # Combined sensor data (all 14 nights)
│   ├── breathe_london_air_quality.csv                       # Air quality from API
│   └── ultrahuman_sleep_data.csv                            # Sleep metrics from ring
├── notebooks/
│   └── data_collection.ipynb                                # Data collection and methodology
├── streamlit/
│   └── config.toml                                          # Streamlit theme config
├── app.py                                                   # Streamlit dashboard application
├── requirements.txt                                         # Python dependencies
└── README.md
```

## Setup

### Hardware

- Heltec WiFi LoRa 32 V3 development board (ESP32-S3)
- KY-015 / DHT11 temperature and humidity sensor (GPIO 7)
- ELB0604 photoresistor light sensor (GPIO 1)
- KY-038 microphone sound sensor (GPIO 2)

All sensors powered at 3.3V. The Arduino sketch (`arduino/sleep_monitor/sensors_program/sensors_program.ino`) should be flashed to the board using the Arduino IDE.

### Software

Requires Python 3.10+.

```bash
pip install -r requirements.txt
```

### Running the Dashboard

The dashboard is deployed and accessible online at:
**https://sleep-monitor.streamlit.app**

Alternatively, to run locally:

```bash
streamlit run app.py
```

## Data Collection

The data collection process is documented in `notebooks/data_collection.ipynb`. The notebook covers:

1. **Bedroom environment sensors** - serial logging from the Heltec board, one reading per minute. Each night produces a separate CSV file (14 in total), which are then combined into a single `bedroom_sensors.csv` for analysis
2. **External air quality** - bulk retrieval from the Breathe London API after the collection period
3. **Personal sleep metrics** - manual export from the Ultrahuman app
