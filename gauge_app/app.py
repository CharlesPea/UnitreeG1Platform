from flask import Flask
from flask_socketio import SocketIO
import os

# Load app configuration
from gauge_app.config import get_config

# Create Flask application factory
def create_app():
    # Use absolute path for public directory
    public_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'public')
    app = Flask(
        __name__,
        static_folder=public_path,
        template_folder=public_path
    )
    # Shared state
    app.latest_gauge_value = None

    # Load configuration
    app.config.from_object(get_config())

    # Register blueprints
    from gauge_app.routes.anomalies import bp as anomalies_bp
    app.register_blueprint(anomalies_bp)

    from gauge_app.routes.web_routes import bp as web_bp
    app.register_blueprint(web_bp)

    from gauge_app.routes.video_routes import bp as video_bp
    app.register_blueprint(video_bp)

    return app

from gauge_app.services.camera_service import init_app as init_camera
# Instantiate app and Socket.IO
app = create_app()
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Initialize services
from gauge_app.services import mqtt_service
mqtt_service.init_app(app, socketio)


from gauge_app.services.camera_service import init_app as init_camera
init_camera(app)
# Run server
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 3000))
    socketio.run(app, host='0.0.0.0', port=port)
