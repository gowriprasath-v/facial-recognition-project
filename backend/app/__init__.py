from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from app.config import config
import os
import logging
from logging.handlers import RotatingFileHandler

def create_app(config_name=None):
    """Create and configure Flask application"""
    
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'development')
    
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Initialize extensions
    CORS(app, origins=['http://localhost:3000'])
    jwt = JWTManager(app)
    
    # Configure logging
    if not app.debug and not app.testing:
        if not os.path.exists('logs'):
            os.mkdir('logs')
        
        file_handler = RotatingFileHandler(
            'logs/facial_recognition.log', 
            maxBytes=10240000,  # 10MB
            backupCount=10
        )
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('Facial Recognition API startup')
        
        # Also log to console in production
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s'
        ))
        app.logger.addHandler(console_handler)
    
    # Register blueprints
    from app.routes.auth import auth_bp
    from app.routes.upload import upload_bp  
    from app.routes.photos import photos_bp
    
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(upload_bp, url_prefix='/api/upload')
    app.register_blueprint(photos_bp, url_prefix='/api/photos')
    
    # JWT error handlers
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return jsonify({
            'status': 'error',
            'message': 'Token has expired'
        }), 401

    @jwt.invalid_token_loader  
    def invalid_token_callback(error):
        return jsonify({
            'status': 'error',
            'message': 'Invalid token'
        }), 401

    @jwt.unauthorized_loader
    def missing_token_callback(error):
        return jsonify({
            'status': 'error', 
            'message': 'Authorization header is expected'
        }), 401
    
    # Global error handlers
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            'status': 'error', 
            'message': 'Endpoint not found'
        }), 404
    
    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            'status': 'error',
            'message': 'Bad request'
        }), 400
    
    @app.errorhandler(403)
    def forbidden(error):
        return jsonify({
            'status': 'error',
            'message': 'Access forbidden'
        }), 403
    
    @app.errorhandler(413)
    def payload_too_large(error):
        return jsonify({
            'status': 'error',
            'message': 'File too large. Maximum size is 5MB'
        }), 413
    
    @app.errorhandler(500)
    def internal_error(error):
        app.logger.error(f"Internal server error: {error}")
        return jsonify({
            'status': 'error',
            'message': 'Internal server error'
        }), 500
    
    # Health check endpoint
    @app.route('/api/health')
    def health_check():
        try:
            # Check database connection
            from app.database import db_manager
            db_healthy = db_manager.health_check()
            
            # Check ML processor
            from app.utils.ml_processor import health_check as ml_health
            ml_status = ml_health()
            
            return jsonify({
                'status': 'healthy',
                'message': 'Facial Recognition API is running',
                'version': '1.0.0',
                'database': 'connected' if db_healthy else 'disconnected',
                'ml_processor': ml_status['status'],
                'environment': config_name
            }), 200 if db_healthy else 503
            
        except Exception as e:
            app.logger.error(f"Health check failed: {e}")
            return jsonify({
                'status': 'unhealthy',
                'message': 'Health check failed',
                'error': str(e)
            }), 503
    
    # ML status endpoint
    @app.route('/api/ml/status')
    def ml_status():
        try:
            from app.utils.ml_processor import get_ml_stats
            stats = get_ml_stats()
            return jsonify({
                'status': 'success',
                'data': stats
            }), 200
        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': f'ML status check failed: {str(e)}'
            }), 500
    
    return app
