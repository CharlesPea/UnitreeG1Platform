from flask import Flask
from flask_socketio import SocketIO
import os

# Main application setup
def create_app():
    # Use absolute path for public directory
    public_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'public')
    app = Flask(__name__, 
                static_folder=public_path,
                template_folder=public_path)
    app.latest_gauge_value = None  # shared state for gauge values
    return app

# app.py
from gauge_app.config import get_config

app = create_app()
app.config.from_object(get_config())
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

# Import routes after app creation to avoid circular imports
from gauge_app.routes import web_routes, video_routes
from gauge_app.services import mqtt_service

# Register blueprints
app.register_blueprint(web_routes.bp)
app.register_blueprint(video_routes.bp)

# Initialize MQTT service
mqtt_service.init_app(app, socketio)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 3000))
    socketio.run(app, host='0.0.0.0', port=port)