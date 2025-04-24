# gauge_app/services/mqtt_service.py
import paho.mqtt.client as mqtt
import json

# MQTT Configuration
MQTT_BROKER = 'broker-cn.emqx.io'
MQTT_PORT = 1883
MQTT_TOPICS = [
    'temperaturapeacock', 'presionpeacock', 'luzpeacock',
    'humedadpeacock', 'calidadairepeacock', 'poderpeacock'
]
CONTROLLER_TOPIC = 'carlospeacock'

mqtt_client = None
socketio_instance = None

def init_app(app, socketio):
    global mqtt_client, socketio_instance
    socketio_instance = socketio
    
    # Setup MQTT client
    mqtt_client = mqtt.Client()
    mqtt_client.on_connect = on_mqtt_connect
    mqtt_client.on_message = on_mqtt_message
    mqtt_client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
    mqtt_client.loop_start()
    
    # Register Socket.IO event handlers
    register_socketio_handlers(socketio)

def on_mqtt_connect(client, userdata, flags, rc):
    print("✓ Connected to MQTT broker (rc=%s)" % rc)
    for t in MQTT_TOPICS:
        client.subscribe(t)
        print("  • Subscribed to", t)

def on_mqtt_message(client, userdata, msg):
    data = msg.payload.decode()
    socketio_instance.emit('sensorData', {'topic': msg.topic, 'data': data})

def register_socketio_handlers(socketio):
    @socketio.on('connect')
    def handle_connect():
        print("→ Client connected")

    @socketio.on('controllerData')
    def handle_controller(data):
        mqtt_client.publish(CONTROLLER_TOPIC, json.dumps(data))

    @socketio.on('disconnect')
    def handle_disconnect():
        print("← Client disconnected")