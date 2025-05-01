#!/usr/bin/env python3
import time
import random
import json
import threading
import requests
import datetime
import paho.mqtt.client as mqtt

BROKER = 'broker-cn.emqx.io'
PORT   = 1883

THRESHOLDS = {
    'temperaturapeacock':  {'low': 20.0,  'high': 30.0},
    'humedadpeacock':     {'low': 30.0,  'high': 60.0},
    'luzpeacock':         {'low': 300.0, 'high':1000.0},
    'presionpeacock':     {'low': 850.0, 'high':1100.0},
    'calidadairepeacock': {'low':   0.0, 'high': 100.0},
    'poderpeacock':       {'low':  20.0, 'high': 100.0},
}

# Only non-temp/humidity channels exceed thresholds occasionally
P_EXCEED = 0.05

def simulate_value(low, high):
    """Mostly in-range, but 5% of the time outside [low, high]."""
    if random.random() < P_EXCEED:
        span = high - low
        if random.random() < 0.5:
            return round(random.uniform(low - 0.2*span, low - 0.1), 2)
        else:
            return round(random.uniform(high + 0.1, high + 0.2*span), 2)
    return round(random.uniform(low, high), 2)

def publisher_loop(client, topic, low, high, interval, actual=None):
    """Publish `actual` if given, else a simulated value, every `interval` seconds."""
    while True:
        value = actual if actual is not None else simulate_value(low, high)
        payload = json.dumps(value)
        client.publish(topic, payload)
        print(f"Published to {topic}: {value}")
        time.sleep(interval)


import requests
import datetime

def get_osaka_weather():
    """
    Fetches Osaka's current temperature and humidity (as of now) in Asia/Tokyo time.
    Returns (temperature_C, humidity_percent).
    """
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": 34.6937,
        "longitude": 135.5023,
        "current_weather": "true",
        "hourly": "relativehumidity_2m",
        "timezone": "Asia/Tokyo"      # ensure all times are local Osaka time :contentReference[oaicite:2]{index=2}
    }
    resp = requests.get(url, params=params)
    data = resp.json()

    temp = data["current_weather"]["temperature"]
    cw_time = data["current_weather"]["time"]  # e.g. "2025-05-01T10:00"

    times = data["hourly"]["time"]
    humidities = data["hourly"]["relativehumidity_2m"]

    try:
        idx = times.index(cw_time)
    except ValueError:
        # 1) Floor to the top of the hour
        dt = datetime.datetime.fromisoformat(cw_time)
        dt_floor = dt.replace(minute=0, second=0, microsecond=0)
        time_str = dt_floor.isoformat()
        try:
            idx = times.index(time_str)
        except ValueError:
            # 2) Find the nearest hour by minimal timedelta
            datetimes = [datetime.datetime.fromisoformat(t) for t in times]
            idx = min(range(len(datetimes)), key=lambda i: abs(datetimes[i] - dt))
    humidity = humidities[idx]
    return round(temp, 2), round(humidity, 2)


def main():
    # 1) Fetch real Osaka weather (temp & humidity)
    temp, hum = get_osaka_weather()

    client = mqtt.Client()
    client.connect(BROKER, PORT, keepalive=60)
    client.loop_start()

    base_interval = 5  # seconds between each sensor reading
    for i, (topic, bounds) in enumerate(THRESHOLDS.items()):
        low, high = bounds['low'], bounds['high']
        # Override temp/humidity with real values; others simulate
        actual = None
        if topic == 'temperaturapeacock':
            actual = temp
        elif topic == 'humedadpeacock':
            actual = hum

        t = threading.Thread(
            target=publisher_loop,
            args=(client, topic, low, high, base_interval, actual),
            daemon=True
        )
        t.start()
        time.sleep(1)  # stagger threads

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopping...")
    finally:
        client.loop_stop()
        client.disconnect()

if __name__ == "__main__":
    main()
