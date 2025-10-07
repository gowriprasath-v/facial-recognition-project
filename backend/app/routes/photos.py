from flask import Blueprint, jsonify, send_from_directory, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.database import get_db

photos_bp = Blueprint('photos', __name__)

@photos_bp.route('/my-photos', methods=['GET'])
@jwt_required()
def get_my_photos():
    try:
        user_id = get_jwt_identity()
        db = get_db()
        
        # Find group photos where user is detected
        photos = list(db.group_photos.find({
            'faces_detected.user_id': user_id,
            'processed': True
        }))
        
        result = []
        for photo in photos:
            result.append({
                'photo_id': str(photo['_id']),
                'filename': photo['filename'],
                'uploaded_by': photo['uploaded_by'],
                'num_faces': len(photo.get('faces_detected', []))
            })
        
        return jsonify({
            'status': 'success',
            'data': {
                'photos': result,
                'count': len(result)
            }
        }), 200
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Failed to fetch photos: {str(e)}'}), 500

@photos_bp.route('/serve/<path:filename>')
def serve_file(filename):
    try:
        return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename)
    except Exception as e:
        return jsonify({'status': 'error', 'message': 'File not found'}), 404
