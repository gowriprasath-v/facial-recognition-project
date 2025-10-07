from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from app.config import config
import logging
import os

def create_app(config_name=None):
    """Create Flask application"""
    
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'development')
    
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Initialize extensions
    CORS(app, origins=['http://localhost:3000'])
    jwt = JWTManager(app)
    
    # Configure logging
    if not app.debug:
        if not os.path.exists('logs'):
            os.makedirs('logs')
        
        file_handler = logging.FileHandler('logs/app.log')
        file_handler.setLevel(logging.INFO)
        formatter = logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        )
        file_handler.setFormatter(formatter)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
    
    # Register blueprints
    from app.routes.auth import auth_bp
    from app.routes.upload import upload_bp
    from app.routes.photos import photos_bp
    
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(upload_bp, url_prefix='/api/upload')
    app.register_blueprint(photos_bp, url_prefix='/api/photos')
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'status': 'error', 'message': 'Endpoint not found'}), 404
    
    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({'status': 'error', 'message': 'Bad request'}), 400
    
    @app.errorhandler(500)
    def internal_error(error):
        app.logger.error(f"Internal error: {error}")
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500
    
    # Health check
    @app.route('/api/health')
    def health():
        from app.database import db_manager
        db_healthy = db_manager.health_check()
        
        return jsonify({
            'status': 'healthy' if db_healthy else 'unhealthy',
            'message': 'Facial Recognition API',
            'database': 'connected' if db_healthy else 'disconnected'
        }), 200 if db_healthy else 503
    
    return app
