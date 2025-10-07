from marshmallow import Schema, fields, validate, ValidationError
from werkzeug.datastructures import FileStorage

class UserRegistrationSchema(Schema):
    username = fields.Str(
        required=True,
        validate=[
            validate.Length(min=3, max=50),
            validate.Regexp(r'^[a-zA-Z0-9_]+$')
        ]
    )
    email = fields.Email(required=False, allow_none=True)
    password = fields.Str(required=True, validate=validate.Length(min=6))

class UserLoginSchema(Schema):
    username = fields.Str(required=True)
    password = fields.Str(required=True)

def validate_request_data(schema, data):
    try:
        result = schema.load(data)
        return True, result, None
    except ValidationError as e:
        return False, None, str(e.messages)

def validate_file(file, allowed_extensions):
    if not file or file.filename == '':
        return False, "No file selected"
    
    if '.' not in file.filename:
        return False, "File must have an extension"
    
    ext = file.filename.rsplit('.', 1)[1].lower()
    if ext not in allowed_extensions:
        return False, f"Allowed extensions: {', '.join(allowed_extensions)}"
    
    return True, "Valid file"
