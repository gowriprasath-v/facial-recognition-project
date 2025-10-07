from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash
from bson import ObjectId
import logging

logger = logging.getLogger(__name__)

auth_bp = Blueprint('auth', __name__)

def get_db():
    """Get database connection"""
    try:
        client = MongoClient(current_app.config['MONGO_URI'])
        return client.get_default_database()
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        return None

@auth_bp.route('/register', methods=['POST'])
def register():
    """Register a new user"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data or not all(k in data for k in ('username', 'email', 'password')):
            return jsonify({
                'status': 'error',
                'message': 'Username, email, and password are required'
            }), 400
        
        username = data['username'].strip()
        email = data['email'].strip().lower()
        password = data['password']
        
        # Basic validation
        if len(username) < 3:
            return jsonify({
                'status': 'error',
                'message': 'Username must be at least 3 characters long'
            }), 400
        
        if len(password) < 6:
            return jsonify({
                'status': 'error',
                'message': 'Password must be at least 6 characters long'
            }), 400
        
        # Get database connection
        db = get_db()
        if db is None:
            return jsonify({
                'status': 'error',
                'message': 'Database connection failed'
            }), 500
        
        # Check if user already exists
        if db.users.find_one({'$or': [{'username': username}, {'email': email}]}):
            return jsonify({
                'status': 'error',
                'message': 'Username or email already exists'
            }), 400
        
        # Create new user
        user_data = {
            'username': username,
            'email': email,
            'password_hash': generate_password_hash(password),
            'profile_photo': None,
            'face_embedding': None,
            'face_confidence': None
        }
        
        result = db.users.insert_one(user_data)
        user_id = str(result.inserted_id)
        
        # Create access token
        access_token = create_access_token(identity=user_id)
        
        return jsonify({
            'status': 'success',
            'message': 'User registered successfully',
            'data': {
                'user_id': user_id,
                'username': username,
                'email': email,
                'access_token': access_token
            }
        }), 201
        
    except Exception as e:
        logger.error(f"Registration error: {e}")
        return jsonify({
            'status': 'error',
            'message': f'Registration failed: {str(e)}'
        }), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    """Login user"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data or not all(k in data for k in ('username', 'password')):
            return jsonify({
                'status': 'error',
                'message': 'Username and password are required'
            }), 400
        
        username = data['username'].strip()
        password = data['password']
        
        # Get database connection
        db = get_db()
        if db is None:
            return jsonify({
                'status': 'error',
                'message': 'Database connection failed'
            }), 500
        
        # Find user
        user = db.users.find_one({'username': username})
        
        if not user or not check_password_hash(user['password_hash'], password):
            return jsonify({
                'status': 'error',
                'message': 'Invalid username or password'
            }), 401
        
        # Create access token
        access_token = create_access_token(identity=str(user['_id']))
        
        return jsonify({
            'status': 'success',
            'message': 'Login successful',
            'data': {
                'user_id': str(user['_id']),
                'username': user['username'],
                'email': user['email'],
                'access_token': access_token,
                'has_profile_photo': user.get('profile_photo') is not None,
                'has_face_embedding': user.get('face_embedding') is not None
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Login error: {e}")
        return jsonify({
            'status': 'error',
            'message': f'Login failed: {str(e)}'
        }), 500

@auth_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    """Get current user profile"""
    try:
        user_id = get_jwt_identity()
        
        # Get database connection
        db = get_db()
        if db is None:
            return jsonify({
                'status': 'error',
                'message': 'Database connection failed'
            }), 500
        
        # Find user
        user = db.users.find_one({'_id': ObjectId(user_id)})
        
        if not user:
            return jsonify({
                'status': 'error',
                'message': 'User not found'
            }), 404
        
        # Return user profile (without sensitive data)
        return jsonify({
            'status': 'success',
            'message': 'Profile retrieved successfully',
            'data': {
                'user_id': str(user['_id']),
                'username': user['username'],
                'email': user['email'],
                'profile_photo': user.get('profile_photo'),
                'has_face_embedding': user.get('face_embedding') is not None,
                'face_confidence': user.get('face_confidence')
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Get profile error: {e}")
        return jsonify({
            'status': 'error',
            'message': f'Failed to retrieve profile: {str(e)}'
        }), 500
