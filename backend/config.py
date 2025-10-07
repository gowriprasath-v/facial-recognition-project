import os
from datetime import timedelta

class Config:
    # MongoDB Configuration
    MONGO_URI = 'mongodb://localhost:27017/facial_recognition'
    
    # JWT Configuration
    JWT_SECRET_KEY = 'your-secret-key-change-in-production'
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)
    
    # Upload Configuration
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    
    # Security
    SECRET_KEY = 'dev-secret-key-change-in-production'
    
    # Flask Configuration
    DEBUG = True
    TESTING = False

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
