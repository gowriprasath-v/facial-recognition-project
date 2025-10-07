from flask import Blueprint, jsonify, send_from_directory, current_app, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.database import get_db
from bson import ObjectId
import logging
import os

logger = logging.getLogger(__name__)
photos_bp = Blueprint('photos', __name__)

@photos_bp.route('/my-photos', methods=['GET'])
@jwt_required()
def get_my_photos():
    """Get user's matched photos with detailed information"""
    try:
        user_id = get_jwt_identity()
        db = get_db()
        
        logger.info(f"Fetching matched photos for user: {user_id}")
        
        # Find group photos where user is matched
        photos = list(db.group_photos.find({
            'faces_detected.matched_users.user_id': user_id,
            'processed': True
        }).sort('uploaded_at', -1))  # Most recent first
        
        result = []
        for photo in photos:
            # Find user's matches in this photo
            user_matches = []
            for i, face in enumerate(photo.get('faces_detected', [])):
                for match in face.get('matched_users', []):
                    if match['user_id'] == user_id:
                        user_matches.append({
                            'face_index': i,
                            'similarity_score': match['similarity_score'],
                            'confidence': match['confidence'],
                            'matched_at': match.get('matched_at', '')
                        })
            
            if user_matches:  # Only include if user has matches
                # Get uploader username
                uploader = db.users.find_one({'_id': ObjectId(photo['uploaded_by'])})
                uploader_name = uploader.get('username', 'Unknown') if uploader else 'Unknown'
                
                result.append({
                    'photo_id': str(photo['_id']),
                    'filename': photo['filename'],
                    'uploaded_by': photo['uploaded_by'],
                    'uploader_name': uploader_name,
                    'uploaded_at': photo.get('uploaded_at', '').isoformat() if photo.get('uploaded_at') else '',
                    'total_faces': len(photo.get('faces_detected', [])),
                    'total_matches': photo.get('total_matches', 0),
                    'my_matches': user_matches,
                    'download_url': f'/api/photos/serve/groups/{photo["filename"]}'
                })
        
        logger.info(f"Found {len(result)} matched photos for user: {user_id}")
        
        return jsonify({
            'status': 'success',
            'data': {
                'photos': result,
                'count': len(result)
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Photos fetch error for user {user_id}: {e}")
        return jsonify({'status': 'error', 'message': f'Failed to fetch photos: {str(e)}'}), 500

@photos_bp.route('/photo/<photo_id>', methods=['GET'])
@jwt_required()
def get_photo_details(photo_id):
    """Get detailed information about a specific photo"""
    try:
        user_id = get_jwt_identity()
        db = get_db()
        
        # Find the photo
        photo = db.group_photos.find_one({'_id': ObjectId(photo_id)})
        if not photo:
            return jsonify({'status': 'error', 'message': 'Photo not found'}), 404
        
        # Check if user has access (either uploaded it or appears in it)
        has_access = False
        user_matches = []
        
        if photo['uploaded_by'] == user_id:
            has_access = True
        else:
            # Check if user appears in photo
            for i, face in enumerate(photo.get('faces_detected', [])):
                for match in face.get('matched_users', []):
                    if match['user_id'] == user_id:
                        has_access = True
                        user_matches.append({
                            'face_index': i,
                            'similarity_score': match['similarity_score'],
                            'confidence': match['confidence']
                        })
        
        if not has_access:
            return jsonify({'status': 'error', 'message': 'Access denied'}), 403
        
        # Get all matched users in this photo
        all_matches = []
        for i, face in enumerate(photo.get('faces_detected', [])):
            for match in face.get('matched_users', []):
                user_info = db.users.find_one({'_id': ObjectId(match['user_id'])})
                all_matches.append({
                    'face_index': i,
                    'user_id': match['user_id'],
                    'username': user_info.get('username', 'Unknown') if user_info else 'Unknown',
                    'similarity_score': match['similarity_score'],
                    'confidence': match['confidence']
                })
        
        # Get uploader info
        uploader = db.users.find_one({'_id': ObjectId(photo['uploaded_by'])})
        
        return jsonify({
            'status': 'success',
            'data': {
                'photo_id': str(photo['_id']),
                'filename': photo['filename'],
                'uploaded_by': photo['uploaded_by'],
                'uploader_name': uploader.get('username', 'Unknown') if uploader else 'Unknown',
                'uploaded_at': photo.get('uploaded_at', '').isoformat() if photo.get('uploaded_at') else '',
                'processed': photo.get('processed', False),
                'total_faces': len(photo.get('faces_detected', [])),
                'total_matches': photo.get('total_matches', 0),
                'all_matches': all_matches,
                'my_matches': user_matches,
                'is_owner': photo['uploaded_by'] == user_id
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Photo details error: {e}")
        return jsonify({'status': 'error', 'message': f'Failed to get photo details: {str(e)}'}), 500

@photos_bp.route('/serve/profiles/<filename>')
@jwt_required()
def serve_profile_photo(filename):
    """Serve profile photos (only own profile)"""
    try:
        user_id = get_jwt_identity()
        
        # Check if this is user's own profile photo
        db = get_db()
        user = db.users.find_one({'_id': ObjectId(user_id)})
        
        if not user or not user.get('profile_photo'):
            return jsonify({'status': 'error', 'message': 'Profile photo not found'}), 404
        
        user_filename = os.path.basename(user['profile_photo'])
        if user_filename != filename:
            return jsonify({'status': 'error', 'message': 'Access denied'}), 403
        
        profile_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'profiles')
        return send_from_directory(profile_path, filename)
        
    except Exception as e:
        logger.error(f"Profile photo serve error: {e}")
        return jsonify({'status': 'error', 'message': 'File not found'}), 404

@photos_bp.route('/serve/groups/<filename>')
@jwt_required()
def serve_group_photo(filename):
    """Serve group photos (only if user has access)"""
    try:
        user_id = get_jwt_identity()
        db = get_db()
        
        # Find the group photo by filename
        photo = db.group_photos.find_one({'filename': filename})
        if not photo:
            return jsonify({'status': 'error', 'message': 'Photo not found'}), 404
        
        # Check access (uploaded by user OR user appears in photo)
        has_access = False
        
        if photo['uploaded_by'] == user_id:
            has_access = True
        else:
            # Check if user appears in photo
            for face in photo.get('faces_detected', []):
                for match in face.get('matched_users', []):
                    if match['user_id'] == user_id:
                        has_access = True
                        break
                if has_access:
                    break
        
        if not has_access:
            return jsonify({'status': 'error', 'message': 'Access denied'}), 403
        
        group_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'groups')
        return send_from_directory(group_path, filename)
        
    except Exception as e:
        logger.error(f"Group photo serve error: {e}")
        return jsonify({'status': 'error', 'message': 'File not found'}), 404

@photos_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_user_stats():
    """Get photo statistics for current user"""
    try:
        user_id = get_jwt_identity()
        db = get_db()
        
        # Count photos uploaded by user
        uploaded_count = db.group_photos.count_documents({'uploaded_by': user_id})
        
        # Count photos where user appears
        appeared_count = db.group_photos.count_documents({
            'faces_detected.matched_users.user_id': user_id,
            'uploaded_by': {'$ne': user_id}  # Exclude own uploads
        })
        
        # Count total face appearances
        total_appearances = 0
        photos_with_user = db.group_photos.find({
            'faces_detected.matched_users.user_id': user_id
        })
        
        for photo in photos_with_user:
            for face in photo.get('faces_detected', []):
                for match in face.get('matched_users', []):
                    if match['user_id'] == user_id:
                        total_appearances += 1
        
        # Check if has profile photo
        user = db.users.find_one({'_id': ObjectId(user_id)})
        has_profile = user and user.get('profile_processed', False)
        
        return jsonify({
            'status': 'success',
            'data': {
                'has_profile_photo': has_profile,
                'photos_uploaded': uploaded_count,
                'photos_appeared_in': appeared_count,
                'total_face_appearances': total_appearances,
                'total_accessible_photos': uploaded_count + appeared_count
            }
        }), 200
        
    except Exception as e:
        logger.error(f"User stats error: {e}")
        return jsonify({'status': 'error', 'message': f'Failed to get stats: {str(e)}'}), 500
