import os
import uuid
import logging
from datetime import datetime
from werkzeug.utils import secure_filename
from PIL import Image

logger = logging.getLogger(__name__)

class FileHandler:
    def __init__(self, upload_folder):
        self.upload_folder = upload_folder
        self.ensure_directories()
    
    def ensure_directories(self):
        """Create necessary directories"""
        dirs = ['profiles', 'groups']
        for dir_name in dirs:
            path = os.path.join(self.upload_folder, dir_name)
            os.makedirs(path, exist_ok=True)
    
    def save_profile_photo(self, file, user_id):
        """Save and process profile photo"""
        try:
            ext = file.filename.rsplit('.', 1)[1].lower()
            filename = f"profile_{user_id}_{uuid.uuid4().hex[:8]}.{ext}"
            filepath = os.path.join(self.upload_folder, 'profiles', filename)
            
            file.save(filepath)
            
            # Basic image processing
            self._process_image(filepath, max_size=(800, 800))
            
            logger.info(f"Saved profile photo: {filename}")
            return True, filepath, filename
            
        except Exception as e:
            logger.error(f"Failed to save profile photo: {e}")
            return False, None, str(e)
    
    def save_group_photo(self, file, user_id):
        """Save group photo"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            ext = file.filename.rsplit('.', 1)[1].lower()
            filename = f"group_{timestamp}_{user_id[:8]}.{ext}"
            filepath = os.path.join(self.upload_folder, 'groups', filename)
            
            file.save(filepath)
            
            logger.info(f"Saved group photo: {filename}")
            return True, filepath, filename
            
        except Exception as e:
            logger.error(f"Failed to save group photo: {e}")
            return False, None, str(e)
    
    def _process_image(self, filepath, max_size=(1200, 1200)):
        """Basic image processing"""
        try:
            with Image.open(filepath) as img:
                if img.mode in ('RGBA', 'LA', 'P'):
                    img = img.convert('RGB')
                
                img.thumbnail(max_size, Image.Resampling.LANCZOS)
                img.save(filepath, 'JPEG', quality=85, optimize=True)
        except Exception as e:
            logger.warning(f"Image processing failed for {filepath}: {e}")
    
    def delete_file(self, filepath):
        """Delete file safely"""
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
                return True
        except Exception as e:
            logger.error(f"Failed to delete {filepath}: {e}")
        return False
