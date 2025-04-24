# gauge_app/config.py
import os

class Config:
    """Base configuration class."""
    DEBUG = False
    TESTING = False
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev_key')
    
    # MQTT settings
    MQTT_BROKER = os.environ.get('MQTT_BROKER', 'broker-cn.emqx.io')
    MQTT_PORT = int(os.environ.get('MQTT_PORT', 1883))
    MQTT_TOPICS = [
        'temperaturapeacock', 'presionpeacock', 'luzpeacock',
        'humedadpeacock', 'calidadairepeacock', 'poderpeacock'
    ]
    CONTROLLER_TOPIC = os.environ.get('CONTROLLER_TOPIC', 'carlospeacock')
    
    # Camera settings
    CAMERA_WIDTH = int(os.environ.get('CAMERA_WIDTH', 480))
    CAMERA_HEIGHT = int(os.environ.get('CAMERA_HEIGHT', 480))
    CAMERA_INDEX = int(os.environ.get('CAMERA_INDEX', 0))

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