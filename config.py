import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'smart-home-sec-lab-key-928374829104')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    SESSION_COOKIE_SECURE = False  # Set to True in production HTTPS
    PERMANENT_SESSION_LIFETIME = 3600  # 1 hour
    # Device gateway shared token for authenticating simulated devices / gateway
    DEVICE_GATEWAY_TOKEN = os.environ.get('DEVICE_GATEWAY_TOKEN', 'gateway-sim-secret-key-99881122')

class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URI', f"sqlite:///{os.path.join(BASE_DIR, 'smart_home.db')}")

class TestingConfig(Config):
    TESTING = True
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    DEVICE_GATEWAY_TOKEN = 'test-gateway-token-12345'

class ProductionConfig(Config):
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URI', f"sqlite:///{os.path.join(BASE_DIR, 'smart_home.db')}")
    SESSION_COOKIE_SECURE = True

config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
