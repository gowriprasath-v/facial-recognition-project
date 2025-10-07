import os
import cv2
import numpy as np
import logging
from mtcnn import MTCNN
from keras.models import load_model
from pymongo import MongoClient
from bson import ObjectId

logger = logging.getLogger(__name__)

# Initialize models globally
try:
    # Load FaceNet model
    model_path = os.path.join('models', 'facenet_keras.h5')
    if os.path.exists(model_path):
        model = load_model(model_path)
        logger.info("FaceNet model loaded successfully")
    else:
        model = None
        logger.warning("FaceNet model not found - using placeholder embeddings")
    
    # Initialize MTCNN detector
    detector = MTCNN()
    logger.info("MTCNN detector initialized")
    
except Exception as e:
    logger.error(f"Error loading ML models: {e}")
    model = None
    detector = None

def preprocess_face(face_img):
    """Preprocess face for FaceNet input"""
    face_resized = cv2.resize(face_img, (160, 160))
    face_normalized = face_resized / 255.0
    mean, std = face_normalized.mean(), face_normalized.std()
    face_normalized = (face_normalized - mean) / std
    return face_normalized

def get_embedding(face_pixels):
    """Get face embedding from FaceNet model"""
    if model is None:
        # Return dummy embedding if model not loaded
        return np.random.random(128).tolist()
    
    try:
        face_pixels = face_pixels.astype('float32')
        sample = np.expand_dims(face_pixels, axis=0)
        embedding = model.predict(sample)
        return embedding[0].tolist()
    except Exception as e:
        logger.error(f"Error getting embedding: {e}")
        return np.random.random(128).tolist()

def detect_faces(image_path):
    """Detect faces in image and return face data"""
    if detector is None:
        logger.warning("MTCNN detector not available")
        return []
    
    try:
        # Read image
        image = cv2.imread(image_path)
        if image is None:
            logger.error(f"Could not load image: {image_path}")
            return []
        
        # Convert BGR to RGB
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # Detect faces
        results = detector.detect_faces(rgb_image)
        
        faces_data = []
        for i, res in enumerate(results):
            x, y, w, h = res['box']
            x, y = max(0, x), max(0, y)
            
            # Extract face
            face = rgb_image[y:y+h, x:x+w]
            
            # Preprocess and get embedding
            face_processed = preprocess_face(face)
            embedding = get_embedding(face_processed)
            
            faces_data.append({
                'face_index': i,
                'bbox': [x, y, w, h],
                'confidence': res['confidence'],
                'embedding': embedding
            })
        
        logger.info(f"Detected {len(faces_data)} faces in {image_path}")
        return faces_data
        
    except Exception as e:
        logger.error(f"Error detecting faces in {image_path}: {e}")
        return []

def cosine_similarity(vec1, vec2):
    """Calculate cosine similarity between two vectors"""
    vec1 = np.array(vec1)
    vec2 = np.array(vec2)
    return float(np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2)))

def process_profile_photo(filepath, user_id):
    """Process profile photo and return face embedding"""
    logger.info(f"Processing profile photo: {filepath}")
    
    try:
        faces_data = detect_faces(filepath)
        
        if not faces_data:
            logger.warning(f"No faces detected in profile photo: {filepath}")
            return None
        
        if len(faces_data) > 1:
            logger.warning(f"Multiple faces detected in profile photo: {filepath}, using first face")
        
        # Use the first (or most confident) face
        face_embedding = faces_data[0]['embedding']
        
        logger.info(f"Profile photo processed successfully: {len(face_embedding)}-D embedding")
        return face_embedding
        
    except Exception as e:
        logger.error(f"Error processing profile photo {filepath}: {e}")
        return None

def process_group_photo(filepath, photo_id, db):
    """Process group photo, detect faces, and find matches"""
    logger.info(f"Processing group photo: {filepath}")
    
    try:
        # Detect all faces in group photo
        faces_data = detect_faces(filepath)
        
        if not faces_data:
            logger.warning(f"No faces detected in group photo: {filepath}")
            return {
                'faces_detected': 0,
                'matches_found': 0,
                'face_data': []
            }
        
        # Get all users with face embeddings
        users_with_embeddings = list(db.users.find({
            'face_embedding': {'$exists': True, '$ne': None}
        }))
        
        matches_found = 0
        matched_users = []
        
        # Check each detected face against all user embeddings
        for face_data in faces_data:
            face_embedding = face_data['embedding']
            best_match = None
            best_similarity = 0.0
            
            for user in users_with_embeddings:
                if user.get('face_embedding'):
                    similarity = cosine_similarity(face_embedding, user['face_embedding'])
                    
                    if similarity > 0.6 and similarity > best_similarity:  # Threshold = 0.6
                        best_similarity = similarity
                        best_match = {
                            'user_id': str(user['_id']),
                            'username': user['username'],
                            'similarity': similarity
                        }
            
            if best_match:
                face_data['matched_user'] = best_match
                if best_match['user_id'] not in [m['user_id'] for m in matched_users]:
                    matched_users.append(best_match)
                    matches_found += 1
        
        # Update group photo document with face data and matches
        db.group_photos.update_one(
            {'_id': ObjectId(photo_id)},
            {
                '$set': {
                    'faces_detected': faces_data,
                    'processed': True,
                    'matches_count': matches_found,
                    'matched_users': matched_users
                }
            }
        )
        
        logger.info(f"Group photo processed: {len(faces_data)} faces, {matches_found} matches")
        
        return {
            'faces_detected': len(faces_data),
            'matches_found': matches_found,
            'face_data': faces_data,
            'matched_users': matched_users
        }
        
    except Exception as e:
        logger.error(f"Error processing group photo {filepath}: {e}")
        return {
            'faces_detected': 0,
            'matches_found': 0,
            'face_data': [],
            'error': str(e)
        }
