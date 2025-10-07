from marshmallow import Schema, fields, validate, ValidationError
from werkzeug.datastructures import FileStorage

class UserRegistrationSchema(Schema):
    username = fields.Str(
        required=True,
        validate=[
            validate.Length(min=3, max=50),
            validate.Regexp(r'^[a-zA-Z0-9_]+$', error='Only letters, numbers, and underscores allowed')
        ]
    )
    email = fields.Email(required=False, allow_none=True)
    password = fields.Str(required=True, validate=validate.Length(min=6))

class UserLoginSchema(Schema):
    username = fields.Str(required=True, validate=validate.Length(min=1))
    password = fields.Str(required=True, validate=validate.Length(min=1))

def validate_request_data(schema, data):
    """Validate request data against schema"""
    try:
        result = schema.load(data)
        return True, result, None
    except ValidationError as e:
        return False, None, e.messages

def validate_file(file, allowed_extensions):
    """Validate uploaded file"""
    if not file or file.filename == '':
        return False, "No file selected"
    
    if not isinstance(file, FileStorage):
        return False, "Invalid file type"
    
    # Check extension
    if '.' not in file.filename:
        return False, "File must have an extension"
    
    ext = file.filename.rsplit('.', 1)[1].lower()
    if ext not in allowed_extensions:
        return False, f"Allowed extensions: {', '.join(allowed_extensions)}"
    
    # Check file size (basic check)
    file.seek(0, 2)  # Go to end
    size = file.tell()
    file.seek(0)  # Reset
    
    if size == 0:
        return False, "File is empty"
    
    return True, "Valid file"
