from marshmallow import Schema, fields, validate, ValidationError
from flask import jsonify

class UserRegistrationSchema(Schema):
    username = fields.Str(required=True, validate=validate.Length(min=3, max=50))
    email = fields.Email(required=True)
    password = fields.Str(required=True, validate=validate.Length(min=6, max=128))

class UserLoginSchema(Schema):
    username = fields.Str(required=True, validate=validate.Length(min=3, max=50))
    password = fields.Str(required=True, validate=validate.Length(min=1, max=128))

def validate_json(schema_class):
    """Decorator to validate JSON input using marshmallow schema"""
    def decorator(f):
        def decorated_function(*args, **kwargs):
            schema = schema_class()
            try:
                from flask import request
                json_data = request.get_json()
                if not json_data:
                    return jsonify({
                        'status': 'error',
                        'message': 'JSON payload is required'
                    }), 400
                
                # Validate and deserialize
                validated_data = schema.load(json_data)
                # Pass validated data to the route function
                return f(validated_data, *args, **kwargs)
                
            except ValidationError as err:
                return jsonify({
                    'status': 'error',
                    'message': 'Validation failed',
                    'errors': err.messages
                }), 400
                
        decorated_function.__name__ = f.__name__
        return decorated_function
    return decorator

def validate_file_upload(allowed_extensions=None, max_size=None):
    """Decorator to validate file uploads"""
    if allowed_extensions is None:
        allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'bmp'}
    
    def decorator(f):
        def decorated_function(*args, **kwargs):
            from flask import request
            
            # Check if file is present
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
            
            # Validate file extension
            if not ('.' in file.filename and 
                   file.filename.rsplit('.', 1)[1].lower() in allowed_extensions):
                return jsonify({
                    'status': 'error',
                    'message': f'Invalid file type. Allowed: {", ".join(allowed_extensions)}'
                }), 400
            
            # Validate file size (optional)
            if max_size:
                file.seek(0, 2)  # Seek to end
                size = file.tell()
                file.seek(0)  # Reset
                
                if size > max_size:
                    return jsonify({
                        'status': 'error',
                        'message': f'File too large. Maximum size: {max_size // (1024*1024)}MB'
                    }), 400
            
            return f(*args, **kwargs)
            
        decorated_function.__name__ = f.__name__
        return decorated_function
    return decorator
