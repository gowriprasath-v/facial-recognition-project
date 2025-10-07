from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.database import get_db
from app.utils.file_handler import FileHandler
from app.utils.validators import validate_file
from bson import ObjectId
import logging
from typing import List, Dict
import os

logger = logging.getLogger(__name__)
upload_bp = Blueprint('upload', __name__)

@upload_bp.route('/profile', methods=['POST'])
@jwt_required()
def upload_profile():
    """Upload and process profile photo with ML"""
    try:
        user_id = get_jwt_identity()
        logger.info(f"Profile upload request from user: {user_id}")
        
        if 'file' not in request.files:
            return jsonify({'status': 'error', 'message': 'No file provided'}), 400
        
        file = request.files['file']
        
        # Validate file
        valid, message = validate_file(file, current_app.config['ALLOWED_EXTENSIONS'])
        if not valid:
            logger.warning(f"Invalid file upload attempt: {message}")
            return jsonify({'status': 'error', 'message': message}), 400
        
        # Save file
        file_handler = FileHandler(current_app.config['UPLOAD_FOLDER'])
        success, filepath, filename = file_handler.save_profile_photo(file, user_id)
        
        if not success:
            logger.error(f"File save failed: {filepath}")
            return jsonify({'status': 'error', 'message': f'File save failed: {filepath}'}), 500
        
        # Process with ML
        from app.utils.ml_processor import process_profile_photo
        ml_result = process_profile_photo(filepath, user_id)
        
        if not ml_result['success']:
            # Clean up uploaded file if ML processing fails
            if os.path.exists(filepath):
                os.remove(filepath)
            logger.error(f"ML processing failed for user {user_id}: {ml_result['message']}")
            return jsonify({
                'status': 'error', 
                'message': f'ML processing failed: {ml_result["message"]}'
            }), 500
        
        # Update user record with photo path and embedding
        db = get_db()
        update_result = db.users.update_one(
            {'_id': ObjectId(user_id)},
            {
                '$set': {
                    'profile_photo': filepath,
                    'face_embedding': ml_result['embedding'],
                    'profile_processed': True,
                    'profile_uploaded_at': datetime.utcnow()
                }
            }
        )
        
        if update_result.modified_count == 0:
            logger.warning(f"User update failed for user: {user_id}")
        
        logger.info(f"Profile photo processed successfully for user: {user_id}")
        
        return jsonify({
            'status': 'success',
            'message': 'Profile photo uploaded and processed successfully',
            'data': {
                'filename': filename,
                'ml_message': ml_result['message'],
                'embedding_length': len(ml_result['embedding']),
                'face_detected': ml_result.get('face_detected', True)
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Profile upload error: {e}")
        return jsonify({'status': 'error', 'message': f'Upload failed: {str(e)}'}), 500

@upload_bp.route('/group', methods=['POST'])
@jwt_required()
def upload_group():
    """Upload and process group photo with ML"""
    try:
        user_id = get_jwt_identity()
        logger.info(f"Group photo upload request from user: {user_id}")
        
        if 'file' not in request.files:
            return jsonify({'status': 'error', 'message': 'No file provided'}), 400
        
        file = request.files['file']
        
        # Validate file
        valid, message = validate_file(file, current_app.config['ALLOWED_EXTENSIONS'])
        if not valid:
            logger.warning(f"Invalid group file upload: {message}")
            return jsonify({'status': 'error', 'message': message}), 400
        
        # Save file
        file_handler = FileHandler(current_app.config['UPLOAD_FOLDER'])
        success, filepath, filename = file_handler.save_group_photo(file, user_id)
        
        if not success:
            logger.error(f"Group file save failed: {filepath}")
            return jsonify({'status': 'error', 'message': f'File save failed: {filepath}'}), 500
        
        # Create initial group photo record
        from datetime import datetime
        db = get_db()
        group_data = {
            'filename': filename,
            'filepath': filepath,
            'uploaded_by': user_id,
            'uploaded_at': datetime.utcnow(),
            'faces_detected': [],
            'processed': False,
            'processing_status': 'pending'
        }
        
        result = db.group_photos.insert_one(group_data)
        photo_id = str(result.inserted_id)
        
        # Process with ML
        from app.utils.ml_processor import process_group_photo
        ml_result = process_group_photo(filepath, photo_id)
        
        if not ml_result['success']:
            # Update status to failed but keep the record
            db.group_photos.update_one(
                {'_id': result.inserted_id},
                {'$set': {'processing_status': 'failed', 'error_message': ml_result['message']}}
            )
            logger.error(f"ML processing failed for group photo {photo_id}: {ml_result['message']}")
            return jsonify({
                'status': 'error',
                'message': f'ML processing failed: {ml_result["message"]}',
                'data': {'photo_id': photo_id, 'filename': filename}
            }), 500
        
        # Run face matching
        matches_found = run_face_matching(photo_id, ml_result['faces_data'])
        
        # Update group photo with ML results
        db.group_photos.update_one(
            {'_id': result.inserted_id},
            {
                '$set': {
                    'faces_detected': ml_result['faces_data'],
                    'processed': True,
                    'processing_status': 'completed',
                    'total_faces': len(ml_result['faces_data']),
                    'total_matches': matches_found,
                    'processed_at': datetime.utcnow()
                }
            }
        )
        
        logger.info(f"Group photo processed successfully: {photo_id}, faces: {len(ml_result['faces_data'])}, matches: {matches_found}")
        
        return jsonify({
            'status': 'success',
            'message': 'Group photo uploaded and processed successfully',
            'data': {
                'photo_id': photo_id,
                'filename': filename,
                'faces_detected': len(ml_result['faces_data']),
                'matches_found': matches_found,
                'ml_message': ml_result['message']
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Group upload error: {e}")
        return jsonify({'status': 'error', 'message': f'Upload failed: {str(e)}'}), 500

def run_face_matching(photo_id: str, faces_data: List[Dict]) -> int:
    """
    Run face matching for a group photo against all user profiles
    
    Args:
        photo_id: Group photo ID
        faces_data: List of detected faces with embeddings
        
    Returns:
        Total number of matches found
    """
    try:
        db = get_db()
        
        # Get all users with profile embeddings
        users_with_profiles = list(db.users.find({
            'face_embedding': {'$exists': True, '$ne': None},
            'profile_processed': True
        }))
        
        if not users_with_profiles:
            logger.info("No users with profile embeddings found for matching")
            return 0
        
        from app.utils.ml_processor import find_face_matches
        total_matches = 0
        
        logger.info(f"Starting face matching for photo {photo_id} against {len(users_with_profiles)} users")
        
        # For each user, find matches in this group photo
        for user in users_with_profiles:
            user_id = str(user['_id'])
            user_embedding = user['face_embedding']
            username = user.get('username', 'unknown')
            
            matches = find_face_matches(user_embedding, faces_data)
            
            if matches:
                logger.info(f"Found {len(matches)} matches for user {username}")
                
                # Update each matched face with user info
                for match in matches:
                    face_index = match['face_index']
                    
                    # Add user match to this face
                    db.group_photos.update_one(
                        {'_id': ObjectId(photo_id)},
                        {
                            '$push': {
                                f'faces_detected.{face_index}.matched_users': {
                                    'user_id': user_id,
                                    'username': username,
                                    'similarity_score': match['similarity_score'],
                                    'confidence': match['confidence'],
                                    'matched_at': datetime.utcnow()
                                }
                            }
                        }
                    )
                
                total_matches += len(matches)
        
        logger.info(f"Face matching completed for photo {photo_id}: {total_matches} total matches")
        return total_matches
        
    except Exception as e:
        logger.error(f"Error in face matching for photo {photo_id}: {e}")
        return 0

@upload_bp.route('/status', methods=['GET'])
@jwt_required()
def get_upload_status():
    """Get upload status for current user"""
    try:
        user_id = get_jwt_identity()
        db = get_db()
        
        user = db.users.find_one({'_id': ObjectId(user_id)})
        if not user:
            return jsonify({'status': 'error', 'message': 'User not found'}), 404
        
        # Count user's uploads
        group_photos_count = db.group_photos.count_documents({'uploaded_by': user_id})
        processed_photos_count = db.group_photos.count_documents({
            'uploaded_by': user_id,
            'processed': True
        })
        
        return jsonify({
            'status': 'success',
            'data': {
                'has_profile_photo': user.get('profile_processed', False),
                'profile_photo_path': user.get('profile_photo'),
                'group_photos_uploaded': group_photos_count,
                'group_photos_processed': processed_photos_count
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Upload status error: {e}")
        return jsonify({'status': 'error', 'message': f'Failed to get status: {str(e)}'}), 500
