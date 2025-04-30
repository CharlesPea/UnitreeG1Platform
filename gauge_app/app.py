import os
from dotenv import load_dotenv
from flask import Flask
from flask_socketio import SocketIO

# 1. Load .env early
load_dotenv()

from gauge_app.config import get_config

def create_app():
    # 2. Instantiate Flask
    public_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), '..', 'public')
    )
    app = Flask(__name__, static_folder=public_path, template_folder=public_path)
    app.latest_gauge_value = None

    # 3. Load your Config class
    app.config.from_object(get_config())

    # 4. Set defaults for MQTT, controller topic, etc.
    app.config.setdefault('MQTT_BROKER',      'broker-cn.emqx.io')
    app.config.setdefault('MQTT_PORT',        1883)
    app.config.setdefault('MQTT_TOPICS',      [
        'temperaturapeacock','presionpeacock','luzpeacock',
        'humedadpeacock','calidadairepeacock','poderpeacock'
    ])
    app.config.setdefault('CONTROLLER_TOPIC', 'carlospeacock')
    # (No need to set default for OPENAI_API_KEY if you pull it in your Config)

    # 5. Register API & stream blueprints first
    from gauge_app.routes.anomalies    import bp as anomalies_bp
    from gauge_app.routes.video_routes import bp as video_bp
    from gauge_app.routes.screenshot   import bp as screenshot_bp

    app.register_blueprint(anomalies_bp)
    app.register_blueprint(video_bp)
    app.register_blueprint(screenshot_bp)

    # 6. Finally, catch-all for your SPA
    from gauge_app.routes.web_routes import bp as web_bp
    app.register_blueprint(web_bp)

    return app

# 7. Create app & SocketIO
app = create_app()
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# 8. Initialize camera & MQTT
from gauge_app.services.camera_service import init_app as init_camera
from gauge_app.services import mqtt_service

mqtt_service.init_app(app, socketio)
init_camera(app)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 3000))
    socketio.run(app, host='0.0.0.0', port=port)
