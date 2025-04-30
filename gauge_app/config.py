# gauge_app/config.py
import os

class Config:
    """Base configuration class."""
    DEBUG = False
    TESTING = False
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev_key')
    

    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')


    # MQTT settings
    MQTT_BROKER = os.environ.get('MQTT_BROKER', 'broker-cn.emqx.io')
    MQTT_PORT = int(os.environ.get('MQTT_PORT', 1883))
    MQTT_TOPICS = [
        'temperaturapeacock', 'presionpeacock', 'luzpeacock',
        'humedadpeacock', 'calidadairepeacock', 'poderpeacock'
    ]
    CONTROLLER_TOPIC = os.environ.get('CONTROLLER_TOPIC', 'carlospeacock')
    
    # Camera settings
    CAMERA_WIDTH = int(os.environ.get('CAMERA_WIDTH', 1600))
    CAMERA_HEIGHT = int(os.environ.get('CAMERA_HEIGHT', 900))
    CAMERA_INDEX = int(os.environ.get('CAMERA_INDEX', 0))

    THRESHOLDS = {
        'temperaturapeacock': { 'low': 20.0, 'high': 30.0 },   # °C (68–86°F) :contentReference[oaicite:4]{index=4}
        'humedadpeacock':    { 'low': 30.0, 'high': 60.0 },   # % RH (30–60%) :contentReference[oaicite:5]{index=5}
        'luzpeacock':        { 'low': 300.0, 'high': 1000.0 },# lux (office:300–500; <1000) :contentReference[oaicite:6]{index=6}
        'presionpeacock':    { 'low': 850.0, 'high': 1100.0 },# hPa (altitude sickness below ~840 hPa) :contentReference[oaicite:7]{index=7}
        'calidadairepeacock':{ 'low':   0.0, 'high': 100.0 }, # AQI >100 “Unhealthy” :contentReference[oaicite:8]{index=8}
        'poderpeacock':      { 'low':  20.0, 'high': 100.0 } # % battery (<20% low)
    }
    
class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True

class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    DEBUG = True

class ProductionConfig(Config):
    """Production configuration."""
    pass

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

def get_config():
    """Return the appropriate configuration class based on environment."""
    env = os.environ.get('FLASK_ENV', 'default')
    return config.get(env, config['default'])