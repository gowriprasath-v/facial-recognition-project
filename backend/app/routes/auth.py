from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
from app.database import get_db
from app.utils.validators import UserRegistrationSchema, UserLoginSchema, validate_request_data
from bson import ObjectId
import logging

logger = logging.getLogger(__name__)
auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    """Register new user"""
    try:
        data = request.get_json() or {}
        
        # Validate input
        valid, validated_data, error = validate_request_data(UserRegistrationSchema(), data)
        if not valid:
            return jsonify({'status': 'error', 'message': error}), 400
        
        db = get_db()
        
        # Check if user exists
        if db.users.find_one({'username': validated_data['username']}):
            return jsonify({'status': 'error', 'message': 'Username already exists'}), 400
        
        # Create user
        user_data = {
            'username': validated_data['username'],
            'email': validated_data.get('email'),
            'password_hash': generate_password_hash(validated_data['password']),
            'profile_photo': None,
            'face_embedding': None
        }
        
        result = db.users.insert_one(user_data)
        access_token = create_access_token(identity=str(result.inserted_id))
        
        logger.info(f"User registered: {validated_data['username']}")
        
        return jsonify({
            'status': 'success',
            'message': 'User registered successfully',
            'data': {
                'access_token': access_token,
                'user_id': str(result.inserted_id)
            }
        }), 201
        
    except Exception as e:
        logger.error(f"Registration error: {e}")
        return jsonify({'status': 'error', 'message': 'Registration failed'}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    """User login"""
    try:
        data = request.get_json() or {}
        
        # Validate input
        valid, validated_data, error = validate_request_data(UserLoginSchema(), data)
        if not valid:
            return jsonify({'status': 'error', 'message': error}), 400
        
        db = get_db()
        user = db.users.find_one({'username': validated_data['username']})
        
        if not user or not check_password_hash(user['password_hash'], validated_data['password']):
            return jsonify({'status': 'error', 'message': 'Invalid credentials'}), 401
        
        access_token = create_access_token(identity=str(user['_id']))
        
        logger.info(f"User logged in: {validated_data['username']}")
        
        return jsonify({
            'status': 'success',
            'message': 'Login successful',
            'data': {
                'access_token': access_token,
                'user_id': str(user['_id']),
                'username': user['username']
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Login error: {e}")
        return jsonify({'status': 'error', 'message': 'Login failed'}), 500

@auth_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    """Get user profile"""
    try:
        user_id = get_jwt_identity()
        db = get_db()
        user = db.users.find_one({'_id': ObjectId(user_id)})
        
        if not user:
            return jsonify({'status': 'error', 'message': 'User not found'}), 404
        
        return jsonify({
            'status': 'success',
            'data': {
                'user_id': str(user['_id']),
                'username': user['username'],
                'email': user.get('email'),
                'has_profile_photo': user.get('profile_photo') is not None
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Profile fetch error: {e}")
        return jsonify({'status': 'error', 'message': 'Failed to fetch profile'}), 500
