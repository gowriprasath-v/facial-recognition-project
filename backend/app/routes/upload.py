from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.database import get_db
from app.utils.file_handler import FileHandler
from app.utils.validators import validate_file
from bson import ObjectId
import logging

logger = logging.getLogger(__name__)
upload_bp = Blueprint('upload', __name__)

@upload_bp.route('/profile', methods=['POST'])
@jwt_required()
def upload_profile():
    """Upload profile photo"""
    try:
        user_id = get_jwt_identity()
        
        if 'file' not in request.files:
            return jsonify({'status': 'error', 'message': 'No file provided'}), 400
        
        file = request.files['file']
        
        # Validate file
        valid, message = validate_file(file, current_app.config['ALLOWED_EXTENSIONS'])
        if not valid:
            return jsonify({'status': 'error', 'message': message}), 400
        
        # Save file
        file_handler = FileHandler(current_app.config['UPLOAD_FOLDER'])
        success, filepath, filename = file_handler.save_profile_photo(file, user_id)
        
        if not success:
            return jsonify({'status': 'error', 'message': filepath}), 500
        
        # Update user record
        db = get_db()
        db.users.update_one(
            {'_id': ObjectId(user_id)},
            {'$set': {'profile_photo': filepath}}
        )
        
        logger.info(f"Profile photo uploaded for user: {user_id}")
        
        return jsonify({
            'status': 'success',
            'message': 'Profile photo uploaded successfully',
            'data': {'filename': filename}
        }), 200
        
    except Exception as e:
        logger.error(f"Profile upload error: {e}")
        return jsonify({'status': 'error', 'message': 'Upload failed'}), 500

@upload_bp.route('/group', methods=['POST'])
@jwt_required()
def upload_group():
    """Upload group photo"""
    try:
        user_id = get_jwt_identity()
        
        if 'file' not in request.files:
            return jsonify({'status': 'error', 'message': 'No file provided'}), 400
        
        file = request.files['file']
        
        # Validate file
        valid, message = validate_file(file, current_app.config['ALLOWED_EXTENSIONS'])
        if not valid:
            return jsonify({'status': 'error', 'message': message}), 400
        
        # Save file
        file_handler = FileHandler(current_app.config['UPLOAD_FOLDER'])
        success, filepath, filename = file_handler.save_group_photo(file, user_id)
        
        if not success:
            return jsonify({'status': 'error', 'message': filepath}), 500
        
        # Create group photo record
        db = get_db()
        group_data = {
            'filename': filename,
            'filepath': filepath,
            'uploaded_by': user_id,
            'faces_detected': [],
            'processed': False
        }
        
        result = db.group_photos.insert_one(group_data)
        
        logger.info(f"Group photo uploaded: {filename}")
        
        return jsonify({
            'status': 'success',
            'message': 'Group photo uploaded successfully',
            'data': {
                'photo_id': str(result.inserted_id),
                'filename': filename
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Group upload error: {e}")
        return jsonify({'status': 'error', 'message': 'Upload failed'}), 500
