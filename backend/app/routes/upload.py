import os
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
import uuid
from pymongo import MongoClient
from bson import ObjectId
from app.utils.ml_processor import process_profile_photo, process_group_photo, test_ml_setup
import logging

logger = logging.getLogger(__name__)

upload_bp = Blueprint('upload', __name__)

def allowed_file(filename):
    """Check if file extension is allowed"""
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_db():
    """Get database connection with better error handling"""
    try:
        mongo_uri = current_app.config.get('MONGO_URI')
        if not mongo_uri:
            logger.error("MONGO_URI not found in app config")
            return None
            
        client = MongoClient(mongo_uri)
        # Test connection
        client.server_info()
        return client.get_default_database()
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        return None

@upload_bp.route('/test-ml', methods=['GET'])
@jwt_required()
def test_ml():
    """Test ML setup endpoint"""
    try:
        result = test_ml_setup()
        
        # Also test database connection
        db = get_db()
        db_status = db is not None
        
        result['database_available'] = db_status
        
        return jsonify({
            'status': 'success',
            'message': 'ML setup test completed',
            'data': result
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'ML test failed: {str(e)}'
        }), 500

@upload_bp.route('/profile', methods=['POST'])
@jwt_required()
def upload_profile():
    """Upload and process profile photo"""
    try:
        # Get current user
        user_id = get_jwt_identity()
        if not user_id:
            return jsonify({
                'status': 'error',
                'message': 'User not authenticated'
            }), 401
        
        # Check if file is in request
        if 'file' not in request.files:
            return jsonify({
                'status': 'error',
                'message': 'No file provided'
            }), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({
                'status': 'error',
                'message': 'No file selected'
            }), 400
        
        # Validate file type
        if not allowed_file(file.filename):
            return jsonify({
                'status': 'error',
                'message': 'Invalid file type. Allowed: png, jpg, jpeg, gif, bmp'
            }), 400
        
        # Get database connection
        db = get_db()
        if db is None:
            return jsonify({
                'status': 'error',
                'message': 'Database connection failed'
            }), 500
        
        # Generate unique filename
        file_extension = file.filename.rsplit('.', 1)[1].lower()
        filename = f"{user_id}_{uuid.uuid4().hex}.{file_extension}"
        
        # Ensure upload directory exists
        upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'profiles')
        os.makedirs(upload_dir, exist_ok=True)
        
        # Save file
        filepath = os.path.join(upload_dir, filename)
        file.save(filepath)
        logger.info(f"✅ Profile photo saved: {filepath}")
        
        # Process the image with ML
        ml_result = process_profile_photo(filepath, user_id)
        
        if ml_result is None:
            # Remove the saved file if processing failed
            try:
                os.remove(filepath)
            except:
                pass
            
            return jsonify({
                'status': 'error',
                'message': 'No face detected in the uploaded image. Please upload a clear photo with a visible face.'
            }), 400
        
        # Update user document with face embedding
        try:
            db.users.update_one(
                {'_id': ObjectId(user_id)},
                {
                    '$set': {
                        'profile_photo': filename,
                        'face_embedding': ml_result['embedding'],
                        'face_confidence': ml_result['confidence']
                    }
                }
            )
            logger.info(f"✅ User profile updated with embedding")
            
        except Exception as db_error:
            logger.error(f"❌ Database update error: {db_error}")
            # Don't fail the request, but log the error
        
        return jsonify({
            'status': 'success',
            'message': 'Profile photo uploaded and processed successfully',
            'data': {
                'filename': filename,
                'faces_detected': ml_result['faces_detected'],
                'confidence': round(ml_result['confidence'], 3),
                'embedding_generated': True
            }
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Profile upload error: {e}")
        return jsonify({
            'status': 'error',
            'message': f'Upload failed: {str(e)}'
        }), 500

@upload_bp.route('/group', methods=['POST'])
@jwt_required()
def upload_group():
    """Upload and process group photo"""
    try:
        # Get current user
        user_id = get_jwt_identity()
        if not user_id:
            return jsonify({
                'status': 'error',
                'message': 'User not authenticated'
            }), 401
        
        # Check if file is in request
        if 'file' not in request.files:
            return jsonify({
                'status': 'error',
                'message': 'No file provided'
            }), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({
                'status': 'error',
                'message': 'No file selected'
            }), 400
        
        # Validate file type
        if not allowed_file(file.filename):
            return jsonify({
                'status': 'error',
                'message': 'Invalid file type. Allowed: png, jpg, jpeg, gif, bmp'
            }), 400
        
        # Get database connection
        db = get_db()
        if db is None:
            return jsonify({
                'status': 'error',
                'message': 'Database connection failed'
            }), 500
        
        # Generate unique filename
        file_extension = file.filename.rsplit('.', 1)[1].lower()
        filename = f"group_{uuid.uuid4().hex}.{file_extension}"
        
        # Ensure upload directory exists
        upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'groups')
        os.makedirs(upload_dir, exist_ok=True)
        
        # Save file
        filepath = os.path.join(upload_dir, filename)
        file.save(filepath)
        logger.info(f"✅ Group photo saved: {filepath}")
        
        # Create group photo document in database
        from datetime import datetime
        group_photo_doc = {
            'filename': filename,
            'uploaded_by': ObjectId(user_id),
            'upload_date': datetime.utcnow(),
            'processed': False,
            'faces_detected': [],
            'matches_count': 0,
            'matched_users': []
        }
        
        insert_result = db.group_photos.insert_one(group_photo_doc)
        photo_id = insert_result.inserted_id
        logger.info(f"✅ Group photo document created: {photo_id}")
        
        # Process the image with ML
        ml_result = process_group_photo(filepath, photo_id, db)
        
        return jsonify({
            'status': 'success',
            'message': 'Group photo uploaded and processed',
            'data': {
                'photo_id': str(photo_id),
                'filename': filename,
                'faces_detected': ml_result['faces_detected'],
                'matches_found': ml_result['matches_found'],
                'matched_users': ml_result['matched_users'],
                'processing_success': ml_result['processing_success'],
                'error': ml_result['error']
            }
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Group upload error: {e}")
        return jsonify({
            'status': 'error',
            'message': f'Upload failed: {str(e)}'
        }), 500

@upload_bp.route('/my-photos', methods=['GET'])
@jwt_required()
def get_my_photos():
    """Get photos that contain the current user"""
    try:
        user_id = get_jwt_identity()
        
        # Get database connection
        db = get_db()
        if db is None:
            return jsonify({
                'status': 'error',
                'message': 'Database connection failed'
            }), 500
        
        # Find group photos where user appears
        matched_photos = list(db.group_photos.find({
            'matched_users.user_id': user_id,
            'processed': True
        }))
        
        # Format response
        photos_data = []
        for photo in matched_photos:
            # Find user's similarity score in this photo
            user_match = next((match for match in photo.get('matched_users', []) 
                             if match['user_id'] == user_id), None)
            
            photos_data.append({
                'photo_id': str(photo['_id']),
                'filename': photo['filename'],
                'upload_date': photo.get('upload_date'),
                'faces_detected': len(photo.get('faces_detected', [])),
                'matches_found': photo.get('matches_count', 0),
                'similarity_score': user_match['similarity'] if user_match else None
            })
        
        return jsonify({
            'status': 'success',
            'message': f'Found {len(photos_data)} photos containing you',
            'data': {
                'photos': photos_data,
                'total_count': len(photos_data)
            }
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Get photos error: {e}")
        return jsonify({
            'status': 'error',
            'message': f'Failed to retrieve photos: {str(e)}'
        }), 500
