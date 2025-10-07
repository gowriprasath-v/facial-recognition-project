import os
import cv2
import numpy as np
import logging
from mtcnn import MTCNN
from bson import ObjectId

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize models globally
detector = None
model = None

def initialize_ml_models():
    """Initialize ML models with proper error handling"""
    global detector, model
    
    try:
        # Initialize MTCNN detector
        detector = MTCNN()
        logger.info("✅ MTCNN detector initialized successfully")
    except Exception as e:
        logger.error(f"❌ Error initializing MTCNN: {e}")
        detector = None

    # Try to load FaceNet model (optional)
    try:
        from keras.models import load_model
        import keras
        
        model_path = os.path.join('models', 'facenet_keras.h5')
        if os.path.exists(model_path):
            # Try to enable unsafe deserialization
            try:
                keras.config.enable_unsafe_deserialization()
            except:
                pass
            
            model = load_model(model_path, safe_mode=False)
            logger.info("✅ FaceNet model loaded successfully")
        else:
            model = None
            logger.warning("⚠️ FaceNet model not found at models/facenet_keras.h5 - using dummy embeddings")
    except Exception as e:
        logger.warning(f"⚠️ FaceNet not available: {e} - using dummy embeddings")
        model = None

# Initialize models on import
initialize_ml_models()

def preprocess_face(face_img):
    """Preprocess face for FaceNet input"""
    try:
        if face_img is None or face_img.size == 0:
            return np.zeros((160, 160, 3))
            
        face_resized = cv2.resize(face_img, (160, 160))
        face_normalized = face_resized.astype('float32') / 255.0
        mean, std = face_normalized.mean(), face_normalized.std()
        if std > 0:
            face_normalized = (face_normalized - mean) / std
        return face_normalized
    except Exception as e:
        logger.error(f"Error preprocessing face: {e}")
        return np.zeros((160, 160, 3))

def get_embedding(face_pixels):
    """Get face embedding from FaceNet model"""
    try:
        if model is None:
            # Return consistent dummy embedding based on face pixels
            face_hash = hash(str(face_pixels.flatten()[:10].tolist()))
            np.random.seed(abs(face_hash) % 2147483647)
            return np.random.random(128).tolist()
        
        face_pixels = face_pixels.astype('float32')
        sample = np.expand_dims(face_pixels, axis=0)
        embedding = model.predict(sample, verbose=0)
        return embedding[0].tolist()
    except Exception as e:
        logger.error(f"Error getting embedding: {e}")
        # Fallback dummy embedding
        np.random.seed(42)
        return np.random.random(128).tolist()

def detect_faces(image_path):
    """Detect faces in image and return face data"""
    logger.info(f"🔍 Starting face detection for: {image_path}")
    
    if detector is None:
        logger.error("❌ MTCNN detector not available")
        return []
    
    try:
        # Check if file exists
        if not os.path.exists(image_path):
            logger.error(f"❌ Image file not found: {image_path}")
            return []
        
        logger.info(f"📂 Loading image from: {image_path}")
        
        # Read image
        image = cv2.imread(image_path)
        if image is None:
            logger.error(f"❌ Could not load image: {image_path}")
            return []
        
        logger.info(f"✅ Image loaded successfully. Shape: {image.shape}")
        
        # Convert BGR to RGB
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        logger.info("✅ Image converted to RGB")
        
        # Detect faces
        logger.info("🔍 Running MTCNN face detection...")
        results = detector.detect_faces(rgb_image)
        
        if not results:
            logger.warning("⚠️ No faces detected in image")
            return []
        
        logger.info(f"✅ MTCNN detected {len(results)} faces")
        
        faces_data = []
        for i, res in enumerate(results):
            try:
                # Extract bounding box
                x, y, w, h = res['box']
                x, y = max(0, x), max(0, y)
                
                # Ensure face is within image bounds
                h_img, w_img = rgb_image.shape[:2]
                x = min(x, w_img - 1)
                y = min(y, h_img - 1)
                w = min(w, w_img - x)
                h = min(h, h_img - y)
                
                if w <= 0 or h <= 0:
                    logger.warning(f"⚠️ Invalid face dimensions for face {i}: {w}x{h}")
                    continue
                
                # Extract face
                face = rgb_image[y:y+h, x:x+w]
                logger.info(f"✅ Face {i} extracted. Shape: {face.shape}")
                
                # Preprocess and get embedding
                face_processed = preprocess_face(face)
                embedding = get_embedding(face_processed)
                logger.info(f"✅ Successfully processed face {i}")
                
                faces_data.append({
                    'face_index': i,
                    'bbox': [int(x), int(y), int(w), int(h)],
                    'confidence': float(res['confidence']),
                    'embedding': embedding
                })
                
            except Exception as e:
                logger.error(f"❌ Error processing face {i}: {e}")
                continue
        
        logger.info(f"✅ Successfully processed {len(faces_data)} faces")
        return faces_data
        
    except Exception as e:
        logger.error(f"❌ Error detecting faces in {image_path}: {e}")
        return []

def cosine_similarity(vec1, vec2):
    """Calculate cosine similarity between two vectors"""
    try:
        vec1 = np.array(vec1)
        vec2 = np.array(vec2)
        
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
            
        return float(np.dot(vec1, vec2) / (norm1 * norm2))
    except Exception as e:
        logger.error(f"Error calculating cosine similarity: {e}")
        return 0.0

def process_profile_photo(filepath, user_id):
    """Process profile photo and return face embedding"""
    logger.info(f"👤 Processing profile photo: {filepath}")
    
    try:
        faces_data = detect_faces(filepath)
        
        if not faces_data:
            logger.warning(f"⚠️ No faces detected in profile photo: {filepath}")
            return None
        
        if len(faces_data) > 1:
            logger.warning(f"⚠️ Multiple faces detected in profile photo: {filepath}, using most confident face")
            # Sort by confidence and use the most confident face
            faces_data.sort(key=lambda x: x['confidence'], reverse=True)
        
        # Use the first (or most confident) face
        face_embedding = faces_data[0]['embedding']
        confidence = faces_data[0]['confidence']
        
        logger.info(f"✅ Profile photo processed successfully: {len(face_embedding)}-D embedding, confidence: {confidence:.2f}")
        return {
            'embedding': face_embedding,
            'confidence': confidence,
            'faces_detected': len(faces_data)
        }
        
    except Exception as e:
        logger.error(f"❌ Error processing profile photo {filepath}: {e}")
        return None

def process_group_photo(filepath, photo_id, db):
    """Process group photo, detect faces, and find matches"""
    logger.info(f"👥 Processing group photo: {filepath}")
    
    try:
        # Detect all faces in group photo
        faces_data = detect_faces(filepath)
        
        if not faces_data:
            logger.warning(f"⚠️ No faces detected in group photo: {filepath}")
            return {
                'faces_detected': 0,
                'matches_found': 0,
                'face_data': [],
                'matched_users': [],
                'processing_success': True,
                'error': None
            }
        
        # Get all users with face embeddings
        users_with_embeddings = list(db.users.find({
            'face_embedding': {'$exists': True, '$ne': None}
        }))
        
        logger.info(f"📊 Found {len(users_with_embeddings)} users with embeddings")
        
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
                    
                    if similarity > 0.5 and similarity > best_similarity:  # Threshold = 0.5
                        best_similarity = similarity
                        best_match = {
                            'user_id': str(user['_id']),
                            'username': user['username'],
                            'similarity': round(similarity, 3)
                        }
            
            if best_match:
                face_data['matched_user'] = best_match
                # Avoid duplicate users in matched_users list
                if best_match['user_id'] not in [m['user_id'] for m in matched_users]:
                    matched_users.append(best_match)
                    matches_found += 1
                    logger.info(f"✅ Match found: {best_match['username']} (similarity: {best_similarity:.3f})")
        
        # Update group photo document with face data and matches
        try:
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
            logger.info("✅ Group photo data updated in database")
        except Exception as db_error:
            logger.error(f"❌ Database update error: {db_error}")
        
        logger.info(f"✅ Group photo processed: {len(faces_data)} faces, {matches_found} matches")
        
        return {
            'faces_detected': len(faces_data),
            'matches_found': matches_found,
            'face_data': faces_data,
            'matched_users': matched_users,
            'processing_success': True,
            'error': None
        }
        
    except Exception as e:
        logger.error(f"❌ Error processing group photo {filepath}: {e}")
        return {
            'faces_detected': 0,
            'matches_found': 0,
            'face_data': [],
            'matched_users': [],
            'processing_success': False,
            'error': str(e)
        }

def test_ml_setup():
    """Test ML components availability"""
    return {
        'mtcnn_available': detector is not None,
        'facenet_available': model is not None,
        'opencv_available': True,  # If we got here, CV2 is working
        'status': 'ML components initialized'
    }
