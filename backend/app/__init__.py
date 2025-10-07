from flask import Flask
from flask_jwt_extended import JWTManager
from flask_cors import CORS
import os
import logging

def create_app(config_name='development'):
    app = Flask(__name__)
    
    # Load configuration
    from config import config
    app.config.from_object(config[config_name])
    
    # Ensure upload directories exist
    upload_dir = app.config['UPLOAD_FOLDER']
    os.makedirs(os.path.join(upload_dir, 'profiles'), exist_ok=True)
    os.makedirs(os.path.join(upload_dir, 'groups'), exist_ok=True)
    
    # Initialize extensions
    jwt = JWTManager(app)
    CORS(app)
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Test MongoDB connection
    try:
        from pymongo import MongoClient
        client = MongoClient(app.config['MONGO_URI'])
        db = client.get_default_database()
        # Test connection
        client.server_info()
        print(f"✅ Connected to MongoDB: {db.name}")
    except Exception as e:
        print(f"❌ MongoDB connection failed: {e}")
        print("⚠️ App will continue but database operations will fail")
    
    # Register blueprints
    from app.routes.auth import auth_bp
    from app.routes.upload import upload_bp
    
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(upload_bp, url_prefix='/api/upload')
    
    return app
