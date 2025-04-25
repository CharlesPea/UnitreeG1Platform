# gauge_app/services/mqtt_service.py
import paho.mqtt.client as mqtt
import json

from datetime import datetime
from gauge_app.config import Config

# In-memory stores
sensor_history = { t: [] for t in Config.THRESHOLDS }   # list of (timestamp, float_value)
anomaly_log    = []  # list of dicts: {'topic','value','time'}


mqtt_client       = mqtt.Client()
socketio_instance = None

def init_app(app, socketio):
    global socketio_instance
    socketio_instance = socketio

    broker        = app.config['MQTT_BROKER']
    port          = app.config['MQTT_PORT']
    topics        = app.config['MQTT_TOPICS']
    controller_to = app.config['CONTROLLER_TOPIC']

    # register callbacks
    mqtt_client.on_connect = lambda client, u, f, rc: on_mqtt_connect(client, u, f, rc, topics)
    mqtt_client.on_message = on_mqtt_message

    # single connect + start loop in its own thread
    mqtt_client.connect(broker, port, keepalive=60)
    mqtt_client.loop_start()                 # <-- only this, no loop_forever

    register_socketio_handlers(socketio, controller_to)

def on_mqtt_connect(client, userdata, flags, rc, topics):
    if rc == 0:
        print("✓ Connected to MQTT broker")
        for t in topics:
            client.subscribe(t)
            print("  • Subscribed to", t)
    else:
        print(f"✗ MQTT connect failed (rc={rc})")

# gauge_app/routes/anomalies.py
from flask import Blueprint, send_file
import io, statistics
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from gauge_app.services.mqtt_service import sensor_history, anomaly_log

bp = Blueprint('anomalies', __name__)

@bp.route('/anomalies/pdf')
def anomalies_pdf():
    buf = io.BytesIO()
    p   = canvas.Canvas(buf, pagesize=letter)
    width, height = letter

    # Title
    p.setFont("Helvetica-Bold", 16)
    p.drawString(50, height - 50, "Anomaly Log Summary")

    # Summary: for each topic, avg & peak
    y = height - 80
    p.setFont("Helvetica", 12)
    for topic, readings in sensor_history.items():
        if not readings: continue
        values = [v for (_, v) in readings]
        avg    = statistics.mean(values)
        peak   = max(values)
        trough = min(values)
        p.drawString(50, y, f"{topic}: avg={avg:.1f}, peak={peak}, low={trough}")
        y -= 20

    # Detailed anomalies
    y -= 10
    p.setFont("Helvetica-Bold", 14)
    p.drawString(50, y, "Anomalies:")
    y -= 20
    p.setFont("Helvetica", 10)
    for entry in anomaly_log[-50:]:   # last 50
        time_str = entry['time'].strftime("%Y-%m-%d %H:%M:%S")
        p.drawString(60, y,
            f"{time_str} | {entry['topic']} = {entry['value']}"
        )
        y -= 15
        if y < 50:
            p.showPage()
            y = height - 50

    p.save()
    buf.seek(0)
    return send_file(
        buf,
        as_attachment=True,
        download_name="anomaly_log.pdf",
        mimetype="application/pdf"
    )


def register_socketio_handlers(socketio, controller_to):
    @socketio.on('connect')
    def handle_connect():
        print("→ Client connected")

    @socketio.on('controllerData')
    def handle_controller(data):
        mqtt_client.publish(controller_to, json.dumps(data))

    @socketio.on('disconnect')
    def handle_disconnect():
        print("← Client disconnected")
