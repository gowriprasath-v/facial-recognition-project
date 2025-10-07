import os
import uuid
from datetime import datetime
from werkzeug.utils import secure_filename

class FileHandler:
    def __init__(self, upload_folder):
        self.upload_folder = upload_folder
        self.ensure_directories()
    
    def ensure_directories(self):
        dirs = ['profiles', 'groups']
        for dir_name in dirs:
            path = os.path.join(self.upload_folder, dir_name)
            os.makedirs(path, exist_ok=True)
    
    def save_profile_photo(self, file, user_id):
        try:
            ext = file.filename.rsplit('.', 1)[1].lower()
            filename = f"profile_{user_id}_{uuid.uuid4().hex[:8]}.{ext}"
            filepath = os.path.join(self.upload_folder, 'profiles', filename)
            
            file.save(filepath)
            return True, filepath, filename
            
        except Exception as e:
            return False, None, str(e)
    
    def save_group_photo(self, file, user_id):
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            ext = file.filename.rsplit('.', 1)[1].lower()
            filename = f"group_{timestamp}_{user_id[:8]}.{ext}"
            filepath = os.path.join(self.upload_folder, 'groups', filename)
            
            file.save(filepath)
            return True, filepath, filename
            
        except Exception as e:
            return False, None, str(e)
