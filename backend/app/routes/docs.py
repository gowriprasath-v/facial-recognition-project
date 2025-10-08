from flask import Blueprint, jsonify

docs_bp = Blueprint('docs', __name__)

@docs_bp.route('/', methods=['GET'])
def api_documentation():
    """API Documentation endpoint"""
    docs = {
        "title": "Facial Recognition API",
        "version": "1.0.0",
        "description": "API for facial recognition and photo management with ML processing",
        "base_url": "/api",
        "authentication": "JWT Bearer Token required for protected endpoints",
        "endpoints": {
            "authentication": {
                "POST /api/auth/register": {
                    "description": "Register a new user account",
                    "body": {
                        "username": "string (3-50 chars, required)",
                        "email": "string (valid email, required)",
                        "password": "string (6-128 chars, required)"
                    },
                    "rate_limit": "5 per minute",
                    "response": "Returns user data and access token"
                },
                "POST /api/auth/login": {
                    "description": "Login with existing credentials",
                    "body": {
                        "username": "string (required)",
                        "password": "string (required)"
                    },
                    "rate_limit": "10 per minute",
                    "response": "Returns user data and access token"
                },
                "GET /api/auth/profile": {
                    "description": "Get current user profile information",
                    "auth": "JWT Bearer Token required",
                    "rate_limit": "100 per hour",
                    "response": "Returns user profile data"
                }
            },
            "uploads": {
                "POST /api/upload/profile": {
                    "description": "Upload profile photo for face recognition",
                    "auth": "JWT Bearer Token required",
                    "body": "multipart/form-data with 'file' field",
                    "file_limits": "Max 5MB, formats: jpg, jpeg, png, gif, bmp",
                    "rate_limit": "20 per hour",
                    "response": "Face detection results and embedding generation status"
                },
                "POST /api/upload/group": {
                    "description": "Upload group photo for face matching",
                    "auth": "JWT Bearer Token required", 
                    "body": "multipart/form-data with 'file' field",
                    "file_limits": "Max 10MB, formats: jpg, jpeg, png, gif, bmp",
                    "rate_limit": "50 per hour",
                    "response": "Face detection and matching results"
                },
                "GET /api/upload/my-photos": {
                    "description": "Get all group photos containing current user",
                    "auth": "JWT Bearer Token required",
                    "rate_limit": "100 per hour",
                    "response": "List of photos with similarity scores"
                },
                "GET /api/upload/test-ml": {
                    "description": "Test ML components and database connectivity",
                    "auth": "JWT Bearer Token required",
                    "rate_limit": "10 per minute",
                    "response": "Status of ML models and database connection"
                },
                "GET /api/upload/stats": {
                    "description": "Get upload statistics for current user",
                    "auth": "JWT Bearer Token required",
                    "rate_limit": "50 per hour",
                    "response": "User statistics and activity data"
                }
            },
            "documentation": {
                "GET /api/docs/": {
                    "description": "Get this API documentation",
                    "auth": "None required",
                    "rate_limit": "General rate limit applies",
                    "response": "Complete API documentation in JSON format"
                }
            }
        },
        "ml_features": {
            "face_detection": "MTCNN neural network for accurate face detection",
            "face_recognition": "FaceNet embeddings for face matching and identification",
            "similarity_threshold": "0.5 (configurable in ML processor)",
            "supported_formats": ["jpg", "jpeg", "png", "gif", "bmp"],
            "processing": "Real-time face detection and matching with database storage"
        },
        "error_handling": {
            "validation": "Input validation with detailed error messages",
            "rate_limiting": "Per-endpoint rate limits to prevent abuse",
            "file_validation": "File type and size validation",
            "ml_fallbacks": "Graceful handling of ML component failures"
        },
        "security_features": {
            "jwt_authentication": "Secure token-based authentication",
            "rate_limiting": "Per-IP and per-endpoint rate limits", 
            "input_validation": "Marshmallow schema validation",
            "file_security": "File type and size validation",
            "environment_variables": "Secure configuration management"
        }
    }
    
    return jsonify(docs), 200
