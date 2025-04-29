#!/usr/bin/env python3
import time
import random
import json
import threading

import paho.mqtt.client as mqtt

BROKER = 'broker-cn.emqx.io'
PORT = 1883

THRESHOLDS = {
    'temperaturapeacock':    {'low': 20.0,  'high': 30.0},   # °C (68–86°F)
    'humedadpeacock':       {'low': 30.0,  'high': 60.0},   # % RH (30–60%)
    'luzpeacock':           {'low': 300.0, 'high': 1000.0}, # lux (office:300–500; <1000)
    'presionpeacock':       {'low': 850.0, 'high': 1100.0}, # hPa (altitude sickness below ~840 hPa)
    'calidadairepeacock':   {'low': 0.0,   'high': 100.0},  # AQI >100 “Unhealthy”
    'poderpeacock':         {'low': 20.0,  'high': 100.0},  # % battery (<20% low)
}

# Probability to exceed thresholds
P_EXCEED = 0.05

def simulate_value(low, high):
    """Generate a value mostly within [low, high], occasionally outside."""
    if random.random() < P_EXCEED:
        # go out of range
        span = high - low
        if random.random() < 0.5:
            # below low
            return round(random.uniform(low - 0.2*span, low - 0.1), 2)
        else:
            # above high
            return round(random.uniform(high + 0.1, high + 0.2*span), 2)
    else:
        # within range
        return round(random.uniform(low, high), 2)

def publisher_loop(client, topic, low, high, interval):
    """Publish a new reading on `topic` every `interval` seconds."""
    while True:
        value = simulate_value(low, high)
        payload = json.dumps({'value': value})
        client.publish(topic, payload)
        print(f"Published to {topic}: {payload}")
        time.sleep(interval)

def main():
    client = mqtt.Client()
    client.connect(BROKER, PORT, keepalive=60)
    client.loop_start()

    # Stagger intervals so reads aren’t all simultaneous
    base_interval = 5  # seconds between readings per channel
    for i, (topic, bounds) in enumerate(THRESHOLDS.items()):
        low, high = bounds['low'], bounds['high']
        # e.g. first topic every 5s, next every 5s but start 1s later, etc.
        t = threading.Thread(
            target=publisher_loop,
            args=(client, topic, low, high, base_interval),
            daemon=True
        )
        t.start()
        time.sleep(1)

    # keep the main thread alive
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
