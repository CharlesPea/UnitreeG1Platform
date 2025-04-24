# gauge_app/services/mqtt_service.py
import paho.mqtt.client as mqtt
import json

# Global references for MQTT client and Socket.IO instance
mqtt_client = None
socketio_instance = None


def init_app(app, socketio):
    """
    Initialize the MQTT client using Flask app config and integrate it with Socket.IO.
    """
    global mqtt_client, socketio_instance
    socketio_instance = socketio

    # Load MQTT settings from Flask config
    broker        = app.config['MQTT_BROKER']
    port          = app.config['MQTT_PORT']
    topics        = app.config['MQTT_TOPICS']
    controller_to = app.config['CONTROLLER_TOPIC']

    # Create and configure MQTT client
    mqtt_client = mqtt.Client()
    mqtt_client.on_connect = lambda client, userdata, flags, rc: \
        on_mqtt_connect(client, userdata, flags, rc, topics)
    mqtt_client.on_message = on_mqtt_message

    # Connect and run the network loop in an eventlet greenlet
    mqtt_client.connect(broker, port, keepalive=60)
    socketio.start_background_task(mqtt_client.loop_forever)

    # Register Socket.IO handlers, passing the controller topic
    register_socketio_handlers(socketio, controller_to)

def on_mqtt_connect(client, userdata, flags, rc, topics):
    """
    Subscribe to all configured topics upon successful connection.
    """
    if rc == 0:
        print(f"✓ Connected to MQTT broker")
        for t in topics:
            client.subscribe(t)
            print(f"  • Subscribed to {t}")
    else:
        print(f"✗ MQTT connect failed (rc={rc})")


def on_mqtt_message(client, userdata, msg):
    """
    Emit incoming sensor data over Socket.IO.
    """
    try:
        payload = msg.payload.decode()
    except Exception:
        payload = None
    socketio_instance.emit('sensorData', {'topic': msg.topic, 'data': payload})


def register_socketio_handlers(socketio, controller_to):
    """
    Handle Socket.IO events: client connect/disconnect and controller input.
    """
    @socketio.on('connect')
    def handle_connect():
        print("→ Client connected")

    @socketio.on('controllerData')
    def handle_controller(data):
        # Publish controller updates back to the robot
        mqtt_client.publish(controller_to, json.dumps(data))

    @socketio.on('disconnect')
    def handle_disconnect():
        print("← Client disconnected")
